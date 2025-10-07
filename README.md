# GDPR Obfuscator

This project provides a general-purpose tool to process data being ingested into AWS and intercept Personally Identifiable Information (PII). All information stored by Northcoders data projects should be for bulk data analysis only. Consequently, there is a requirement under GDPR to ensure that all data containing information that can be used to identify an individual should be anonymised.

## Features

-   **PII Obfuscation**: Replaces sensitive data in specified fields with a `****` mask.
-   **Multi-format Support**: Handles **CSV**, **JSON**, and **Parquet** data formats.
-   **AWS S3 Integration**: Reads source files from S3 and uploads processed results back to the same bucket with a `transformed/` prefix.
-   **Flexible Invocation**:
    -   As a **command-line utility** for local execution and demonstration.
    -   As a **library module** for integration into other Python codebases.
    -   As an **AWS Lambda function**, ready for integration with AWS Step Functions, EventBridge, or Airflow.
-   **High Code Quality**: The project features extensive test coverage, adheres to PEP-8 standards, and includes static security analysis.

## Installation and Setup

### 1. Prerequisites

-   Python 3.9+
-   `pip` and `venv`
-   AWS CLI

### 2. Local Environment Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd gdpr-obfuscator
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install all development and testing dependencies:**
    ```bash
    pip install -r requirements-dev.txt
    ```

4.  **Configure AWS Credentials:**
    For local execution and testing, you need to configure your AWS CLI. Ensure you have appropriate permissions (`s3:GetObject`, `s3:PutObject`, `s3:HeadObject`) for the target S3 buckets.
    ```bash
    aws configure
    ```

## Usage

### Command-Line Execution

You can run the obfuscation process locally by passing parameters as a JSON string.

**CSV Example**
```bash
python -m src.main '{"file_to_obfuscate": "s3://your-bucket/your-file.csv", "pii_fields": ["name", "email"]}'
```

**JSON Example**
```bash
python -m src.main '{"file_to_obfuscate": "s3://your-bucket/your-file.json", "pii_fields": ["name", "email"]}'
```

**Parquet Example**
```bash
python -m src.main '{"file_to_obfuscate": "s3://your-bucket/your-file.parquet", "pii_fields": ["name", "email"]}'
```

### Library Usage

You can import and use the core logic within your Python code.

```python
import boto3
from src.s3_utils import obfuscate_data

s3_client = boto3.client("s3")
params = {
    "file_to_obfuscate": "s3://your-bucket/your-file.csv",
    "pii_fields": ["name", "email"]
}

# Get the result as bytes
obfuscated_bytes = obfuscate_data(params, s3_client, return_bytes=True)

# Or perform the full cycle with S3 upload and get metadata
result_summary = obfuscate_data(params, s3_client, return_bytes=False)
print(result_summary)
```

## ☁️ Deployment to AWS Lambda

1.  **Create a Deployment ZIP Archive:**
    This archive will contain your code and all production dependencies.
    ```bash
    # Install dependencies into a 'package' directory
    pip install -r requirements.txt -t ./package
    
    # Copy your source code
    cp -r src/* ./package/
    
    # Create the ZIP archive
    cd package
    zip -r ../deployment_package.zip .
    cd ..
    ```

2.  **Create the Lambda Function in AWS:**
    -   **Function Name**: `gdpr-obfuscator`
    -   **Runtime**: Python 3.9 (or newer)
    -   **Architecture**: x86_64
    -   **Handler**: `lambda_handler.lambda_handler`
    -   **Code Upload**: Upload the created `deployment_package.zip`.
    -   **IAM Role**: Create or use an existing role with `s3:GetObject`, `s3:PutObject`, and `s3:HeadObject` permissions for the S3 buckets your function will interact with.
    -   **Timeout**: Set an adequate execution timeout (e.g., 1 minute).

3.  **Example Invocation via AWS Step Functions:**
    You can integrate this Lambda into an AWS Step Function. An example command for starting an execution:
    ```bash
    aws stepfunctions start-execution \
      --state-machine-arn "arn:aws:states:eu-west-2:645583760702:stateMachine:InvokeLambdaAndRetrieveFile" \
      --input '{"file_to_obfuscate": "s3://gdpr-ingestion-bucket/uk_student_records_1000.parquet", "pii_fields": ["name", "email_address"]}'
    ```

### Deploying with Terraform

As an alternative to manual setup, you can use the provided Terraform configuration to automate the deployment of the Lambda function and its associated IAM resources.

1.  **Prerequisites:**
    -   Terraform CLI installed.
    -   Step 1 from the manual deployment (`Create a Deployment ZIP Archive`) completed to create `deployment_package.zip`. Terraform will use this archive.

2.  **Navigate to the Terraform Directory:**
    *(Assuming the Terraform files are located in a `terraform/` directory at the project root.)*
    ```bash
    cd terraform
    ```

3.  **Initialize Terraform:**
    This command initializes the working directory containing the Terraform configuration files.
    ```bash
    terraform init
    ```

4.  **Apply the Configuration:**
    This command applies the changes required to reach the desired state of the configuration.
    ```bash
    terraform apply
    ```
    You will be prompted to confirm the action by typing `yes`.

## 🧪 Testing and Code Quality

### Running Tests

To run the full test suite:
```bash
pytest
```

To view the code coverage report:
```bash
pytest --cov=src
```

### Static Security Analysis

The project uses `bandit` to scan for common security vulnerabilities in the code.
```bash
bandit -r src/
```
