import logging
from urllib.parse import urlparse
from botocore.exceptions import ClientError
from core import read_df_from_bytes, obfuscate_df, write_df_to_bytes
from config import MAX_FILE_SIZE, SUPPORTED_FORMATS

logger = logging.getLogger(__name__)

# s3_url = 's3://gdpr-ingestion-bucket/uk_student_records_1000.csv'
def parse_s3_url(s3_url):
    """
    Parses an S3 URL to extract the bucket name and object key.

    Supports 's3://bucket/key' and common 'https://' formats like
    'https://bucket.s3.amazonaws.com/key'.

    Args:
        s3_url (str): The S3 URL to parse.

    Returns:
        tuple: A tuple containing the bucket name (str) and object key (str).

    Raises:
        ValueError: If the URL is empty or cannot be parsed into a bucket and key.
    """
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
    """
    Determines the file format from the object key's extension.

    Args:
        object_key (str): The S3 object key (e.g., 'path/to/file.csv').

    Returns:
        str: The file format in lowercase (e.g., 'csv').

    Raises:
        ValueError: If the object key has no file extension or if the
                    format is not in SUPPORTED_FORMATS.
    """
    if "." not in object_key:
        raise ValueError("Cannot determine file format - no extension found")
    
    file_format = object_key.rsplit(".", 1)[-1].lower()
    
    if file_format not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported file format: {file_format}")
    
    return file_format


def _validate_and_get_s3_metadata(s3_client, bucket_name, object_key):
    """
    Validates an S3 object's existence and size using a head_object call.

    Args:
        s3_client: The boto3 S3 client instance.
        bucket_name (str): The name of the S3 bucket.
        object_key (str): The key of the object in the bucket.

    Returns:
        dict: The response from the `head_object` call on success.

    Raises:
        ValueError: If the file is not found, is empty, exceeds MAX_FILE_SIZE,
                    or if a client error occurs.
    """
    try:
        head = s3_client.head_object(Bucket=bucket_name, Key=object_key)
        content_length = head.get("ContentLength", 0)
        if content_length > MAX_FILE_SIZE:
            raise ValueError(f"File too large: {content_length} bytes (max {MAX_FILE_SIZE})")
        if content_length == 0:
            raise ValueError(f"File is empty: s3://{bucket_name}/{object_key}")
        return head
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            raise ValueError(f"File not found: s3://{bucket_name}/{object_key}")
        else:
            # Handle other client errors like access denied
            logger.error(f"S3 client error on head_object: {e}")
            raise ValueError(f"Could not access file metadata: {e}")


def _download_s3_object(s3_client, bucket_name, object_key):
    """
    Downloads an object from S3 and returns its content as bytes.

    Args:
        s3_client: The boto3 S3 client instance.
        bucket_name (str): The name of the S3 bucket.
        object_key (str): The key of the object to download.

    Returns:
        bytes: The content of the S3 object.

    Raises:
        ValueError: If a client error occurs during the download.
    """
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        return response["Body"].read()
    except ClientError as e:
        logger.error(f"S3 client error on get_object: {e}")
        raise ValueError(f"Failed to download file from S3: {e}")


def _generate_transformed_key(original_key):
    """
    Generates the key for the transformed (output) file.

    Takes the base filename from the original key and prepends a
    'transformed/' prefix.

    Example: 'path/to/file.csv' -> 'transformed/file.csv'

    Args:
        original_key (str): The original S3 object key.

    Returns:
        str: The new key for the transformed file.
    """
    base_filename = original_key.split('/')[-1]
    return f"transformed/{base_filename}"


def _upload_s3_object(s3_client, bucket_name, object_key, data_bytes):
    """
    Uploads a bytes object to a specified S3 location.

    Args:
        s3_client: The boto3 S3 client instance.
        bucket_name (str): The destination S3 bucket.
        object_key (str): The destination S3 object key.
        data_bytes (bytes): The data to upload.
    """
    try:
        s3_client.put_object(Bucket=bucket_name, Key=object_key, Body=data_bytes)
        logger.info(f"Successfully uploaded to s3://{bucket_name}/{object_key}")
    except ClientError as e:
        logger.error(f"S3 client error on put_object: {e}")
        raise ValueError(f"Failed to save obfuscated file to S3: {e}")


def obfuscate_data(params, s3_client, return_bytes=True):
    """
    Orchestrates the data obfuscation process.

    This function validates parameters, downloads a file from S3,
    obfuscates specified PII fields, and uploads the result back to S3.

    Args:
        params (dict): A dictionary containing the execution parameters,
                       including 'file_to_obfuscate' and 'pii_fields'.
        s3_client: The boto3 S3 client instance.
        return_bytes (bool): If True, returns the obfuscated data as bytes.
                             If False, returns a JSON summary.

    Returns:
        bytes or dict: The obfuscated file content as bytes or a summary
                       dictionary, depending on the `return_bytes` flag.

    Raises:
        ValueError: If parameters are invalid or if any step in the process fails.
    """
    if not isinstance(params, dict):
        raise ValueError("Step Function must pass event as a JSON object")

    if "file_to_obfuscate" not in params:
        raise ValueError("Missing required parameter: file_to_obfuscate")
    
    bucket_name, object_key = parse_s3_url(params["file_to_obfuscate"])
    pii_fields = params.get("pii_fields")

    if not pii_fields or not isinstance(pii_fields, list):
        raise ValueError("Missing or invalid required parameter: pii_fields (list expected)")

    logger.info(f"Processing S3 object: s3://{bucket_name}/{object_key}")

    _validate_and_get_s3_metadata(s3_client, bucket_name, object_key)
    body = _download_s3_object(s3_client, bucket_name, object_key)

    file_format = get_file_format(object_key)
    df = read_df_from_bytes(file_format, body)
    logger.info(f"Loaded DataFrame with {len(df)} rows and {len(df.columns)} columns")
    
    df_obfuscated = obfuscate_df(df, pii_fields)
    output_bytes = write_df_to_bytes(df_obfuscated, file_format)
    
    transformed_key = _generate_transformed_key(object_key)
    _upload_s3_object(s3_client, bucket_name, transformed_key, output_bytes)
    
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
