import sys
import json
import boto3
import logging
from s3_utils import obfuscate_data

# Configure logging for the command-line application
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

if __name__ == "__main__":
    #'{"file_to_obfuscate": "s3://gdpr-ingestion-bucket/uk_student_records_1000.csv", "pii_fields": ["name", "email_address"]}'
    if len(sys.argv) != 2:
        print("Usage: python main.py '<json-params>'")
        sys.exit(1)
    params = json.loads(sys.argv[1])
    s3_client = boto3.client("s3")
    result = obfuscate_data(params, s3_client, return_bytes=False)
    print(json.dumps(result, indent=2))
    