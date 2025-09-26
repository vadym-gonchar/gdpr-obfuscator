# Step Function assume role
data "aws_iam_policy_document" "step_function_assume" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["states.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "step_function_role" {
  name_prefix        = "sfn-role-${var.step_function_name}-"
  assume_role_policy = data.aws_iam_policy_document.step_function_assume.json
}

# Политика для вызова Lambda из Step Function
data "aws_iam_policy_document" "sf_lambda_invoke_doc" {
  statement {
    effect    = "Allow"
    actions   = ["lambda:InvokeFunction"]
    resources = [aws_lambda_function.obfuscator_tool.arn]
  }
}

resource "aws_iam_role_policy" "sf_lambda_invoke_policy" {
  name   = "step-function-lambda-invoke-policy"
  role   = aws_iam_role.step_function_role.id
  policy = data.aws_iam_policy_document.sf_lambda_invoke_doc.json
}

resource "aws_sfn_state_machine" "step_function" {
  name     = var.step_function_name
  role_arn = aws_iam_role.step_function_role.arn

  definition = templatefile(
    "${path.module}/step_function_definition.asl.json",
    {
      lambda_arn = aws_lambda_function.obfuscator_tool.arn
    }
  )
}
