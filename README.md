python src/main.py '{"file_to_obfuscate": "s3://gdpr-ingestion-bucket/uk_student_records_1000.csv", "pii_fields": ["name", "email_address"]}'

python src/main.py '{"file_to_obfuscate": "s3://gdpr-ingestion-bucket/uk_student_records_1000.json", "pii_fields": ["name", "email_address"]}'

python src/main.py '{"file_to_obfuscate": "s3://gdpr-ingestion-bucket/uk_student_records_1000.parquet", "pii_fields": ["name", "email_address"]}'

aws stepfunctions start-execution --state-machine-arn "arn:aws:states:eu-west-2:645583760702:stateMachine:InvokeLambdaAndRetrieveFile" --input '{"s3_bucket": "gdpr-ingestion-bucket", "s3_key": "uk_student_records_1000.csv", "pii_fields": ["name", "email_address"]}'

aws stepfunctions start-execution --state-machine-arn "arn:aws:states:eu-west-2:645583760702:stateMachine:InvokeLambdaAndRetrieveFile" --input '{"s3_bucket": "gdpr-ingestion-bucket", "s3_key": "uk_student_records_1000.json", "pii_fields": ["name", "email_address"]}'

aws stepfunctions start-execution --state-machine-arn "arn:aws:states:eu-west-2:645583760702:stateMachine:InvokeLambdaAndRetrieveFile" --input '{"s3_bucket": "gdpr-ingestion-bucket", "s3_key": "uk_student_records_1000.parquet", "pii_fields": ["name", "email_address"]}'
