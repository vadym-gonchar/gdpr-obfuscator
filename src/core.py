import io
import pandas as pd
import logging

from config import SUPPORTED_FORMATS

logger = logging.getLogger(__name__)

def read_df_from_bytes(file_format, data):
    if file_format not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported file format: {file_format}")
    
    try:
        if file_format == "csv":
            try:
                return pd.read_csv(io.BytesIO(data), encoding='utf-8')
            except UnicodeDecodeError:
                return pd.read_csv(io.BytesIO(data), encoding='latin1')
        elif file_format == "json":
            return pd.read_json(io.BytesIO(data), orient="records")
        elif file_format == "parquet":
            return pd.read_parquet(io.BytesIO(data))
    except Exception as e:
        raise ValueError(f"Failed to read {file_format} data: {str(e)}")


def obfuscate_value_mask(value):
    if pd.isna(value):
        return value
    return "****"


def obfuscate_df(df, pii_fields):
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Input data is not a pandas DataFrame")
    
    if not pii_fields:
        logger.warning("No PII fields specified, returning original DataFrame")
        return df.copy()
    
    # Check which PII fields actually exist in the DataFrame
    missing_fields = [field for field in pii_fields if field not in df.columns]
    if missing_fields:
        logger.warning(f"PII fields not found in data: {missing_fields}")
    
    existing_fields = [field for field in pii_fields if field in df.columns]
    if not existing_fields:
        logger.warning("None of the specified PII fields found in data")
        return df.copy()
    
    result_df = df.copy()
    
    for field in existing_fields:
        logger.info(f"Obfuscating field: {field}")
        result_df[field] = result_df[field].apply(obfuscate_value_mask)
    
    return result_df


def write_df_to_bytes(df, file_format):
    if file_format not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported file format: {file_format}")
    
    try:
        if file_format == "csv":
            buffer = io.StringIO() # Use StringIO for text data
            df.to_csv(buffer, index=False)
            return buffer.getvalue().encode("utf-8")
        elif file_format == "json":
            buffer = io.StringIO() # Use StringIO for text data
            df.to_json(buffer, orient="records", force_ascii=False)
            return buffer.getvalue().encode("utf-8")
        elif file_format == "parquet":
            buffer = io.BytesIO()
            df.to_parquet(buffer, index=False)
            buffer.seek(0)
            return buffer.read()
    except Exception as e:
        raise ValueError(f"Failed to write {file_format} data: {str(e)}")
