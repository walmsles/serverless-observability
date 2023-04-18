import json
import os

import boto3
from aws_lambda_powertools.logging import Logger, correlation_paths
from aws_lambda_powertools.utilities.data_classes import (
    APIGatewayProxyEvent,
    event_source,
)
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger(service="notify-handler")
client = boto3.client("events")
EVENTBUS_NAME = os.environ.get("EVENTBUS_NAME", "")


@logger.inject_lambda_context(
    log_event=True, correlation_id_path=correlation_paths.API_GATEWAY_REST
)
@event_source(data_class=APIGatewayProxyEvent)
def handler(event: APIGatewayProxyEvent, context: LambdaContext):
    logger.info({"status": "START", "message": "Processing Order Notification"})
    request_id = ""
    correlation_id = event.request_context.request_id
    body = event.json_body
    body["meta_data"] = {"correlation_id": correlation_id}

    try:
        logger.info("submit event to EventBus")
        # Send API Event to EventBridge
        response = client.put_events(
            Entries=[
                {
                    "Detail": json.dumps(body),
                    "DetailType": "order-notify",
                    "Resources": [context.invoked_function_arn],
                    "EventBusName": EVENTBUS_NAME,
                    "Source": context.function_name,
                }
            ],
        )

        # Get the request Id form the EventBridge Interaction
        request_id = response.get("ResponseMetadata", {}).get("RequestId")

        # Check for failures from the put_events Batch call
        if response["FailedEntryCount"] > 0:
            raise Exception("Error sending to EventBus")

        logger.info({"status": "COMPLETE"})
        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "request_id": request_id,
                    "correlation_id": correlation_id,
                }
            ),
        }
    except Exception as e:
        logger.error({"status": "FAILED"}, exc_info=e, stack_info=True)
        return {
            "statusCode": 400,
            "body": json.dumps({"request_id": request_id, "error": str(e)}),
        }
