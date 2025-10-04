# Existing bucket
data "aws_s3_bucket" "s3_ingestion_zone" {
  bucket = var.s3_bucket_name
}

# Merges the CloudWatch and S3 policy documents into a single policy.
data "aws_iam_policy_document" "lambda_inline_policy_doc" {
  source_policy_documents = [
    data.aws_iam_policy_document.lambda_cloudwatch_policy_doc.json,
    data.aws_iam_policy_document.lambda_s3_policy_doc.json
  ]
}

# Defines the IAM policy document granting Lambda access to the S3 bucket.
data "aws_iam_policy_document" "lambda_s3_policy_doc" {
  statement {
    sid    = "S3ReadWriteForObfuscator"
    effect = "Allow"
    actions   = ["s3:GetObject", "s3:PutObject"]
    resources = ["arn:aws:s3:::${var.s3_bucket_name}/*"]
  }
}
