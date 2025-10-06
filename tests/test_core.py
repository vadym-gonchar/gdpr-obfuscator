import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from src.core import (
    read_df_from_bytes,
    obfuscate_df,
    write_df_to_bytes,
    obfuscate_value_mask,
)
from src.config import OBFUSCATION_MASK


@pytest.fixture
def sample_df():
    """Provides a sample DataFrame for testing."""
    return pd.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "email": ["a@a.com", "b@b.com", "c@c.com"],
            "value": [100, 200, 300],
        }
    )


class TestReadWrite:
    @pytest.mark.parametrize(
        "file_format, writer_options, reader_options",
        [
            ("csv", {}, {}),
            ("json", {"orient": "records"}, {"orient": "records"}),
            ("parquet", {}, {}),
        ],
    )
    def test_write_and_read_df(self, sample_df, file_format, writer_options, reader_options):
        """Tests that a DataFrame can be written to bytes and read back correctly."""
        # Write to bytes
        output_bytes = write_df_to_bytes(sample_df, file_format)
        assert isinstance(output_bytes, bytes)
        assert len(output_bytes) > 0

        # Read back from bytes
        read_back_df = read_df_from_bytes(file_format, output_bytes)

        # Parquet can sometimes alter types, so we compare for equality after conversion
        assert_frame_equal(sample_df, read_back_df, check_dtype=False)

    def test_read_unsupported_format(self):
        """Tests that reading an unsupported format raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported file format: xml"):
            read_df_from_bytes("xml", b"")

    def test_write_unsupported_format(self, sample_df):
        """Tests that writing to an unsupported format raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported file format: xml"):
            write_df_to_bytes(sample_df, "xml")

    def test_read_csv_encoding_fallback(self):
        """Tests that read_df_from_bytes falls back to latin1 for CSV."""
        # This string is valid in latin1 but not in utf-8
        problem_string = "Nøt ÜTF-8"
        csv_data = f"col1\n{problem_string}".encode("latin1")

        df = read_df_from_bytes("csv", csv_data)
        assert df["col1"][0] == problem_string


class TestObfuscation:
    @pytest.mark.parametrize(
        "input_value, expected_value",
        [
            ("sensitive_data", OBFUSCATION_MASK),
            (12345, OBFUSCATION_MASK),
            (None, None),
            (pd.NA, pd.NA),
        ],
    )
    def test_obfuscate_value_mask(self, input_value, expected_value):
        """Tests the masking of individual values."""
        if pd.isna(expected_value):
            assert pd.isna(obfuscate_value_mask(input_value))
        else:
            assert obfuscate_value_mask(input_value) == expected_value

    def test_obfuscate_df_success(self, sample_df):
        """Tests successful obfuscation of specified fields."""
        pii_fields = ["name", "email"]
        obfuscated_df = obfuscate_df(sample_df, pii_fields)

        # Check that original df is unchanged
        assert sample_df["name"][0] == "Alice"

        # Check that specified columns are obfuscated
        assert all(obfuscated_df["name"] == OBFUSCATION_MASK)
        assert all(obfuscated_df["email"] == OBFUSCATION_MASK)

        # Check that other columns are untouched
        assert all(obfuscated_df["id"] == sample_df["id"])
        assert all(obfuscated_df["value"] == sample_df["value"])

    def test_obfuscate_df_with_missing_fields(self, sample_df, caplog):
        """Tests obfuscation when some PII fields are not in the DataFrame."""
        pii_fields = ["name", "non_existent_field"]
        obfuscated_df = obfuscate_df(sample_df, pii_fields)

        # Check that the existing field is obfuscated
        assert all(obfuscated_df["name"] == OBFUSCATION_MASK)

        # Check that a warning was logged for the missing field
        assert "PII fields not found in data: ['non_existent_field']" in caplog.text

    def test_obfuscate_df_no_pii_fields(self, sample_df, caplog):
        """Tests that the DataFrame is returned unchanged if no PII fields are provided."""
        obfuscated_df = obfuscate_df(sample_df, [])

        # The returned DataFrame should be an identical copy
        assert_frame_equal(sample_df, obfuscated_df)
        assert "No PII fields specified" in caplog.text

    def test_obfuscate_df_no_matching_fields(self, sample_df, caplog):
        """Tests behavior when none of the PII fields exist in the DataFrame."""
        pii_fields = ["field1", "field2"]
        obfuscated_df = obfuscate_df(sample_df, pii_fields)

        # The returned DataFrame should be an identical copy
        assert_frame_equal(sample_df, obfuscated_df)
        assert "None of the specified PII fields found" in caplog.text
