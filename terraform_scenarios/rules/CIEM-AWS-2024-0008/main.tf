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

resource "aws_iam_role" "fixture" {
  count = var.allow_unsafe_apply ? 1 : 0
  name  = "ciem-excessive-role-fixture"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "ec2.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
}

resource "aws_iam_role_policy" "excessive" {
  count = var.allow_unsafe_apply ? 1 : 0
  name  = "ciem-excessive-role-policy"
  role  = aws_iam_role.fixture[0].id
  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = "*", Resource = "*" }]
  })
}
