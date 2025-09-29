# Terraform variables for the GDPR Obfuscator project
# Lambda function name
variable "lambda_name" {
  type    = string
  default = "obfuscator_tool"
}
# S3 bucket name
variable "s3_bucket_name" {
  type    = string
  default = "gdpr-ingestion-bucket"
}
# Step Function name
variable "step_function_name" {
  type    = string
  default = "InvokeLambdaAndRetrieveFile"
}
# Log retention period in days for CloudWatch logs
variable "log_retention_days" {
  type    = number
  default = 14
}
# Memory size in MB for the Lambda function
variable "lambda_memory_size" {
  type    = number
  default = 512
}
