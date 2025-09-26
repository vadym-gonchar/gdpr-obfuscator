variable "lambda_name" {
  type    = string
  default = "obfuscator_tool"
}

variable "s3_bucket_name" {
  type    = string
  default = "gdpr-ingestion-bucket"
}

variable "step_function_name" {
  type    = string
  default = "InvokeLambdaAndRetrieveFile"
}

variable "log_retention_days" {
  type    = number
  default = 14
}

variable "lambda_memory_size" {
  type    = number
  default = 512
}
