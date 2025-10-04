# Defines the IAM policy that allows Lambda to assume this role.
data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

# Creates the IAM role for the Lambda function.
resource "aws_iam_role" "lambda_role" {
  name_prefix        = "role-${var.lambda_name}-"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

# Attaches an inline policy to the Lambda role for CloudWatch and S3 permissions.
resource "aws_iam_role_policy" "lambda_inline_policy" {
  name   = "lambda-inline-cloudwatch-s3-policy"
  role   = aws_iam_role.lambda_role.id
  policy = data.aws_iam_policy_document.lambda_inline_policy_doc.json
}

# Creates a ZIP archive of the Lambda function source code.
resource "archive_file" "obfuscator_tool_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../src" # Package all files from the src directory
  output_path = "${path.module}/../src/obfuscator_tool.zip"
}

# Defines the Lambda function resource.
resource "aws_lambda_function" "obfuscator_tool" {
  function_name    = var.lambda_name
  filename         = archive_file.obfuscator_tool_zip.output_path
  source_code_hash = archive_file.obfuscator_tool_zip.output_base64sha256
  handler          = "lambda_handler.lambda_handler" # Entry point: lambda_handler.py file, lambda_handler function
  runtime          = "python3.12"
  role             = aws_iam_role.lambda_role.arn

  timeout     = 60
  memory_size = var.lambda_memory_size

  # Attach the official AWS Data Wrangler Layer for Python 3.12, which includes pandas.
  layers = ["arn:aws:lambda:${data.aws_region.current.name}:336392948345:layer:AWSSDKPandas-Python312:14"]

  environment {
    variables = {
      S3_BUCKET      = var.s3_bucket_name
      MAX_FILE_SIZE  = "1000000"
    }
  }
}
