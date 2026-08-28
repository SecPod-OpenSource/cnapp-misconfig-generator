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

resource "aws_s3_bucket" "fixture" {
  count         = var.allow_unsafe_apply ? 1 : 0
  bucket_prefix = "cspm-public-delete-bucket-"
  force_destroy = true

  tags = { Purpose = "cspm-misconfiguration-fixture" }
}

resource "aws_s3_bucket_public_access_block" "disabled" {
  count                   = var.allow_unsafe_apply ? 1 : 0
  bucket                  = aws_s3_bucket.fixture[0].id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "fixture" {
  count      = var.allow_unsafe_apply ? 1 : 0
  bucket     = aws_s3_bucket.fixture[0].id
  depends_on = [aws_s3_bucket_public_access_block.disabled]
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowPublicDelete"
        Effect    = "Allow"
        Principal = "*"
        Action    = ["s3:DeleteObject"]
        Resource  = ["${aws_s3_bucket.fixture[0].arn}/*"]
      }
    ]
  })
}
