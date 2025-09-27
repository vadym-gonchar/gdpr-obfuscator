import boto3
import logging
from urllib.parse import urlparse
from core import read_df_from_bytes, obfuscate_df, write_df_to_bytes
from config import MAX_FILE_SIZE, SUPPORTED_FORMATS

logger = logging.getLogger(__name__)

# s3_url = 's3://gdpr-ingestion-bucket/uk_student_records_1000.csv'
def parse_s3_url(s3_url):
    if not s3_url:
        raise ValueError("S3 URL cannot be empty")
    
    parsed = urlparse(s3_url)
    # parsed=ParseResult(scheme='s3', netloc='gdpr-ingestion-bucket', 
    # path='/uk_student_records_1000.csv', params='', query='', fragment='')

    # Handle s3://bucket/key format
    if parsed.scheme == "s3":
        bucket = parsed.netloc
        key = parsed.path.lstrip("/")
        if not bucket or not key:
            raise ValueError("S3 URL missing bucket or key")
        return bucket, key
    
    # Handle URLs like https://bucket.s3.amazonaws.com/key or https://s3.amazonaws.com/bucket/key
    if parsed.scheme in ("http", "https"):
        netloc_parts = parsed.netloc.split(".")
        if len(netloc_parts) >= 3 and netloc_parts[1].startswith("s3"):
            bucket = netloc_parts[0]
            key = parsed.path.lstrip("/")
            if not bucket or not key:
                raise ValueError("S3 URL missing bucket or key")
            return bucket, key
        
        path_parts = parsed.path.lstrip("/").split("/", 1)
        if len(path_parts) == 2:
            bucket, key = path_parts[0], path_parts[1]
            return bucket, key
    
    raise ValueError("Unable to parse S3 URL. Provide s3://bucket/key or supported https S3 URL.")


def get_file_format(object_key):
    if "." not in object_key:
        raise ValueError("Cannot determine file format - no extension found")
    
    file_format = object_key.rsplit(".", 1)[-1].lower()
    
    if file_format not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported file format: {file_format}")
    
    return file_format


def obfuscate_data(params, return_bytes=True):
    if not isinstance(params, dict):
        raise ValueError("Step Function must pass event as a JSON object")

    if "file_to_obfuscate" not in params:
        raise ValueError("Missing required parameter: file_to_obfuscate")
    
    # backet_name, object_key = parse_s3_url("s3://gdpr-ingestion-bucket/uk_student_records_1000.csv")
    # pii_fields = ["name", "email_address"]
    bucket_name, object_key = parse_s3_url(params["file_to_obfuscate"])
    pii_fields = params.get("pii_fields")

    if not pii_fields or not isinstance(pii_fields, list):
        raise ValueError("Missing or invalid required parameter: pii_fields (list expected)")
    
    try:
        # boto3 looks for credentials in ~/.aws/credentials and creates the client.
        # s3_client = botocore.client.S3 object has methods like get_object, etc to interact with S3. 
        s3_client = boto3.client("s3")
    except Exception as e:
        raise ValueError(f"Failed to initialize S3 client: {str(e)}")
    
    logger.info(f"Processing S3 object: s3://{bucket_name}/{object_key}")
    
    try:
        # head_object retrieves metadata from an object to get its size (ContentLength is in bytes).
        # head = {'ResponseMetadata': {'RequestId': '...', 'HostId': '...', 'HTTPStatusCode': 200, ...},
        # 'ContentLength': 12345, 'ContentType': 'text/csv', ...}.
        head = s3_client.head_object(Bucket=bucket_name, Key=object_key)
        content_length = head.get("ContentLength", 0)
        if content_length > MAX_FILE_SIZE:
            raise ValueError(f"File too large: {content_length} bytes (max {MAX_FILE_SIZE})")
        if content_length == 0:
            raise ValueError(f"File is empty: s3://{bucket_name}/{object_key}")
    except s3_client.exceptions.NoSuchKey:
        raise ValueError(f"File not found: s3://{bucket_name}/{object_key}")
    except Exception as e:
        if "File too large" in str(e):
            raise
        logger.warning(f"Could not check file size: {str(e)}")
    
    try:
        # get_object retrieves the actual file from S3.
        # response["Body"] is a StreamingBody, which has a read() method to get the file bytes.
        # body = b'...' (file content in bytes)
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        body = response["Body"].read()
    except Exception as e:
        raise ValueError(f"Failed to download file from S3: {str(e)}")
    
    file_format = get_file_format(object_key)
    
    df = read_df_from_bytes(file_format, body)
    logger.info(f"Loaded DataFrame with {len(df)} rows and {len(df.columns)} columns")
    
    df_obfuscated = obfuscate_df(df, pii_fields)
    output_bytes = write_df_to_bytes(df_obfuscated, file_format)
    
    transformed_key = f"transformed/{object_key.split('/')[-1]}"
    try:
        # put_object uploads the obfuscated data back to S3 under "transformed/" prefix.
        s3_client.put_object(
            Bucket=bucket_name,
            Key=transformed_key,
            Body=output_bytes
        )
        logger.info(f"Obfuscated file saved to s3://{bucket_name}/{transformed_key}")
    except Exception as e:
        logger.error(f"Failed to save obfuscated file to S3: {str(e)}")
        raise ValueError(f"Failed to save obfuscated file to S3: {str(e)}")
    
    if return_bytes:
        return output_bytes
    else:
        return {
            "status": "success",
            "original_size": len(body),
            "output_size": len(output_bytes),
            "rows_processed": len(df),
            "fields_obfuscated": [field for field in pii_fields if field in df.columns],
            "output_s3_path": f"s3://{bucket_name}/{transformed_key}"
        }
