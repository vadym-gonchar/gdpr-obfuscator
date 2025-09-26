# Existing bucket
data "aws_s3_bucket" "s3_ingestion_zone" {
  bucket = var.s3_bucket_name
}

# Объединенная политика для CloudWatch и S3
data "aws_iam_policy_document" "lambda_inline_policy_doc" {
  source_policy_documents = [
    data.aws_iam_policy_document.lambda_cloudwatch_policy_doc.json,
    data.aws_iam_policy_document.lambda_s3_policy_doc.json
  ]
}

# Политика для доступа Lambda к S3
data "aws_iam_policy_document" "lambda_s3_policy_doc" {
  statement {
    sid    = "S3ReadWriteForObfuscator"
    effect = "Allow"
    actions   = ["s3:GetObject", "s3:PutObject"]
    resources = ["arn:aws:s3:::${var.s3_bucket_name}/*"]
  }
}
