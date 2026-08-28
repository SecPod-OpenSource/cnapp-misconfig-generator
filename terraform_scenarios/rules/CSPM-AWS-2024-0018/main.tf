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

resource "aws_ebs_volume" "source" {
  count             = var.allow_unsafe_apply ? 1 : 0
  availability_zone = var.availability_zone
  size              = 8
  encrypted         = false

  tags = { Purpose = "cspm-misconfiguration-fixture" }
}

resource "aws_ebs_snapshot" "source" {
  count     = var.allow_unsafe_apply ? 1 : 0
  volume_id = aws_ebs_volume.source[0].id

  tags = { Purpose = "cspm-misconfiguration-fixture" }
}

resource "aws_ami" "public" {
  count               = var.allow_unsafe_apply ? 1 : 0
  name                = "cspm-public-ami-fixture"
  description         = "INTENTIONALLY INSECURE: public AMI"
  virtualization_type = "hvm"
  root_device_name    = "/dev/sda1"

  ebs_block_device {
    device_name           = "/dev/sda1"
    snapshot_id           = aws_ebs_snapshot.source[0].id
    delete_on_termination = true
    volume_size           = 8
  }
}

resource "aws_ami_launch_permission" "public" {
  count    = var.allow_unsafe_apply ? 1 : 0
  image_id = aws_ami.public[0].id
  group    = "all"
}
