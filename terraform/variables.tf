# Terraform variables for the GDPR Obfuscator project

# Name for the Lambda function.
variable "lambda_name" {
  type    = string
  default = "obfuscator_tool"
}

# Name of the S3 bucket for data ingestion.
variable "s3_bucket_name" {
  type    = string
  default = "gdpr-ingestion-bucket" #REPLACE with your bucket name where obfuscated files will be stored. It should exist before the first deployment.
}

# Name for the Step Function state machine.
variable "step_function_name" {
  type    = string
  default = "InvokeLambdaAndRetrieveFile"
}

# Log retention period in days for the Lambda function's CloudWatch log group.
variable "log_retention_days" {
  type    = number
  default = 14
}

# Memory size in MB allocated to the Lambda function.
variable "lambda_memory_size" {
  type    = number
  default = 512
}
