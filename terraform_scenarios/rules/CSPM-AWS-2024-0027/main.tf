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
  cidr_block = "10.251.0.0/16"

  tags = { Purpose = "cspm-misconfiguration-fixture" }
}

resource "aws_internet_gateway" "fixture" {
  count  = var.allow_unsafe_apply ? 1 : 0
  vpc_id = aws_vpc.fixture[0].id
}

resource "aws_subnet" "public" {
  count                   = var.allow_unsafe_apply ? 1 : 0
  vpc_id                  = aws_vpc.fixture[0].id
  cidr_block              = "10.251.1.0/24"
  availability_zone       = var.availability_zone
  map_public_ip_on_launch = true
}

resource "aws_route_table" "public" {
  count  = var.allow_unsafe_apply ? 1 : 0
  vpc_id = aws_vpc.fixture[0].id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.fixture[0].id
  }
}

resource "aws_route_table_association" "public" {
  count          = var.allow_unsafe_apply ? 1 : 0
  subnet_id      = aws_subnet.public[0].id
  route_table_id = aws_route_table.public[0].id
}

resource "aws_security_group" "instance" {
  count       = var.allow_unsafe_apply ? 1 : 0
  name        = "cspm-public-ip-instance-fixture"
  description = "No ingress or egress; public IP is the intentional finding."
  vpc_id      = aws_vpc.fixture[0].id
  egress      = []
}

resource "aws_instance" "public_ip" {
  count                       = var.allow_unsafe_apply ? 1 : 0
  ami                         = var.ami_id
  instance_type               = "t3.micro"
  subnet_id                   = aws_subnet.public[0].id
  vpc_security_group_ids      = [aws_security_group.instance[0].id]
  associate_public_ip_address = true

  tags = { Purpose = "cspm-misconfiguration-fixture" }
}
