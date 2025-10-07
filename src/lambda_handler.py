"""
AWS Lambda handler for the GDPR Obfuscator tool.

This script defines the entry point for the AWS Lambda function. It receives
an event, typically from an AWS Step Function or another trigger, extracts
the necessary parameters, and invokes the core data obfuscation logic.
"""
import json
import logging
from .main import run_obfuscation

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

    try:
        params = event.get("Input", event)
        result = run_obfuscation(params)
        logger.info(f"File obfuscated successfully. Result: {json.dumps(result)}")
        return result

    except ValueError as e:
        logger.error("A validation error occurred: " + str(e))
        raise

    except Exception as e:
        logger.exception("Unexpected error in lambda_handler: " + str(e))
        raise
    