import json
from typing import Any, Dict

import requests
from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.batch import (
    BatchProcessor,
    EventType,
    process_partial_response,
)
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.config import Config
from tenacity import retry, stop_after_attempt, wait_fixed, wait_random

processor = BatchProcessor(event_type=EventType.SQS)
logger = Logger(service="delivery-handler")
config = Config(
    region_name="ap-southeast-2",
    connect_timeout=1,
    retries={"total_max_attempts": 2, "max_attempts": 5},
)
ssm_provider = parameters.SecretsProvider(config=config)


# retry up to 5 times and wait 3 seconds + random time from 0 to 5 seconds (jitter)
@retry(wait=wait_fixed(3) + wait_random(0, 5), stop=stop_after_attempt(5), reraise=True)
def try_api_delivery(
    endpoint: str, api_key: str, correlation_id: str, body: Dict[str, Any]
) -> str:
    # do stuff
    logger.info("trying API delivery")
    http_headers: Dict[str, str] = {
        "x-api-key": api_key,
        "x-correlation-id": correlation_id,
    }

    response = requests.post(url=endpoint, json=body, headers=http_headers)

    # Log the status code
    logger.info({"message": response.status_code})

    # raise exception to enable tenacity retry
    response.raise_for_status()
    return response.json()


def record_handler(record: SQSRecord):
    logger.info({"status": "START", "message": "Processing Delivery Notification"})

    api_body: Dict[str, Any] = json.loads(record.body).get("detail", {})

    correlation_id: str = api_body.get("meta_data", {}).get(
        "correlation_id", "undefined"
    )

    # remove meta_data from the API body
    del api_body["meta_data"]

    # read endpoint and API key
    try:
        # read endpoint and API Key
        endpoint: str = parameters.get_parameter("/sls-observe/delivery/endpoint")
        api_key: str = ssm_provider.get("/sls-observe/delivery/api-key")

        # robustly try and retry API Delivery (uses tenacity retry)
        response = try_api_delivery(endpoint, api_key, correlation_id, api_body)

        logger.info(response)
        logger.info(
            {
                "status": "COMPLETE",
                "message": response,
            }
        )
    except requests.HTTPError as error:
        logger.error(
            {
                "status": "FAILED",
                "message": str(error),
            }
        )
        raise error

    except parameters.exceptions.GetParameterError as error:
        logger.error("Parameter retrieval failed", exc_info=error)
        raise error


# Lambda handler
@logger.inject_lambda_context(
    log_event=True, correlation_id_path="detail.meta_data.correlation_id"
)
def handler(event, context: LambdaContext):
    return process_partial_response(
        event=event, record_handler=record_handler, processor=processor, context=context
    )
