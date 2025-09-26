import boto3
import logging
from urllib.parse import urlparse
from core import read_df_from_bytes, obfuscate_df, write_df_to_bytes
from config import MAX_FILE_SIZE, SUPPORTED_FORMATS

logger = logging.getLogger(__name__)

def parse_s3_url(s3_url):
    if not s3_url:
        raise ValueError("S3 URL cannot be empty")
    
    parsed = urlparse(s3_url)
    
    if parsed.scheme == "s3":
        bucket = parsed.netloc
        key = parsed.path.lstrip("/")
        if not bucket or not key:
            raise ValueError("S3 URL missing bucket or key")
        return bucket, key
    
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


def get_file_format(file_path):
    if not file_path:
        raise ValueError("File path cannot be empty")
    
    if "." not in file_path:
        raise ValueError("Cannot determine file format - no extension found")
    
    file_format = file_path.rsplit(".", 1)[-1].lower()
    
    if file_format not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported file format: {file_format}")
    
    return file_format


def obfuscate_data(params, return_bytes=True):
    if not isinstance(params, dict):
        raise ValueError("Step Function must pass event as a JSON object")

    if "file_to_obfuscate" in params:
        bucket_name, object_key = parse_s3_url(params["file_to_obfuscate"])
    else:
        bucket_name = params.get("s3_bucket")
        object_key = params.get("s3_key")

    pii_fields = params.get("pii_fields")
    strategy = params.get("strategy", "mask")
    max_size = params.get("max_size", MAX_FILE_SIZE)
    output_prefix = params.get("output_prefix", "transformed/")

    if not bucket_name:
        raise ValueError("Missing required S3 bucket information")

    if not object_key:
        raise ValueError("Missing required S3 object key information")

    if not pii_fields or not isinstance(pii_fields, list):
        raise ValueError("Missing or invalid required parameter: pii_fields (list expected)")
    
    try:
        s3_client = boto3.client("s3")
    except Exception as e:
        raise ValueError(f"Failed to initialize S3 client: {str(e)}")
    
    logger.info(f"Processing S3 object: s3://{bucket_name}/{object_key}")
    
    try:
        head = s3_client.head_object(Bucket=bucket_name, Key=object_key)
        content_length = head.get("ContentLength", 0)
        if content_length > max_size:
            raise ValueError(f"File too large: {content_length} bytes (max {max_size})")
    except s3_client.exceptions.NoSuchKey:
        raise ValueError(f"File not found: s3://{bucket_name}/{object_key}")
    except Exception as e:
        if "File too large" in str(e):
            raise
        logger.warning(f"Could not check file size: {str(e)}")
    
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        body = response["Body"].read()
    except Exception as e:
        raise ValueError(f"Failed to download file from S3: {str(e)}")
    
    if len(body) > max_size:
        raise ValueError(f"Downloaded file too large: {len(body)} bytes (max {max_size})")
    
    file_format = get_file_format(object_key)
    
    df = read_df_from_bytes(file_format, body)
    logger.info(f"Loaded DataFrame with {len(df)} rows and {len(df.columns)} columns")
    
    df_obfuscated = obfuscate_df(df, pii_fields, strategy=strategy)
    output_bytes = write_df_to_bytes(df_obfuscated, file_format)
    
    transformed_key = f"{output_prefix.rstrip('/')}/{object_key.split('/')[-1]}"
    try:
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
            "strategy_used": strategy,
            "output_s3_path": f"s3://{bucket_name}/{transformed_key}"
        }
