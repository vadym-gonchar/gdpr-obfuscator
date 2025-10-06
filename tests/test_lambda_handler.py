import pytest
from unittest.mock import patch, MagicMock
import json

from src.lambda_handler import lambda_handler

# A sample context object, though it's not used in the function
SAMPLE_CONTEXT = MagicMock()


@patch("src.lambda_handler.boto3.client")
@patch("src.lambda_handler.obfuscate_data")
def test_lambda_handler_success_step_function_event(
    mock_obfuscate_data, mock_boto_client
):
    """
    Tests the lambda handler with a typical event from a Step Function,
    where parameters are nested under the "Input" key.
    """
    # --- Setup ---
    mock_s3_client = MagicMock()
    mock_boto_client.return_value = mock_s3_client

    expected_result = {"status": "success", "output_s3_path": "s3://.../file.csv"}
    mock_obfuscate_data.return_value = expected_result

    step_function_event = {
        "Input": {
            "file_to_obfuscate": "s3://my-bucket/my-file.csv",
            "pii_fields": ["email"],
        }
    }

    # --- Execute ---
    result = lambda_handler(step_function_event, SAMPLE_CONTEXT)

    # --- Assertions ---
    mock_boto_client.assert_called_once_with("s3")
    mock_obfuscate_data.assert_called_once_with(
        step_function_event["Input"], mock_s3_client, return_bytes=False
    )
    assert result == expected_result


@patch("src.lambda_handler.boto3.client")
@patch("src.lambda_handler.obfuscate_data")
def test_lambda_handler_success_direct_event(mock_obfuscate_data, mock_boto_client):
    """
    Tests the lambda handler with a direct invocation event (e.g., from console).
    """
    # --- Setup ---
    mock_s3_client = MagicMock()
    mock_boto_client.return_value = mock_s3_client
    mock_obfuscate_data.return_value = {"status": "success"}

    direct_event = {
        "file_to_obfuscate": "s3://my-bucket/my-file.csv",
        "pii_fields": ["email"],
    }

    # --- Execute ---
    lambda_handler(direct_event, SAMPLE_CONTEXT)

    # --- Assertions ---
    mock_obfuscate_data.assert_called_once_with(
        direct_event, mock_s3_client, return_bytes=False
    )


@pytest.mark.parametrize(
    "event, expected_error_msg",
    [
        ({}, "Missing required parameter: file_to_obfuscate"),
        (
            {"file_to_obfuscate": "s3://bucket/file"},
            "Missing or invalid required parameter: pii_fields",
        ),
        (
            {"file_to_obfuscate": "s3://bucket/file", "pii_fields": "not-a-list"},
            "Missing or invalid required parameter: pii_fields",
        ),
        (
            {
                "Records": [
                    {"s3": {"bucket": {"name": "b"}, "object": {"key": "k"}}}
                ]
            },
            "Missing required parameter: file_to_obfuscate",
        ),
    ],
)
def test_lambda_handler_invalid_events(event, expected_error_msg):
    """
    Tests that the lambda handler correctly raises ValueError for various
    invalid input events.
    """
    with pytest.raises(ValueError, match=expected_error_msg):
        lambda_handler(event, SAMPLE_CONTEXT)


@patch("src.lambda_handler.boto3.client")
@patch("src.lambda_handler.obfuscate_data")
def test_lambda_handler_non_dict_event(mock_obfuscate_data, mock_boto_client):
    """
    Tests that the handler raises an error if the event is not a dictionary,
    which would cause an AttributeError on `.get()`.
    """
    with pytest.raises(AttributeError):
        # Passing a string instead of a dict
        lambda_handler("not a dict", SAMPLE_CONTEXT)