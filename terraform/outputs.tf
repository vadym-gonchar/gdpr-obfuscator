output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.obfuscator_tool.arn
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.obfuscator_tool.function_name
}

output "log_group_name" {
  description = "CloudWatch Log Group for the Lambda"
  value       = aws_cloudwatch_log_group.lambda_log_group.name
}

output "step_function_arn" {
  description = "ARN of the Step Function"
  value       = aws_sfn_state_machine.step_function.arn
}
