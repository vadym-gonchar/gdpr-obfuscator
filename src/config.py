"""Shared configuration constants for the GDPR Obfuscator tool."""
import os

# Read from environment variable if available, otherwise use default.
# os.getenv returns a string, so we convert it to an integer.
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "1000000"))

SUPPORTED_FORMATS = ['csv', 'json', 'parquet']

# Prefix for the output S3 object key.
TRANSFORMED_PREFIX = "transformed/"

# Mask used to replace PII data.
OBFUSCATION_MASK = "****"