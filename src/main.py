"""
Command-line entry point for the GDPR Obfuscator tool.
Allows running the obfuscation process locally by passing parameters as a JSON string.
"""
import sys
import json
import boto3
import logging
from .s3_utils import obfuscate_data

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def run_obfuscation(params):
    """
    Initializes dependencies and runs the main obfuscation logic.
    This function serves as a common entry point for different invocation methods.
    """
    s3_client = boto3.client("s3")
    return obfuscate_data(params, s3_client, return_bytes=False)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m src.main '<json-params>'")
        sys.exit(1)
    
    try:
        params = json.loads(sys.argv[1])
        result = run_obfuscation(params)
        print(json.dumps(result, indent=2))
    except json.JSONDecodeError:
        logging.error("Error: Invalid JSON provided in arguments.")
        sys.exit(1)
    except ValueError as e:
        logging.error(f"A validation error occurred: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        sys.exit(1)
    