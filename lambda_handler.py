import logging
import json
from s3_utils import obfuscate_data

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")

    try:
        result = obfuscate_data(event, return_bytes=False)
        
        logger.info("File obfuscated successfully")
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "File obfuscated successfully",
                "result": result
            })
        }
        
    except ValueError as e:
        logger.error(f"Error: {str(e)}")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": str(e)})
        }
        
    except Exception as e:
        logger.exception("Unexpected error in lambda_handler")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }
