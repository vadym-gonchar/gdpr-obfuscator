"""
AWS Lambda handler for the GDPR Obfuscator tool.

This script defines the entry point for the AWS Lambda function. It receives
an event, typically from an AWS Step Function or another trigger, extracts
the necessary parameters, and invokes the core data obfuscation logic.
"""
import logging
import json
import boto3
from s3_utils import obfuscate_data

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Main handler function for the AWS Lambda execution.

    It parses the input event, creates an S3 client, and calls the
    obfuscate_data function to perform the main task. It handles exceptions
    and re-raises them to allow AWS Lambda's runtime to manage error reporting.

    Args:
        event (dict): The event dictionary passed by the Lambda trigger.
                      Can contain an "Input" key if triggered by a Step Function.
        context (object): The Lambda runtime information object. Not used.

    Returns:
        dict: A JSON-serializable dictionary with the results of the obfuscation.
    """
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
