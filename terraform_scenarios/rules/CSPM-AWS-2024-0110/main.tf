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

variable "db_password" {
  description = "Password for this disposable fixture; supply through a secure Terraform variable mechanism."
  type        = string
  sensitive   = true
}

resource "aws_db_instance" "public_postgres" {
  count                   = var.allow_unsafe_apply ? 1 : 0
  identifier              = "cspm-public-rds-fixture"
  allocated_storage       = 20
  engine                  = "postgres"
  engine_version          = "16"
  instance_class          = "db.t3.micro"
  username                = "fixture_admin"
  password                = var.db_password
  publicly_accessible     = true
  skip_final_snapshot     = true
  deletion_protection     = false
  backup_retention_period = 0

  tags = { Purpose = "cspm-misconfiguration-fixture" }
}
