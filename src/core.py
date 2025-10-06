import io
import pandas as pd
import logging

from config import SUPPORTED_FORMATS, OBFUSCATION_MASK

logger = logging.getLogger(__name__)

def read_df_from_bytes(file_format, data):
    """
    Reads byte data into a pandas DataFrame based on the specified file format.

    Supports CSV, JSON, and Parquet formats. For CSV, it attempts to read
    with UTF-8 encoding and falls back to latin1 on error.

    Args:
        file_format (str): The format of the file ('csv', 'json', 'parquet').
        data (bytes): The raw byte content of the file.

    Returns:
        pd.DataFrame: A pandas DataFrame containing the loaded data.

    Raises:
        ValueError: If the file format is unsupported or if reading the data fails.
    """
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
    """
    Obfuscates a single value by replacing it with '****'.

    If the value is NaN or None, it is returned unchanged.

    Args:
        value: The value to obfuscate.

    Returns:
        The obfuscated value or the original value if it's null.
    """
    if pd.isna(value):
        return value
    return OBFUSCATION_MASK


def obfuscate_df(df, pii_fields):
    """
    Obfuscates specified columns in a pandas DataFrame.

    It creates a copy of the DataFrame and applies the `obfuscate_value_mask`
    function to each column listed in `pii_fields`.

    Args:
        df (pd.DataFrame): The input DataFrame.
        pii_fields (list): A list of column names to obfuscate.

    Returns:
        pd.DataFrame: A new DataFrame with the specified fields obfuscated.
    """
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Input data is not a pandas DataFrame")
    
    if not pii_fields:
        logger.warning("No PII fields specified, returning original DataFrame")
        return df.copy()
    
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
    """
    Writes a pandas DataFrame to a byte string in the specified format.

    Supports CSV, JSON, and Parquet formats.

    Args:
        df (pd.DataFrame): The DataFrame to write.
        file_format (str): The target format ('csv', 'json', 'parquet').

    Returns:
        bytes: The DataFrame content as a byte string.

    Raises:
        ValueError: If the file format is unsupported or if writing fails.
    """
    if file_format not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported file format: {file_format}")
    
    try:
        if file_format == "csv":
            buffer = io.StringIO()
            df.to_csv(buffer, index=False)
            return buffer.getvalue().encode("utf-8")
        elif file_format == "json":
            buffer = io.StringIO()
            df.to_json(buffer, orient="records", force_ascii=False)
            return buffer.getvalue().encode("utf-8")
        elif file_format == "parquet":
            buffer = io.BytesIO()
            df.to_parquet(buffer, index=False)
            buffer.seek(0)
            return buffer.read()
    except Exception as e:
        raise ValueError(f"Failed to write {file_format} data: {str(e)}")
