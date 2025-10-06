import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from botocore.exceptions import ClientError
from moto import mock_aws
import os
import boto3

from src.s3_utils import (
    parse_s3_url,
    get_file_format,
    _validate_and_get_s3_metadata,
    _download_s3_object,
    _generate_transformed_key,
    _upload_s3_object,
    obfuscate_data,
    read_df_from_bytes,
)
from src.config import MAX_FILE_SIZE


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


@patch("src.s3_utils._validate_and_get_s3_metadata")
@patch("src.s3_utils._download_s3_object")
@patch("src.s3_utils.read_df_from_bytes")
@patch("src.s3_utils.obfuscate_df")
@patch("src.s3_utils.write_df_to_bytes")
@patch("src.s3_utils._upload_s3_object")
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


class TestObfuscateDataWithMoto:
    """
    Integration tests for the obfuscate_data orchestrator using moto to mock AWS.
    """

    BUCKET_NAME = "test-bucket"
    REGION = "eu-west-2"

    @pytest.fixture(scope="class")
    def aws_credentials(self):
        """Mocked AWS Credentials for moto."""
        os.environ["AWS_ACCESS_KEY_ID"] = "testing"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
        os.environ["AWS_SECURITY_TOKEN"] = "testing"
        os.environ["AWS_SESSION_TOKEN"] = "testing"
        os.environ["AWS_DEFAULT_REGION"] = self.REGION

    @pytest.fixture(scope="class")
    def s3(self, aws_credentials):
        with mock_aws():
            client = boto3.client("s3", region_name=self.REGION)
            client.create_bucket(
                Bucket=self.BUCKET_NAME,
                CreateBucketConfiguration={"LocationConstraint": self.REGION},
            )
            yield client

    @pytest.mark.parametrize(
        "file_format, pii_fields",
        [
            ("csv", ["name", "email"]),
            ("json", ["name", "email"]),
            ("parquet", ["name", "email"]),
        ],
    )
    def test_obfuscate_data_happy_path(self, s3, file_format, pii_fields):
        """
        Tests the full obfuscation cycle: download from S3, obfuscate, upload to S3.
        This test is parametrized to run for all supported file formats.
        """
        # 1. Setup: Create sample data and upload to mock S3 in the correct format
        original_key = f"source/data.{file_format}"
        sample_df = pd.DataFrame({
            "id": [1], "name": ["John Doe"], "email": ["john@example.com"]
        })
        
        # Use a helper from core to create the byte content
        from src.core import write_df_to_bytes
        original_content_bytes = write_df_to_bytes(sample_df, file_format)

        s3.put_object(Bucket=self.BUCKET_NAME, Key=original_key, Body=original_content_bytes)

        params = {
            "file_to_obfuscate": f"s3://{self.BUCKET_NAME}/{original_key}",
            "pii_fields": pii_fields,
        }

        # 2. Execute the function
        result = obfuscate_data(params, s3, return_bytes=False)

        # 3. Assertions
        transformed_key = f"transformed/data.{file_format}"
        assert result["status"] == "success"
        assert result["output_s3_path"] == f"s3://{self.BUCKET_NAME}/{transformed_key}"

        # Verify the uploaded file content
        response = s3.get_object(Bucket=self.BUCKET_NAME, Key=transformed_key)
        obfuscated_bytes = response["Body"].read()
        obfuscated_df = read_df_from_bytes(file_format, obfuscated_bytes)

        assert obfuscated_df["id"][0] == 1
        assert obfuscated_df["name"][0] == "****"
        assert obfuscated_df["email"][0] == "****"

    def test_obfuscate_data_file_not_found(self, s3):
        """Tests that a ValueError is raised if the source file doesn't exist."""
        params = {
            "file_to_obfuscate": f"s3://{self.BUCKET_NAME}/non_existent_file.csv",
            "pii_fields": ["email"],
        }
        with pytest.raises(ValueError, match="File not found"):
            obfuscate_data(params, s3)

    def test_obfuscate_data_empty_file(self, s3):
        """Tests that a ValueError is raised for an empty source file."""
        s3.put_object(Bucket=self.BUCKET_NAME, Key="empty.csv", Body="")
        params = {"file_to_obfuscate": f"s3://{self.BUCKET_NAME}/empty.csv", "pii_fields": ["email"]}
        with pytest.raises(ValueError, match="File is empty"):
            obfuscate_data(params, s3)