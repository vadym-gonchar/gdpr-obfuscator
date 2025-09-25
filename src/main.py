import sys
import json
from s3_utils import obfuscate_data

if __name__ == "__main__":
    #'{"file_to_obfuscate": "s3://gdpr-ingestion-bucket/uk_student_records_1000.csv", "pii_fields": ["name", "email_address"]}'
    if len(sys.argv) != 2:
        print("Usage: python main.py '<json-params>'")
        sys.exit(1)
    params = json.loads(sys.argv[1])
    result = obfuscate_data(params, return_bytes=False)
    print(json.dumps(result, indent=2))