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

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py '<json-params>'")
        sys.exit(1)
    
    try:
        params = json.loads(sys.argv[1])
        s3_client = boto3.client("s3")
        result = obfuscate_data(params, s3_client, return_bytes=False)
        print(json.dumps(result, indent=2))
    except json.JSONDecodeError:
        logging.error("Error: Invalid JSON provided in arguments.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        sys.exit(1)
    