import random
import time

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger(service="slow-api")
app = APIGatewayRestResolver()


@app.post("/slow")
def slowHandler():
    try:
        # Grab the correlation_id and setup logger with it
        correlation_id: str = app.current_event.get_header_value(
            "x-correlation-id", "not-supplied"
        )
        logger.set_correlation_id(correlation_id)

        logger.info({"status": "START", "message": "Slow processing..."})

        # randomly raise an Exception to fail the process 20% of the time
        random_fail = random.randint(0, 100)
        if random_fail > 80:
            raise Exception("random process failure")

        # Process the Data
        timeout: int = random.randint(1, 10)
        logger.info({"message": f"slow response, waiting {timeout} seconds"})
        time.sleep(timeout)

        logger.info({"status": "COMPLETE"})

        return {"correlation_id": correlation_id, "message": "processed"}

    except Exception as error:
        logger.error(f"error: {str(error)}", exc_info=error)
        logger.info({"status": "FAILED", "message": str(error)})
        raise error


@logger.inject_lambda_context(log_event=True)
def handler(event, context: LambdaContext):
    return app.resolve(event, context)
