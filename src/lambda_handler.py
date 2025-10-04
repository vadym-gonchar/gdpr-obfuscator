import logging
import json
import boto3
from s3_utils import obfuscate_data

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")

    # Let Lambda's runtime handle exceptions for better error reporting in CloudWatch
    try:
        # Parameters are now nested under the "Input" key by the Step Function
        params = event.get("Input", event)
        s3_client = boto3.client("s3")
        result = obfuscate_data(params, s3_client, return_bytes=False)
        logger.info("File obfuscated successfully")
        return result

    except ValueError as e:
        logger.error("A validation error occurred: " + str(e))
        raise  # Re-raise the exception to let Lambda runtime handle it

    except Exception as e:
        logger.exception("Unexpected error in lambda_handler: " + str(e))
        raise  # Re-raise for detailed error logging
