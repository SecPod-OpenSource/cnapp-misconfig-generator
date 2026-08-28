"""Explicit Terraform templates for rules whose conditions have been reviewed."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Template:
    description: str
    terraform: str


COMMON = '''terraform {
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

'''


def security_group_template(name: str, description: str, protocol: str, from_port: int, to_port: int, cidr: str = "0.0.0.0/0") -> str:
    """Build a reviewed security-group fixture with no incidental egress rule."""
    return COMMON + f'''resource "aws_security_group" "fixture" {{
  count       = var.allow_unsafe_apply ? 1 : 0
  name        = "{name}"
  description = "INTENTIONALLY INSECURE: {description}"

  ingress {{
    description = "INTENTIONALLY INSECURE: {description}"
    from_port   = {from_port}
    to_port     = {to_port}
    protocol    = "{protocol}"
    cidr_blocks = ["{cidr}"]
  }}

  # Avoid an incidental AWS default allow-all egress rule.
  egress = []

  tags = {{ Purpose = "cspm-misconfiguration-fixture" }}
}}
'''


def s3_bucket_template(prefix: str, extra: str = "") -> str:
    return COMMON + f'''resource "aws_s3_bucket" "fixture" {{
  count         = var.allow_unsafe_apply ? 1 : 0
  bucket_prefix = "{prefix}-"
  force_destroy = true

  tags = {{ Purpose = "cspm-misconfiguration-fixture" }}
}}

{extra}'''


def s3_public_policy_template(prefix: str, statement: str) -> str:
    public_access_block = '''resource "aws_s3_bucket_public_access_block" "disabled" {
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
      ''' + statement + '''
    ]
  })
}
'''
    return s3_bucket_template(prefix, public_access_block)


def rds_instance_template(rule_id: str, description: str, insecure_settings: str, username: str = "fixture_admin") -> Template:
    """Create a small PostgreSQL RDS fixture for one direct instance finding."""
    return Template(
        description,
        COMMON + f'''variable "db_password" {{
  description = "Password for this disposable fixture. Set TF_VAR_db_password rather than committing a value."
  type        = string
  sensitive   = true
}}

resource "aws_db_instance" "fixture" {{
  count                   = var.allow_unsafe_apply ? 1 : 0
  identifier              = "{rule_id.lower()}-fixture"
  allocated_storage       = 20
  engine                  = "postgres"
  instance_class          = "db.t3.micro"
  username                = "{username}"
  password                = var.db_password
  skip_final_snapshot     = true
  apply_immediately       = true
{insecure_settings}
  tags = {{ Purpose = "cspm-misconfiguration-fixture" }}
}}
''',
    )


def rds_cluster_template(rule_id: str, description: str, insecure_settings: str, username: str = "fixture_admin") -> Template:
    """Create an Aurora MySQL cluster fixture for direct cluster findings."""
    return Template(
        description,
        COMMON + f'''variable "db_password" {{
  description = "Password for this disposable fixture. Set TF_VAR_db_password rather than committing a value."
  type        = string
  sensitive   = true
}}

resource "aws_rds_cluster" "fixture" {{
  count               = var.allow_unsafe_apply ? 1 : 0
  cluster_identifier  = "{rule_id.lower()}-fixture"
  engine              = "aurora-mysql"
  master_username     = "{username}"
  master_password     = var.db_password
  skip_final_snapshot = true
  apply_immediately   = true
{insecure_settings}
  tags = {{ Purpose = "cspm-misconfiguration-fixture" }}
}}
''',
    )


LAMBDA_COMMON = COMMON + '''terraform {
  required_providers {
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
}

'''


AZURE_COMMON = '''terraform {
  required_version = ">= 1.5.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.azure_subscription_id
}

variable "azure_subscription_id" {
  description = "Azure subscription ID for the dedicated test subscription."
  type        = string
}

variable "azure_location" {
  description = "Azure region for the fixture."
  type        = string
  default     = "centralindia"
}

variable "allow_unsafe_apply" {
  description = "Must be explicitly true before this intentionally insecure fixture is created."
  type        = bool
  default     = false
}

'''


def azure_storage_template(rule_id: str, description: str, settings: str = "", extra: str = "") -> Template:
    slug = rule_id.lower().replace("-", "")
    return Template(
        description,
        AZURE_COMMON + f'''resource "random_string" "fixture" {{
  length  = 10
  special = false
  upper   = false
}}

resource "azurerm_resource_group" "fixture" {{
  count    = var.allow_unsafe_apply ? 1 : 0
  name     = "{slug}-rg"
  location = var.azure_location
}}

resource "azurerm_storage_account" "fixture" {{
  count                    = var.allow_unsafe_apply ? 1 : 0
  name                     = "cspm${{random_string.fixture.result}}"
  resource_group_name      = azurerm_resource_group.fixture[0].name
  location                 = azurerm_resource_group.fixture[0].location
  account_tier             = "Standard"
  account_replication_type = "LRS"
{settings}
}}

{extra}''',
    )


def azure_nsg_template(rule_id: str, description: str, rule: str) -> Template:
    return Template(description, AZURE_COMMON + f'''resource "azurerm_resource_group" "fixture" {{
  count    = var.allow_unsafe_apply ? 1 : 0
  name     = "{rule_id.lower()}-rg"
  location = var.azure_location
}}

resource "azurerm_network_security_group" "fixture" {{
  count               = var.allow_unsafe_apply ? 1 : 0
  name                = "{rule_id.lower()}-nsg"
  location            = azurerm_resource_group.fixture[0].location
  resource_group_name = azurerm_resource_group.fixture[0].name

{rule}
}}
''')


def azure_managed_disk_template(rule_id: str, description: str) -> Template:
    return Template(description, AZURE_COMMON + f'''resource "azurerm_resource_group" "fixture" {{
  count    = var.allow_unsafe_apply ? 1 : 0
  name     = "{rule_id.lower()}-rg"
  location = var.azure_location
}}

resource "azurerm_managed_disk" "fixture" {{
  count                = var.allow_unsafe_apply ? 1 : 0
  name                 = "{rule_id.lower()}-disk"
  location             = azurerm_resource_group.fixture[0].location
  resource_group_name  = azurerm_resource_group.fixture[0].name
  storage_account_type = "Standard_LRS"
  create_option        = "Empty"
  disk_size_gb         = 4
}}
''')


def azure_sql_template(rule_id: str, description: str, server_settings: str = "", extra: str = "") -> Template:
    slug = rule_id.lower().replace("-", "")
    return Template(description, AZURE_COMMON + f'''variable "sql_admin_password" {{
  description = "Password for the disposable Azure SQL administrator. Set TF_VAR_sql_admin_password."
  type        = string
  sensitive   = true
}}

resource "random_string" "fixture" {{
  length  = 10
  special = false
  upper   = false
}}

resource "azurerm_resource_group" "fixture" {{
  count    = var.allow_unsafe_apply ? 1 : 0
  name     = "{slug}-rg"
  location = var.azure_location
}}

resource "azurerm_mssql_server" "fixture" {{
  count                         = var.allow_unsafe_apply ? 1 : 0
  name                          = "cspm${{random_string.fixture.result}}"
  resource_group_name           = azurerm_resource_group.fixture[0].name
  location                      = azurerm_resource_group.fixture[0].location
  version                       = "12.0"
  administrator_login           = "fixtureadmin"
  administrator_login_password  = var.sql_admin_password
  public_network_access_enabled = true
{server_settings}
}}

resource "azurerm_mssql_database" "fixture" {{
  count     = var.allow_unsafe_apply ? 1 : 0
  name      = "fixturedb"
  server_id = azurerm_mssql_server.fixture[0].id
  sku_name  = "Basic"
}}

{extra}''')


def azure_excessive_rbac_template(rule_id: str, description: str) -> Template:
    return Template(description, AZURE_COMMON + f'''data "azurerm_client_config" "current" {{}}

resource "azurerm_resource_group" "fixture" {{
  count    = var.allow_unsafe_apply ? 1 : 0
  name     = "{rule_id.lower()}-rg"
  location = var.azure_location
}}

resource "azurerm_role_definition" "fixture" {{
  count       = var.allow_unsafe_apply ? 1 : 0
  name        = "{rule_id.lower()}-excessive"
  scope       = azurerm_resource_group.fixture[0].id
  description = "INTENTIONALLY INSECURE: grants all Azure actions"

  permissions {{
    actions = ["*"]
  }}

  assignable_scopes = [azurerm_resource_group.fixture[0].id]
}}

resource "azurerm_role_assignment" "fixture" {{
  count              = var.allow_unsafe_apply ? 1 : 0
  scope              = azurerm_resource_group.fixture[0].id
  role_definition_id = azurerm_role_definition.fixture[0].role_definition_resource_id
  principal_id       = data.azurerm_client_config.current.object_id
}}
''')


def lambda_function_template(rule_id: str, description: str, function_settings: str = "", extra: str = "", runtime: str = "python3.12") -> Template:
    """Create a minimal Python Lambda and its execution role for one fixture."""
    slug = rule_id.lower()
    return Template(
        description,
        LAMBDA_COMMON + f'''data "archive_file" "fixture" {{
  type                    = "zip"
  output_path             = "${{path.module}}/{slug}.zip"
  source_content          = "def handler(event, context): return {{'statusCode': 200, 'body': 'fixture'}}"
  source_content_filename = "index.py"
}}

resource "aws_iam_role" "fixture" {{
  count = var.allow_unsafe_apply ? 1 : 0
  name  = "{slug}-lambda-role"
  assume_role_policy = jsonencode({{
    Version   = "2012-10-17"
    Statement = [{{ Effect = "Allow", Principal = {{ Service = "lambda.amazonaws.com" }}, Action = "sts:AssumeRole" }}]
  }})
}}

resource "aws_lambda_function" "fixture" {{
  count            = var.allow_unsafe_apply ? 1 : 0
  function_name    = "{slug}-fixture"
  role             = aws_iam_role.fixture[0].arn
  handler          = "index.handler"
  runtime          = "{runtime}"
  filename         = data.archive_file.fixture.output_path
  source_code_hash = data.archive_file.fixture.output_base64sha256
{function_settings}
}}

{extra}''',
    )


TEMPLATES: dict[str, Template] = {
    "CSPM-AWS-2024-0029": Template(
        "Creates a security group with 0.0.0.0/0 ingress across TCP ports 0-65535.",
        COMMON + '''resource "aws_security_group" "all_inbound" {
  count       = var.allow_unsafe_apply ? 1 : 0
  name        = "cspm-all-inbound-fixture"
  description = "INTENTIONALLY INSECURE: fixture for CSPM-AWS-2024-0029"

  ingress {
    description = "INTENTIONALLY INSECURE: public access to all TCP ports"
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress = []

  tags = { Purpose = "cspm-misconfiguration-fixture" }
}
''',
    ),
    "CSPM-AWS-2024-0033-08": Template(
        "Creates a security group with public SSH ingress on port 22.",
        COMMON + '''resource "aws_security_group" "public_ssh" {
  count       = var.allow_unsafe_apply ? 1 : 0
  name        = "cspm-public-ssh-fixture"
  description = "INTENTIONALLY INSECURE: fixture for CSPM-AWS-2024-0033-08"

  ingress {
    description = "INTENTIONALLY INSECURE: SSH exposed to the internet"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress = []

  tags = { Purpose = "cspm-misconfiguration-fixture" }
}
''',
    ),
    "CSPM-AWS-2024-0110": Template(
        "Creates a publicly accessible PostgreSQL RDS instance with a generated password.",
        COMMON + '''variable "db_password" {
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
''',
    ),
    "CSPM-AWS-2024-0164": Template(
        "Creates an S3 bucket with all account-level public-access protections disabled at bucket level.",
        COMMON + '''resource "aws_s3_bucket" "public_access_block_disabled" {
  count         = var.allow_unsafe_apply ? 1 : 0
  bucket_prefix = "cspm-public-access-block-"

  tags = { Purpose = "cspm-misconfiguration-fixture" }
}

resource "aws_s3_bucket_public_access_block" "disabled" {
  count                   = var.allow_unsafe_apply ? 1 : 0
  bucket                  = aws_s3_bucket.public_access_block_disabled[0].id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}
''',
    ),
}

# These mappings are explicit reviewed translations of rule conditions, not
# title-based guesses. Each fixture creates only the condition for its rule.
_PUBLIC_TCP_PORT_RULES = {
    "CSPM-AWS-2024-0033-01": ("mysql", 3306, "public MySQL ingress"),
    "CSPM-AWS-2024-0033-02": ("dns", 53, "public DNS-over-TCP ingress"),
    "CSPM-AWS-2024-0033-03": ("mongodb", 27017, "public MongoDB ingress"),
    "CSPM-AWS-2024-0033-04": ("mssql", 1433, "public Microsoft SQL Server ingress"),
    "CSPM-AWS-2024-0033-05": ("oracle", 1521, "public Oracle Database ingress"),
    "CSPM-AWS-2024-0033-06": ("postgres", 5432, "public PostgreSQL ingress"),
    "CSPM-AWS-2024-0033-07": ("rdp", 3389, "public RDP ingress"),
    "CSPM-AWS-2024-0033-09": ("nfs", 2049, "public NFS ingress"),
    "CSPM-AWS-2024-0033-10": ("smtp", 25, "public SMTP ingress"),
}

for _rule_id, (_service, _port, _description) in _PUBLIC_TCP_PORT_RULES.items():
    TEMPLATES[_rule_id] = Template(
        f"Creates a security group allowing public TCP access to {_service} on port {_port}.",
        security_group_template(f"cspm-public-{_service}-fixture", _description, "tcp", _port, _port),
    )

TEMPLATES.update({
    "CSPM-AWS-2024-0027": Template(
        "Creates an EC2 instance with a public IPv4 address, in an isolated test VPC.",
        COMMON + '''resource "aws_vpc" "fixture" {
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
''',
    ),
    "CSPM-AWS-2024-0020": Template(
        "Creates a VPC whose default security group has an inbound rule.",
        COMMON + '''resource "aws_vpc" "fixture" {
  count      = var.allow_unsafe_apply ? 1 : 0
  cidr_block = "10.250.0.0/16"

  tags = { Purpose = "cspm-misconfiguration-fixture" }
}

resource "aws_default_security_group" "non_empty" {
  count  = var.allow_unsafe_apply ? 1 : 0
  vpc_id = aws_vpc.fixture[0].id

  ingress {
    description = "INTENTIONALLY INSECURE: non-empty default security group"
    protocol    = "tcp"
    from_port   = 22
    to_port     = 22
    cidr_blocks = ["10.0.0.0/8"]
  }

  egress = []
}
''',
    ),
    "CSPM-AWS-2024-0023": Template(
        "Creates an unencrypted EBS volume in the first available zone.",
        COMMON + '''resource "aws_ebs_volume" "unencrypted" {
  count             = var.allow_unsafe_apply ? 1 : 0
  availability_zone = var.availability_zone
  size              = 1
  encrypted         = false

  tags = { Purpose = "cspm-misconfiguration-fixture" }
}
''',
    ),
    "CSPM-AWS-2024-0032": Template(
        "Creates a security group allowing all public ICMP traffic.",
        security_group_template("cspm-public-icmp-fixture", "all ICMP exposed to the internet", "icmp", -1, -1),
    ),
    "CSPM-AWS-2024-0034-01": Template(
        "Creates a security group allowing FTP ingress on port 21.",
        security_group_template("cspm-ftp-fixture", "FTP ingress", "tcp", 21, 21, "10.0.0.0/8"),
    ),
    "CSPM-AWS-2024-0034-02": Template(
        "Creates a security group allowing Telnet ingress on port 23.",
        security_group_template("cspm-telnet-fixture", "Telnet ingress", "tcp", 23, 23, "10.0.0.0/8"),
    ),
    "CSPM-AWS-2024-0035": Template(
        "Creates a security group allowing a broad TCP port range.",
        security_group_template("cspm-port-range-fixture", "broad TCP port range", "tcp", 1000, 2000, "10.0.0.0/8"),
    ),
    "CSPM-AWS-2024-0476": Template(
        "Creates a security group with unrestricted IPv4 egress.",
        COMMON + '''resource "aws_security_group" "unrestricted_egress" {
  count       = var.allow_unsafe_apply ? 1 : 0
  name        = "cspm-unrestricted-egress-fixture"
  description = "INTENTIONALLY INSECURE: unrestricted egress"

  egress {
    description = "INTENTIONALLY INSECURE: all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Purpose = "cspm-misconfiguration-fixture" }
}
''',
    ),
})

# CIEM IAM scenarios. The two usage-history rules (CIEM-AWS-2024-0001 and
# CIEM-AWS-2024-0007) are intentionally not represented here: Terraform can
# create principals but cannot make AWS report historical inactivity.
TEMPLATES.update({
    "CIEM-AWS-2024-0002": Template(
        "Creates an IAM user with an intentionally over-permissive inline policy.",
        COMMON + '''resource "aws_iam_user" "fixture" {
  count = var.allow_unsafe_apply ? 1 : 0
  name  = "ciem-excessive-user-fixture"
}

resource "aws_iam_user_policy" "excessive" {
  count  = var.allow_unsafe_apply ? 1 : 0
  name   = "ciem-excessive-user-policy"
  user   = aws_iam_user.fixture[0].name
  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = "*", Resource = "*" }]
  })
}
''',
    ),
    "CIEM-AWS-2024-0003": Template(
        "Creates an IAM group with no assigned users.",
        COMMON + '''resource "aws_iam_group" "fixture" {
  count = var.allow_unsafe_apply ? 1 : 0
  name  = "ciem-empty-group-fixture"
}
''',
    ),
    "CIEM-AWS-2024-0004": Template(
        "Creates an IAM group with an intentionally over-permissive inline policy.",
        COMMON + '''resource "aws_iam_group" "fixture" {
  count = var.allow_unsafe_apply ? 1 : 0
  name  = "ciem-excessive-group-fixture"
}

resource "aws_iam_group_policy" "excessive" {
  count  = var.allow_unsafe_apply ? 1 : 0
  name   = "ciem-excessive-group-policy"
  group  = aws_iam_group.fixture[0].name
  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = "*", Resource = "*" }]
  })
}
''',
    ),
    "CIEM-AWS-2024-0005": Template(
        "Creates an unattached customer-managed IAM policy.",
        COMMON + '''resource "aws_iam_policy" "fixture" {
  count       = var.allow_unsafe_apply ? 1 : 0
  name        = "ciem-unattached-policy-fixture"
  description = "INTENTIONALLY INSECURE: unattached customer-managed policy"
  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = ["s3:GetObject"], Resource = "*" }]
  })
}
''',
    ),
    "CIEM-AWS-2024-0006": Template(
        "Creates an intentionally over-permissive customer-managed IAM policy.",
        COMMON + '''resource "aws_iam_policy" "fixture" {
  count       = var.allow_unsafe_apply ? 1 : 0
  name        = "ciem-excessive-managed-policy-fixture"
  description = "INTENTIONALLY INSECURE: administrator-style managed policy"
  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = "*", Resource = "*" }]
  })
}
''',
    ),
    "CIEM-AWS-2024-0008": Template(
        "Creates an IAM role with an intentionally over-permissive inline policy.",
        COMMON + '''resource "aws_iam_role" "fixture" {
  count = var.allow_unsafe_apply ? 1 : 0
  name  = "ciem-excessive-role-fixture"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "ec2.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
}

resource "aws_iam_role_policy" "excessive" {
  count  = var.allow_unsafe_apply ? 1 : 0
  name   = "ciem-excessive-role-policy"
  role   = aws_iam_role.fixture[0].id
  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = "*", Resource = "*" }]
  })
}
''',
    ),
    "CIEM-AWS-2024-0009": Template(
        "Creates an IAM role inline policy with intentionally excessive permissions.",
        COMMON + '''resource "aws_iam_role" "fixture" {
  count = var.allow_unsafe_apply ? 1 : 0
  name  = "ciem-role-inline-policy-fixture"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "ec2.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
}

resource "aws_iam_role_policy" "fixture" {
  count  = var.allow_unsafe_apply ? 1 : 0
  name   = "ciem-overly-permissive-inline-policy"
  role   = aws_iam_role.fixture[0].id
  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = "*", Resource = "*" }]
  })
}
''',
    ),
    "CIEM-AWS-2024-0010": Template(
        "Creates an IAM user inline policy with intentionally excessive permissions.",
        COMMON + '''resource "aws_iam_user" "fixture" {
  count = var.allow_unsafe_apply ? 1 : 0
  name  = "ciem-user-inline-policy-fixture"
}

resource "aws_iam_user_policy" "fixture" {
  count  = var.allow_unsafe_apply ? 1 : 0
  name   = "ciem-overly-permissive-inline-policy"
  user   = aws_iam_user.fixture[0].name
  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = "*", Resource = "*" }]
  })
}
''',
    ),
    "CIEM-AWS-2024-0011": Template(
        "Creates an IAM group inline policy with intentionally excessive permissions.",
        COMMON + '''resource "aws_iam_group" "fixture" {
  count = var.allow_unsafe_apply ? 1 : 0
  name  = "ciem-group-inline-policy-fixture"
}

resource "aws_iam_group_policy" "fixture" {
  count  = var.allow_unsafe_apply ? 1 : 0
  name   = "ciem-overly-permissive-inline-policy"
  group  = aws_iam_group.fixture[0].name
  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = "*", Resource = "*" }]
  })
}
''',
    ),
})

# RDS batch 1: direct DB-instance configuration findings. Aurora, snapshots,
# event subscriptions, and usage-history rules are intentionally handled in
# later batches because they need different supporting infrastructure.
TEMPLATES.update({
    "CSPM-AWS-2024-0107": rds_instance_template("CSPM-AWS-2024-0107", "Creates an RDS instance with automated backups disabled.", "  backup_retention_period = 0\n"),
    "CSPM-AWS-2024-0109": rds_instance_template("CSPM-AWS-2024-0109", "Creates an RDS instance with automatic minor version upgrades disabled.", "  auto_minor_version_upgrade = false\n"),
    "CSPM-AWS-2024-0111": rds_instance_template("CSPM-AWS-2024-0111", "Creates an RDS instance with a one-day backup retention period.", "  backup_retention_period = 1\n"),
    "CSPM-AWS-2024-0112": rds_instance_template("CSPM-AWS-2024-0112", "Creates a single-AZ RDS instance without automatic failover.", "  multi_az = false\n"),
    "CSPM-AWS-2024-0113": rds_instance_template("CSPM-AWS-2024-0113", "Creates an RDS instance without storage encryption.", "  storage_encrypted = false\n"),
    "CSPM-AWS-2024-0333": rds_instance_template("CSPM-AWS-2024-0333", "Creates an RDS instance with IAM database authentication disabled.", "  iam_database_authentication_enabled = false\n"),
    "CSPM-AWS-2024-0336-01": rds_instance_template("CSPM-AWS-2024-0336-01", "Creates a single-AZ RDS instance.", "  multi_az = false\n"),
    "CSPM-AWS-2024-0338": rds_instance_template("CSPM-AWS-2024-0338", "Creates an RDS instance that does not copy tags to snapshots.", "  copy_tags_to_snapshot = false\n"),
    "CSPM-AWS-2024-0344": rds_instance_template("CSPM-AWS-2024-0344", "Creates a PostgreSQL RDS instance on its default port 5432.", "  port = 5432\n"),
    "CSPM-AWS-2024-0346": rds_instance_template("CSPM-AWS-2024-0346", "Creates an RDS instance using the default-style administrator username admin.", "", username="admin"),
})

TEMPLATES.update({
    "CSPM-AWS-2024-0334": rds_cluster_template("CSPM-AWS-2024-0334", "Creates an Aurora cluster with IAM database authentication disabled.", "  iam_database_authentication_enabled = false\n"),
    "CSPM-AWS-2024-0337": rds_cluster_template("CSPM-AWS-2024-0337", "Creates an Aurora cluster that does not copy tags to snapshots.", "  copy_tags_to_snapshot = false\n"),
    "CSPM-AWS-2024-0345": rds_cluster_template("CSPM-AWS-2024-0345", "Creates an Aurora cluster using admin as its master username.", "", username="admin"),
    "CSPM-AWS-2024-0348": rds_cluster_template("CSPM-AWS-2024-0348", "Creates an Aurora cluster without storage encryption.", "  storage_encrypted = false\n"),
    "CSPM-AWS-2024-0350": rds_cluster_template("CSPM-AWS-2024-0350", "Creates an Aurora MySQL cluster without audit log exports.", "  enabled_cloudwatch_logs_exports = []\n"),
    "CSPM-AWS-2024-0351": rds_cluster_template("CSPM-AWS-2024-0351", "Creates an Aurora cluster with automatic minor version upgrades disabled.", "  auto_minor_version_upgrade = false\n"),
    "CSPM-AWS-2024-0354": rds_cluster_template("CSPM-AWS-2024-0354", "Creates an Aurora cluster with deletion protection disabled.", "  deletion_protection = false\n"),
})

TEMPLATES.update({
    "CSPM-AWS-2024-0347": rds_instance_template("CSPM-AWS-2024-0347", "Creates an RDS instance without automated backup retention.", "  backup_retention_period = 0\n"),
    "CSPM-AWS-2024-0349": rds_instance_template("CSPM-AWS-2024-0349", "Creates an RDS instance without encryption at rest.", "  storage_encrypted = false\n"),
    "CSPM-AWS-2024-0353": rds_instance_template("CSPM-AWS-2024-0353", "Creates an RDS instance with enhanced monitoring disabled.", "  monitoring_interval = 0\n"),
    "CSPM-AWS-2024-0355": rds_instance_template("CSPM-AWS-2024-0355", "Creates an RDS instance with deletion protection disabled.", "  deletion_protection = false\n"),
    "CSPM-AWS-2024-0356": rds_instance_template("CSPM-AWS-2024-0356", "Creates a PostgreSQL RDS instance without CloudWatch log exports.", "  enabled_cloudwatch_logs_exports = []\n"),
})

TEMPLATES.update({
    "CSPM-AWS-2024-0167": Template(
        "Creates a VPC without a VPC Flow Log.",
        COMMON + '''resource "aws_vpc" "fixture" {
  count      = var.allow_unsafe_apply ? 1 : 0
  cidr_block = "10.245.0.0/16"

  tags = { Name = "cspm-vpc-no-flow-logs" }
}
''',
    ),
    "CSPM-AWS-2024-0231": Template(
        "Creates a Transit Gateway that automatically accepts shared attachments.",
        COMMON + '''resource "aws_ec2_transit_gateway" "fixture" {
  count                          = var.allow_unsafe_apply ? 1 : 0
  auto_accept_shared_attachments = "enable"
  description                    = "INTENTIONALLY INSECURE: automatic shared-attachment acceptance"

  tags = { Name = "cspm-transit-gateway-auto-accept" }
}
''',
    ),
    "CSPM-AWS-2024-0488": Template(
        "Creates an S3 gateway VPC endpoint with an intentionally public endpoint policy.",
        COMMON + '''resource "aws_vpc" "fixture" {
  count      = var.allow_unsafe_apply ? 1 : 0
  cidr_block = "10.246.0.0/16"
}

resource "aws_route_table" "fixture" {
  count  = var.allow_unsafe_apply ? 1 : 0
  vpc_id = aws_vpc.fixture[0].id
}

resource "aws_vpc_endpoint" "fixture" {
  count           = var.allow_unsafe_apply ? 1 : 0
  vpc_id          = aws_vpc.fixture[0].id
  service_name    = "com.amazonaws.${var.aws_region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids = [aws_route_table.fixture[0].id]
  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = "*", Action = "*", Resource = "*" }]
  })
}
''',
    ),
    "CSPM-AWS-2024-0580": Template(
        "Creates a VPC whose Name tag intentionally violates the required naming convention.",
        COMMON + '''resource "aws_vpc" "fixture" {
  count      = var.allow_unsafe_apply ? 1 : 0
  cidr_block = "10.247.0.0/16"

  tags = { Name = "invalid-vpc-name" }
}
''',
    ),
})

TEMPLATES.update({
    "CSPM-AWS-2024-0294": lambda_function_template(
        "CSPM-AWS-2024-0294",
        "Creates a Lambda resource policy that permits public invocation.",
        extra='''resource "aws_lambda_permission" "public_invoke" {
  count         = var.allow_unsafe_apply ? 1 : 0
  statement_id  = "AllowPublicInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.fixture[0].function_name
  principal     = "*"
}
''',
    ),
    "CSPM-AWS-2024-0296": lambda_function_template(
        "CSPM-AWS-2024-0296",
        "Creates a Lambda function without VPC configuration.",
    ),
    "CSPM-AWS-2024-0297": lambda_function_template(
        "CSPM-AWS-2024-0297",
        "Creates a VPC Lambda function configured with only one subnet.",
        function_settings='''  vpc_config {
    subnet_ids         = [aws_subnet.fixture[0].id]
    security_group_ids = [aws_security_group.fixture[0].id]
  }
''',
        extra='''resource "aws_vpc" "fixture" {
  count      = var.allow_unsafe_apply ? 1 : 0
  cidr_block = "10.249.0.0/16"
}

resource "aws_subnet" "fixture" {
  count      = var.allow_unsafe_apply ? 1 : 0
  vpc_id     = aws_vpc.fixture[0].id
  cidr_block = "10.249.1.0/24"
}

resource "aws_security_group" "fixture" {
  count  = var.allow_unsafe_apply ? 1 : 0
  name   = "cspm-lambda-single-subnet"
  vpc_id = aws_vpc.fixture[0].id
  egress = []
}

resource "aws_iam_role_policy_attachment" "vpc_access" {
  count      = var.allow_unsafe_apply ? 1 : 0
  role       = aws_iam_role.fixture[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}
''',
    ),
    "CSPM-AWS-2024-0444": lambda_function_template(
        "CSPM-AWS-2024-0444",
        "Creates environment variables without a customer-managed KMS key.",
        function_settings='''  environment {
    variables = { SECRET_REFERENCE = "intentionally-not-kms-encrypted" }
  }
''',
    ),
    "CSPM-AWS-2024-0445": lambda_function_template(
        "CSPM-AWS-2024-0445",
        "Creates a Lambda function without a customer-managed KMS key.",
        function_settings='''  environment {
    variables = { FIXTURE = "no-customer-kms-key" }
  }
''',
    ),
    "CSPM-AWS-2024-0295": lambda_function_template(
        "CSPM-AWS-2024-0295",
        "Creates a Lambda using Python 3.13, which is absent from this rule's approved runtime list.",
        runtime="python3.13",
    ),
    "CSPM-AWS-2024-0446": lambda_function_template(
        "CSPM-AWS-2024-0446",
        "Creates a Lambda Function URL with unauthenticated NONE authorization.",
        extra='''resource "aws_lambda_function_url" "fixture" {
  count         = var.allow_unsafe_apply ? 1 : 0
  function_name = aws_lambda_function.fixture[0].function_name
  authorization_type = "NONE"
}
''',
    ),
    "CSPM-AWS-2024-0546": lambda_function_template(
        "CSPM-AWS-2024-0546",
        "Creates a Lambda resource policy granting all Lambda actions to every principal.",
        extra='''resource "aws_lambda_permission" "public_administration" {
  count         = var.allow_unsafe_apply ? 1 : 0
  statement_id  = "AllowPublicLambdaAdministration"
  action        = "lambda:*"
  function_name = aws_lambda_function.fixture[0].function_name
  principal     = "*"
}
''',
    ),
    "CSPM-AWS-2024-0547": lambda_function_template(
        "CSPM-AWS-2024-0547",
        "Creates a Lambda Function URL.",
        extra='''resource "aws_lambda_function_url" "fixture" {
  count              = var.allow_unsafe_apply ? 1 : 0
  function_name      = aws_lambda_function.fixture[0].function_name
  authorization_type = "NONE"
}
''',
    ),
})

TEMPLATES.update({
    "CSPM-AZURE-2024-0071": azure_storage_template("CSPM-AZURE-2024-0071", "Creates a storage account without secure-transfer enforcement.", "  https_traffic_only_enabled = false\n"),
    "CSPM-AZURE-2024-0072": azure_storage_template("CSPM-AZURE-2024-0072", "Creates a storage account without a customer-managed encryption key."),
    "CSPM-AZURE-2024-0073": azure_storage_template("CSPM-AZURE-2024-0073", "Creates a public blob container.", "  allow_nested_items_to_be_public = true\n", '''resource "azurerm_storage_container" "fixture" {
  count                 = var.allow_unsafe_apply ? 1 : 0
  name                  = "public"
  storage_account_id    = azurerm_storage_account.fixture[0].id
  container_access_type = "blob"
}
'''),
    "CSPM-AZURE-2024-0074": azure_storage_template("CSPM-AZURE-2024-0074", "Creates a storage account permitting public blob access.", "  allow_nested_items_to_be_public = true\n"),
    "CSPM-AZURE-2024-0075": azure_storage_template("CSPM-AZURE-2024-0075", "Creates a storage account without blob soft delete retention."),
    "CSPM-AZURE-2024-0076": azure_storage_template("CSPM-AZURE-2024-0076", "Creates storage network rules without a trusted-services bypass.", '''  network_rules {
    default_action = "Deny"
    bypass         = ["None"]
  }
'''),
    "CSPM-AZURE-2024-0131": azure_storage_template("CSPM-AZURE-2024-0131", "Creates a storage account without infrastructure encryption.", "  infrastructure_encryption_enabled = false\n"),
    "CSPM-AZURE-2024-0136": azure_storage_template("CSPM-AZURE-2024-0136", "Creates storage network rules with default access allowed.", '''  network_rules {
    default_action = "Allow"
  }
'''),
    "CSPM-AZURE-2024-0141": azure_storage_template("CSPM-AZURE-2024-0141", "Creates a storage account allowing TLS 1.0.", "  min_tls_version = \"TLS1_0\"\n"),
    "CSPM-AZURE-2024-0142": azure_storage_template("CSPM-AZURE-2024-0142", "Creates a storage account allowing cross-tenant replication.", "  allow_cross_tenant_replication = true\n"),
    "CSPM-AZURE-2024-0132": azure_storage_template("CSPM-AZURE-2024-0132", "Creates a storage account without a key-expiration policy."),
    "CSPM-AZURE-2024-0134": azure_storage_template("CSPM-AZURE-2024-0134", "Creates a storage account without Queue service logging."),
    "CSPM-AZURE-2024-0138": azure_storage_template("CSPM-AZURE-2024-0138", "Creates storage without customer-managed encryption keys."),
    "CSPM-AZURE-2024-0260": azure_storage_template("CSPM-AZURE-2024-0260", "Creates a storage account permitting public access.", "  allow_nested_items_to_be_public = true\n"),
    "CSPM-AZURE-2024-0303": azure_storage_template("CSPM-AZURE-2024-0303", "Creates a storage account without restricted network access.", "  public_network_access_enabled = true\n"),
    "CSPM-AZURE-2024-0304": azure_storage_template("CSPM-AZURE-2024-0304", "Creates a storage account without virtual network rules."),
    "CSPM-AZURE-2024-0531": azure_storage_template("CSPM-AZURE-2024-0531", "Creates locally redundant rather than geo-redundant storage."),
    "CSPM-AZURE-2024-0792": azure_storage_template("CSPM-AZURE-2024-0792", "Creates a storage account without secure-transfer enforcement.", "  https_traffic_only_enabled = false\n"),
    "CSPM-AZURE-2024-0833": azure_storage_template("CSPM-AZURE-2024-0833", "Creates storage without a customer-managed encryption key."),
    "CSPM-AZURE-2024-0858": azure_storage_template("CSPM-AZURE-2024-0858", "Creates a storage account without infrastructure encryption.", "  infrastructure_encryption_enabled = false\n"),
})

TEMPLATES.update({
    "CSPM-AZURE-2024-0025": azure_nsg_template("CSPM-AZURE-2024-0025", "Creates an NSG allowing all inbound traffic.", '''  security_rule {
    name = "allow-all-inbound"
    priority = 100
    direction = "Inbound"
    access = "Allow"
    protocol = "*"
    source_port_range = "*"
    destination_port_range = "*"
    source_address_prefix = "*"
    destination_address_prefix = "*"
  }'''),
    "CSPM-AZURE-2024-0026": azure_nsg_template("CSPM-AZURE-2024-0026", "Creates an NSG allowing public Microsoft SQL Server access.", '''  security_rule {
    name = "allow-public-mssql"
    priority = 100
    direction = "Inbound"
    access = "Allow"
    protocol = "Tcp"
    source_port_range = "*"
    destination_port_range = "1433"
    source_address_prefix = "*"
    destination_address_prefix = "*"
  }'''),
    "CSPM-AZURE-2024-0027": azure_nsg_template("CSPM-AZURE-2024-0027", "Creates an NSG allowing public UDP traffic.", '''  security_rule {
    name = "allow-public-udp"
    priority = 100
    direction = "Inbound"
    access = "Allow"
    protocol = "Udp"
    source_port_range = "*"
    destination_port_range = "*"
    source_address_prefix = "*"
    destination_address_prefix = "*"
  }'''),
    "CSPM-AZURE-2024-0028": azure_nsg_template("CSPM-AZURE-2024-0028", "Creates an NSG allowing public SSH access.", '''  security_rule {
    name = "allow-public-ssh"
    priority = 100
    direction = "Inbound"
    access = "Allow"
    protocol = "Tcp"
    source_port_range = "*"
    destination_port_range = "22"
    source_address_prefix = "*"
    destination_address_prefix = "*"
  }'''),
    "CSPM-AZURE-2024-0261": azure_nsg_template("CSPM-AZURE-2024-0261", "Creates an NSG with unrestricted inbound ports.", '''  security_rule {
    name = "unrestricted-inbound"
    priority = 100
    direction = "Inbound"
    access = "Allow"
    protocol = "*"
    source_port_range = "*"
    destination_port_range = "*"
    source_address_prefix = "Internet"
    destination_address_prefix = "*"
  }'''),
})

TEMPLATES.update({
    "CSPM-AZURE-2024-0080": azure_managed_disk_template("CSPM-AZURE-2024-0080", "Creates a managed disk using the platform-managed encryption key."),
    "CSPM-AZURE-2024-0081": azure_managed_disk_template("CSPM-AZURE-2024-0081", "Creates an unattached managed disk using the platform-managed encryption key."),
    "CSPM-AZURE-2024-0173": azure_managed_disk_template("CSPM-AZURE-2024-0173", "Creates a managed disk without a customer-managed encryption key."),
    "CSPM-AZURE-2024-0824": azure_managed_disk_template("CSPM-AZURE-2024-0824", "Creates a managed disk without double encryption."),
    "CSPM-AZURE-2024-1074": azure_managed_disk_template("CSPM-AZURE-2024-1074", "Creates an unattached managed disk."),
})

TEMPLATES.update({
    "CIEM-AZURE-2024-0007": azure_excessive_rbac_template("CIEM-AZURE-2024-0007", "Creates an Azure custom RBAC role granting all actions and assigns it to the current principal."),
})

TEMPLATES.update({
    "CSPM-AZURE-2024-0050": azure_sql_template("CSPM-AZURE-2024-0050", "Creates an Azure SQL firewall rule allowing all IPv4 addresses.", extra='''resource "azurerm_mssql_firewall_rule" "any" {
  count            = var.allow_unsafe_apply ? 1 : 0
  name             = "AllowAllIPv4"
  server_id        = azurerm_mssql_server.fixture[0].id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "255.255.255.255"
}
'''),
    "CSPM-AZURE-2024-0051": azure_sql_template("CSPM-AZURE-2024-0051", "Creates an Azure SQL database without an adequate auditing retention policy."),
    "CSPM-AZURE-2024-0052": azure_sql_template("CSPM-AZURE-2024-0052", "Creates an Azure SQL database with auditing disabled."),
    "CSPM-AZURE-2024-0053": azure_sql_template("CSPM-AZURE-2024-0053", "Creates an Azure SQL database without threat detection."),
    "CSPM-AZURE-2024-0055": azure_sql_template("CSPM-AZURE-2024-0055", "Creates an Azure SQL database without threat detection alerts."),
    "CSPM-AZURE-2024-0056": azure_sql_template("CSPM-AZURE-2024-0056", "Creates an Azure SQL database without adequate threat detection retention."),
    "CSPM-AZURE-2024-0057": azure_sql_template("CSPM-AZURE-2024-0057", "Creates an Azure SQL database without threat detection email alerts."),
    "CSPM-AZURE-2024-0059": azure_sql_template("CSPM-AZURE-2024-0059", "Creates an Azure SQL server without an Entra administrator."),
    "CSPM-AZURE-2024-0167-04": azure_sql_template("CSPM-AZURE-2024-0167-04", "Creates an Azure SQL database using the Basic SKU."),
    "CSPM-AZURE-2024-0299": azure_sql_template("CSPM-AZURE-2024-0299", "Creates an Azure SQL server with public network access enabled."),
})

# S3 fixtures intentionally avoid ACLs because modern buckets often enforce
# BucketOwnerEnforced object ownership. Public-policy scenarios explicitly turn
# off bucket-level public-access blocks in the disposable test environment.
TEMPLATES.update({
    "CSPM-AWS-2024-0126": Template(
        "Creates a bucket policy allowing object reads over clear-text HTTP.",
        s3_public_policy_template("cspm-http-bucket", '''{
        Sid       = "AllowInsecureTransport"
        Effect    = "Allow"
        Principal = "*"
        Action    = ["s3:GetObject"]
        Resource  = ["${aws_s3_bucket.fixture[0].arn}/*"]
        Condition = { Bool = { "aws:SecureTransport" = "false" } }
      }'''),
    ),
    "CSPM-AWS-2024-0128": Template(
        "Creates a bucket without server-access logging.",
        s3_bucket_template("cspm-no-logging-bucket"),
    ),
    "CSPM-AWS-2024-0130": Template(
        "Creates a bucket without versioning enabled.",
        s3_bucket_template("cspm-no-versioning-bucket"),
    ),
    "CSPM-AWS-2024-0132": Template(
        "Creates a bucket policy allowing everyone to delete objects.",
        s3_public_policy_template("cspm-public-delete-bucket", '''{
        Sid       = "AllowPublicDelete"
        Effect    = "Allow"
        Principal = "*"
        Action    = ["s3:DeleteObject"]
        Resource  = ["${aws_s3_bucket.fixture[0].arn}/*"]
      }'''),
    ),
    "CSPM-AWS-2024-0133": Template(
        "Creates a bucket policy allowing everyone all S3 actions.",
        s3_public_policy_template("cspm-public-all-actions-bucket", '''{
        Sid       = "AllowPublicAllActions"
        Effect    = "Allow"
        Principal = "*"
        Action    = ["s3:*"]
        Resource  = [aws_s3_bucket.fixture[0].arn, "${aws_s3_bucket.fixture[0].arn}/*"]
      }'''),
    ),
    "CSPM-AWS-2024-0165": Template(
        "Creates a bucket with every bucket-level public-access-block setting disabled.",
        s3_bucket_template("cspm-public-access-block-bucket", '''resource "aws_s3_bucket_public_access_block" "disabled" {
  count                   = var.allow_unsafe_apply ? 1 : 0
  bucket                  = aws_s3_bucket.fixture[0].id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}
'''),
    ),
    "CSPM-AWS-2024-0368": Template(
        "Creates a bucket without AWS KMS default encryption.",
        s3_bucket_template("cspm-no-kms-bucket"),
    ),
    "CSPM-AWS-2024-0490": Template(
        "Creates a bucket with website hosting enabled.",
        s3_bucket_template("cspm-website-bucket", '''resource "aws_s3_bucket_website_configuration" "fixture" {
  count  = var.allow_unsafe_apply ? 1 : 0
  bucket = aws_s3_bucket.fixture[0].id

  index_document { suffix = "index.html" }
}
'''),
    ),
    "CSPM-AWS-2024-0609": Template(
        "Creates a bucket policy allowing everyone to read objects.",
        s3_public_policy_template("cspm-public-read-bucket", '''{
        Sid       = "AllowPublicRead"
        Effect    = "Allow"
        Principal = "*"
        Action    = ["s3:GetObject"]
        Resource  = ["${aws_s3_bucket.fixture[0].arn}/*"]
      }'''),
    ),
    "CSPM-AWS-2024-0610": Template(
        "Creates a bucket policy allowing everyone to write objects.",
        s3_public_policy_template("cspm-public-write-bucket", '''{
        Sid       = "AllowPublicWrite"
        Effect    = "Allow"
        Principal = "*"
        Action    = ["s3:PutObject"]
        Resource  = ["${aws_s3_bucket.fixture[0].arn}/*"]
      }'''),
    ),
    "CSPM-AWS-2024-0616": Template(
        "Creates a bucket policy authorizing GetObject for all principals.",
        s3_public_policy_template("cspm-public-get-bucket", '''{
        Sid       = "AllowPublicGet"
        Effect    = "Allow"
        Principal = "*"
        Action    = ["s3:GetObject"]
        Resource  = ["${aws_s3_bucket.fixture[0].arn}/*"]
      }'''),
    ),
    "CSPM-AWS-2024-0617": Template(
        "Creates a bucket policy authorizing ListBucket for all principals.",
        s3_public_policy_template("cspm-public-list-bucket", '''{
        Sid       = "AllowPublicList"
        Effect    = "Allow"
        Principal = "*"
        Action    = ["s3:ListBucket"]
        Resource  = [aws_s3_bucket.fixture[0].arn]
      }'''),
    ),
})

# CNAPP-goat-style EC2 scenarios. These deliberately create full fixtures,
# rather than only isolated security-group rules, so the scenario catalog can
# provision and destroy them as complete test environments.
TEMPLATES.update({
    "CSPM-AWS-2024-0152": Template(
        "Creates an EC2 instance which permits IMDSv1 requests.",
        COMMON + '''resource "aws_vpc" "fixture" {
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
''',
    ),
    "CSPM-AWS-2024-0029": Template(
        "Creates a public EC2 instance protected by an intentionally open all-ports security group.",
        COMMON + '''resource "aws_vpc" "fixture" {
  count      = var.allow_unsafe_apply ? 1 : 0
  cidr_block = "10.252.0.0/16"
}

resource "aws_internet_gateway" "fixture" {
  count  = var.allow_unsafe_apply ? 1 : 0
  vpc_id = aws_vpc.fixture[0].id
}

resource "aws_subnet" "public" {
  count                   = var.allow_unsafe_apply ? 1 : 0
  vpc_id                  = aws_vpc.fixture[0].id
  cidr_block              = "10.252.1.0/24"
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

resource "aws_security_group" "open_public" {
  count       = var.allow_unsafe_apply ? 1 : 0
  name        = "cspm-open-public-ec2-fixture"
  description = "INTENTIONALLY INSECURE: all inbound TCP ports from the internet"
  vpc_id      = aws_vpc.fixture[0].id

  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress = []
}

resource "aws_instance" "open_public" {
  count                       = var.allow_unsafe_apply ? 1 : 0
  ami                         = var.ami_id
  instance_type               = "t3.micro"
  subnet_id                   = aws_subnet.public[0].id
  vpc_security_group_ids      = [aws_security_group.open_public[0].id]
  associate_public_ip_address = true

  tags = { Purpose = "cspm-misconfiguration-fixture" }
}
''',
    ),
    "CSPM-AWS-2024-0018": Template(
        "Creates an EBS volume and snapshot, then registers the snapshot as a public AMI.",
        COMMON + '''resource "aws_ebs_volume" "source" {
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
''',
    ),
})
