resource "aws_cloudwatch_log_group" "lambda_log_group" {
  name              = "/aws/lambda/${var.lambda_name}"
  retention_in_days = var.log_retention_days
}

# Политика для записи логов Lambda в CloudWatch
data "aws_iam_policy_document" "lambda_cloudwatch_policy_doc" {
  statement {
    sid    = "CloudWatchLogsForLambda"
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["${aws_cloudwatch_log_group.lambda_log_group.arn}:*"]
  }
}
