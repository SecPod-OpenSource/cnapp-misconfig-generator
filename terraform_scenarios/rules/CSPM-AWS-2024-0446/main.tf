terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  description = "AWS region in a dedicated disposable test account."
  type        = string
  default     = "us-east-1"
}

variable "allow_unsafe_apply" {
  description = "Must be explicitly true before this intentionally insecure fixture is created."
  type        = bool
  default     = false
}

variable "ami_id" {
  description = "Pre-approved AMI ID for EC2 instance scenarios; this default is valid in us-east-1 only."
  type        = string
  default     = "ami-0f8a61b66d1accaee"
}

variable "availability_zone" {
  description = "Pre-approved Availability Zone; this default is valid in us-east-1 only."
  type        = string
  default     = "us-east-1a"
}

terraform {
  required_providers {
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
}

data "archive_file" "fixture" {
  type                    = "zip"
  output_path             = "${path.module}/cspm-aws-2024-0446.zip"
  source_content          = "def handler(event, context): return {'statusCode': 200, 'body': 'fixture'}"
  source_content_filename = "index.py"
}

resource "aws_iam_role" "fixture" {
  count = var.allow_unsafe_apply ? 1 : 0
  name  = "cspm-aws-2024-0446-lambda-role"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "lambda.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
}

resource "aws_lambda_function" "fixture" {
  count            = var.allow_unsafe_apply ? 1 : 0
  function_name    = "cspm-aws-2024-0446-fixture"
  role             = aws_iam_role.fixture[0].arn
  handler          = "index.handler"
  runtime          = "python3.12"
  filename         = data.archive_file.fixture.output_path
  source_code_hash = data.archive_file.fixture.output_base64sha256

}

resource "aws_lambda_function_url" "fixture" {
  count              = var.allow_unsafe_apply ? 1 : 0
  function_name      = aws_lambda_function.fixture[0].function_name
  authorization_type = "NONE"
}
