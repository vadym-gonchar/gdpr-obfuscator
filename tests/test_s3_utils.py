import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from botocore.exceptions import ClientError

from s3_utils import (
    parse_s3_url,
    get_file_format,
    _validate_and_get_s3_metadata,
    _download_s3_object,
    _generate_transformed_key,
    _upload_s3_object,
    obfuscate_data,
)
from config import MAX_FILE_SIZE


@pytest.mark.parametrize(
    "url, expected_bucket, expected_key",
    [
        ("s3://my-bucket/path/to/file.csv", "my-bucket", "path/to/file.csv"),
        ("https://my-bucket.s3.amazonaws.com/file.json", "my-bucket", "file.json"),
        ("https://s3.eu-west-2.amazonaws.com/my-bucket/file.parquet", "my-bucket", "file.parquet"),
    ],
)
def test_parse_s3_url_success(url, expected_bucket, expected_key):
    """Tests successful parsing of various S3 URL formats."""
    bucket, key = parse_s3_url(url)
    assert bucket == expected_bucket
    assert key == expected_key


@pytest.mark.parametrize(
    "invalid_url",
    ["", "s3:///", "http://google.com", "not_a_url"],
)
def test_parse_s3_url_failure(invalid_url):
    """Tests that invalid S3 URLs raise ValueError."""
    with pytest.raises(ValueError):
        parse_s3_url(invalid_url)


@pytest.mark.parametrize(
    "key, expected_format",
    [("file.csv", "csv"), ("data/archive.JSON", "json"), ("file.Parquet", "parquet")],
)
def test_get_file_format_success(key, expected_format):
    """Tests successful extraction of file format from object key."""
    assert get_file_format(key) == expected_format


@pytest.mark.parametrize(
    "invalid_key, match_text",
    [
        ("file_without_extension", "no extension found"),
        ("file.txt", "Unsupported file format: txt"),
    ],
)
def test_get_file_format_failure(invalid_key, match_text):
    """Tests that invalid object keys for format extraction raise ValueError."""
    with pytest.raises(ValueError, match=match_text):
        get_file_format(invalid_key)


def test_generate_transformed_key():
    """Tests the generation of the output key."""
    assert _generate_transformed_key("path/to/file.csv") == "transformed/file.csv"
    assert _generate_transformed_key("file.json") == "transformed/file.json"


class TestS3Interactions:
    @pytest.fixture
    def mock_s3_client(self):
        """Provides a MagicMock for the S3 client."""
        return MagicMock()

    def test_validate_metadata_success(self, mock_s3_client):
        """Tests successful validation of S3 object metadata."""
        mock_s3_client.head_object.return_value = {"ContentLength": 1024}
        _validate_and_get_s3_metadata(mock_s3_client, "bucket", "key")
        mock_s3_client.head_object.assert_called_once_with(Bucket="bucket", Key="key")

    def test_validate_metadata_too_large(self, mock_s3_client):
        """Tests ValueError when file size exceeds MAX_FILE_SIZE."""
        mock_s3_client.head_object.return_value = {"ContentLength": MAX_FILE_SIZE + 1}
        with pytest.raises(ValueError, match="File too large"):
            _validate_and_get_s3_metadata(mock_s3_client, "bucket", "key")

    def test_validate_metadata_not_found(self, mock_s3_client):
        """Tests ValueError when S3 object is not found (NoSuchKey)."""
        error_response = {"Error": {"Code": "NoSuchKey"}}
        mock_s3_client.head_object.side_effect = ClientError(error_response, "HeadObject")
        with pytest.raises(ValueError, match="File not found"):
            _validate_and_get_s3_metadata(mock_s3_client, "bucket", "key")

    def test_download_s3_object_success(self, mock_s3_client):
        """Tests successful download of an S3 object."""
        mock_body = MagicMock()
        mock_body.read.return_value = b"file_content"
        mock_s3_client.get_object.return_value = {"Body": mock_body}

        content = _download_s3_object(mock_s3_client, "bucket", "key")

        assert content == b"file_content"
        mock_s3_client.get_object.assert_called_once_with(Bucket="bucket", Key="key")

    def test_upload_s3_object_success(self, mock_s3_client):
        """Tests successful upload of an S3 object."""
        data_bytes = b"obfuscated_content"
        _upload_s3_object(mock_s3_client, "bucket", "key", data_bytes)
        mock_s3_client.put_object.assert_called_once_with(
            Bucket="bucket", Key="key", Body=data_bytes
        )


@patch("s3_utils._validate_and_get_s3_metadata")
@patch("s3_utils._download_s3_object")
@patch("s3_utils.read_df_from_bytes")
@patch("s3_utils.obfuscate_df")
@patch("s3_utils.write_df_to_bytes")
@patch("s3_utils._upload_s3_object")
def test_obfuscate_data_orchestration(
    mock_upload, mock_write, mock_obfuscate, mock_read, mock_download, mock_validate
):
    """
    Tests the main orchestrator function `obfuscate_data`.
    This is an integration-style unit test that checks if the sub-functions are called correctly.
    """
    # --- Setup Mocks ---
    mock_s3_client = MagicMock()
    mock_download.return_value = b"original_bytes"
    mock_read.return_value = pd.DataFrame({"email": ["test@test.com"]})
    mock_obfuscate.return_value = "obfuscated_dataframe"
    mock_write.return_value = b"output_bytes"

    params = {
        "file_to_obfuscate": "s3://my-bucket/my-file.csv",
        "pii_fields": ["email"],
    }

    # --- Execute ---
    result = obfuscate_data(params, mock_s3_client, return_bytes=False)

    # --- Assertions ---
    # Check that helper functions were called with correct arguments
    mock_validate.assert_called_once_with(mock_s3_client, "my-bucket", "my-file.csv")
    mock_download.assert_called_once_with(mock_s3_client, "my-bucket", "my-file.csv")
    mock_read.assert_called_once_with("csv", b"original_bytes")
    mock_obfuscate.assert_called_once_with(mock_read.return_value, ["email"])
    mock_write.assert_called_once_with("obfuscated_dataframe", "csv")
    mock_upload.assert_called_once_with(
        mock_s3_client, "my-bucket", "transformed/my-file.csv", b"output_bytes"
    )

    # Check the final result dictionary
    assert result["status"] == "success"
    assert result["output_s3_path"] == "s3://my-bucket/transformed/my-file.csv"