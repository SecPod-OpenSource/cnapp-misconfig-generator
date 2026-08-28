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

resource "aws_vpc" "fixture" {
  count      = var.allow_unsafe_apply ? 1 : 0
  cidr_block = "10.254.0.0/16"
}

resource "aws_subnet" "private" {
  count             = var.allow_unsafe_apply ? 1 : 0
  vpc_id            = aws_vpc.fixture[0].id
  cidr_block        = "10.254.1.0/24"
  availability_zone = var.availability_zone
}

resource "aws_security_group" "instance" {
  count       = var.allow_unsafe_apply ? 1 : 0
  name        = "cspm-imdsv1-fixture"
  description = "No network access; IMDSv1 is the intentional finding."
  vpc_id      = aws_vpc.fixture[0].id
  egress      = []
}

resource "aws_instance" "imdsv1" {
  count                  = var.allow_unsafe_apply ? 1 : 0
  ami                    = var.ami_id
  instance_type          = "t3.micro"
  subnet_id              = aws_subnet.private[0].id
  vpc_security_group_ids = [aws_security_group.instance[0].id]

  metadata_options {
    http_tokens = "optional"
  }

  tags = { Purpose = "cspm-misconfiguration-fixture" }
}
