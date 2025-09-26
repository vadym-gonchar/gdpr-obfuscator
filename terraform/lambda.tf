# IAM assume role policy for Lambda
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

resource "aws_iam_role" "lambda_role" {
  name_prefix        = "role-${var.lambda_name}-"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

# Attach inline CloudWatch + S3 permissions
resource "aws_iam_role_policy" "lambda_inline_policy" {
  name   = "lambda-inline-cloudwatch-s3-policy"
  role   = aws_iam_role.lambda_role.id
  policy = data.aws_iam_policy_document.lambda_inline_policy_doc.json
}

# Создаем ZIP-архив Lambda
resource "archive_file" "obfuscator_tool_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../src"       # берем все файлы из src
  output_path = "${path.module}/../src/obfuscator_tool.zip"
}

# Lambda-функция
resource "aws_lambda_function" "obfuscator_tool" {
  function_name    = var.lambda_name
  filename         = archive_file.obfuscator_tool_zip.output_path
  source_code_hash = archive_file.obfuscator_tool_zip.output_base64sha256
  handler = "lambda_handler.lambda_handler"  # Файл lambda_handler.py в ZIP, функция lambda_handler
  runtime          = "python3.12"
  role             = aws_iam_role.lambda_role.arn

  timeout     = 60
  memory_size = var.lambda_memory_size

  # Подключаем официальный Layer AWS Data Wrangler для Python 3.12
  layers = ["arn:aws:lambda:${data.aws_region.current.name}:336392948345:layer:AWSSDKPandas-Python312:14"]

  environment {
    variables = {
      S3_BUCKET      = var.s3_bucket_name
      MAX_FILE_SIZE  = "1000000"
    }
  }
}
