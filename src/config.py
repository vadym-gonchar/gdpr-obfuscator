"""Shared configuration constants for the GDPR Obfuscator tool."""
import os

MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "1000000"))

SUPPORTED_FORMATS = ['csv', 'json', 'parquet']

TRANSFORMED_PREFIX = "transformed/"

OBFUSCATION_MASK = "****"