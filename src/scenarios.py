"""CNAPP-goat-style scenario catalog backed by reviewed CSPM rule fixtures."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    name: str
    module: str
    platform: str
    rule_id: str
    description: str

    @property
    def service(self) -> str:
        if self.platform == "Azure" and "-storage-" in self.scenario_id:
            return "Storage"
        if self.platform == "Azure" and "-nsg-" in self.scenario_id:
            return "Network"
        if self.platform == "Azure" and "-vm-" in self.scenario_id:
            return "Compute"
        if self.platform == "Azure" and "-sql-" in self.scenario_id:
            return "SQL"
        if self.module == "CIEM" and self.platform == "Azure":
            return "Authorization"
        if self.module == "CIEM":
            return "IAM"
        if "-lambda-" in self.scenario_id:
            return "Lambda"
        if "-vpc-" in self.scenario_id or "-transit-gateway-" in self.scenario_id:
            return "VPC"
        if self.scenario_id.startswith("cspm-aws-s3-"):
            return "S3"
        if "-rds-" in self.scenario_id:
            return "RDS"
        return "EC2"


SCENARIOS: tuple[Scenario, ...] = (
    Scenario(
        "cspm-aws-ec2-public-ip",
        "EC2 Instance With a Public IPv4 Address",
        "CSPM",
        "AWS",
        "CSPM-AWS-2024-0027",
        "Creates an isolated-VPC EC2 instance whose public IPv4 address triggers the CSPM rule.",
    ),
    Scenario(
        "cspm-aws-ec2-open-public",
        "EC2 Open to All TCP Ports",
        "CSPM",
        "AWS",
        "CSPM-AWS-2024-0029",
        "Creates a security group permitting inbound TCP ports 0-65535 from the internet.",
    ),
    Scenario(
        "cspm-aws-ec2-imds-v1-enabled",
        "EC2 With IMDSv1 Enabled",
        "CSPM",
        "AWS",
        "CSPM-AWS-2024-0152",
        "Creates an EC2 instance with IMDSv1 permitted through optional metadata tokens.",
    ),
    Scenario(
        "cspm-aws-ec2-ami-public-volume",
        "Public EC2 AMI",
        "CSPM",
        "AWS",
        "CSPM-AWS-2024-0018",
        "Creates a private source instance, an AMI, and a public AMI launch permission.",
    ),
    Scenario(
        "cspm-aws-ec2-public-ssh",
        "Security Group With Public SSH",
        "CSPM",
        "AWS",
        "CSPM-AWS-2024-0033-08",
        "Creates a security group permitting inbound SSH from the internet.",
    ),
    Scenario(
        "cspm-aws-ebs-unencrypted-volume",
        "Unencrypted EBS Volume",
        "CSPM",
        "AWS",
        "CSPM-AWS-2024-0023",
        "Creates an unencrypted EBS volume.",
    ),
    Scenario("cspm-aws-vpc-default-security-group-non-empty", "Non-Empty Default Security Group", "CSPM", "AWS", "CSPM-AWS-2024-0020", "Creates a VPC with a non-empty default security group."),
    Scenario("cspm-aws-security-group-public-icmp", "Public ICMP Security Group", "CSPM", "AWS", "CSPM-AWS-2024-0032", "Creates a security group that permits all public ICMP traffic."),
    Scenario("cspm-aws-security-group-public-mysql", "Public MySQL Security Group", "CSPM", "AWS", "CSPM-AWS-2024-0033-01", "Creates a security group exposing MySQL to the internet."),
    Scenario("cspm-aws-security-group-public-dns", "Public DNS Security Group", "CSPM", "AWS", "CSPM-AWS-2024-0033-02", "Creates a security group exposing DNS over TCP to the internet."),
    Scenario("cspm-aws-security-group-public-mongodb", "Public MongoDB Security Group", "CSPM", "AWS", "CSPM-AWS-2024-0033-03", "Creates a security group exposing MongoDB to the internet."),
    Scenario("cspm-aws-security-group-public-mssql", "Public Microsoft SQL Server Security Group", "CSPM", "AWS", "CSPM-AWS-2024-0033-04", "Creates a security group exposing Microsoft SQL Server to the internet."),
    Scenario("cspm-aws-security-group-public-oracle", "Public Oracle Database Security Group", "CSPM", "AWS", "CSPM-AWS-2024-0033-05", "Creates a security group exposing Oracle Database to the internet."),
    Scenario("cspm-aws-security-group-public-postgres", "Public PostgreSQL Security Group", "CSPM", "AWS", "CSPM-AWS-2024-0033-06", "Creates a security group exposing PostgreSQL to the internet."),
    Scenario("cspm-aws-security-group-public-rdp", "Public RDP Security Group", "CSPM", "AWS", "CSPM-AWS-2024-0033-07", "Creates a security group exposing RDP to the internet."),
    Scenario("cspm-aws-security-group-public-nfs", "Public NFS Security Group", "CSPM", "AWS", "CSPM-AWS-2024-0033-09", "Creates a security group exposing NFS to the internet."),
    Scenario("cspm-aws-security-group-public-smtp", "Public SMTP Security Group", "CSPM", "AWS", "CSPM-AWS-2024-0033-10", "Creates a security group exposing SMTP to the internet."),
    Scenario("cspm-aws-security-group-ftp", "FTP Security Group", "CSPM", "AWS", "CSPM-AWS-2024-0034-01", "Creates a security group allowing FTP ingress."),
    Scenario("cspm-aws-security-group-telnet", "Telnet Security Group", "CSPM", "AWS", "CSPM-AWS-2024-0034-02", "Creates a security group allowing Telnet ingress."),
    Scenario("cspm-aws-security-group-broad-port-range", "Broad Port Range Security Group", "CSPM", "AWS", "CSPM-AWS-2024-0035", "Creates a security group allowing a broad TCP port range."),
    Scenario("cspm-aws-rds-publicly-accessible", "Publicly Accessible RDS Instance", "CSPM", "AWS", "CSPM-AWS-2024-0110", "Creates a publicly accessible PostgreSQL RDS instance."),
    Scenario("cspm-aws-s3-public-access-block-disabled", "S3 Public Access Block Disabled", "CSPM", "AWS", "CSPM-AWS-2024-0164", "Creates a bucket with public-access-block settings disabled."),
    Scenario("cspm-aws-security-group-unrestricted-egress", "Unrestricted Security Group Egress", "CSPM", "AWS", "CSPM-AWS-2024-0476", "Creates a security group with unrestricted IPv4 egress."),
    Scenario("cspm-aws-s3-http-allowed", "S3 Bucket Allowing HTTP", "CSPM", "AWS", "CSPM-AWS-2024-0126", "Creates a bucket policy allowing clear-text HTTP object reads."),
    Scenario("cspm-aws-s3-access-logging-disabled", "S3 Access Logging Disabled", "CSPM", "AWS", "CSPM-AWS-2024-0128", "Creates a bucket without server-access logging."),
    Scenario("cspm-aws-s3-versioning-disabled", "S3 Versioning Disabled", "CSPM", "AWS", "CSPM-AWS-2024-0130", "Creates a bucket without versioning enabled."),
    Scenario("cspm-aws-s3-public-delete", "S3 Public Delete Permission", "CSPM", "AWS", "CSPM-AWS-2024-0132", "Creates a bucket policy allowing everyone to delete objects."),
    Scenario("cspm-aws-s3-public-all-actions", "S3 Public All-Actions Permission", "CSPM", "AWS", "CSPM-AWS-2024-0133", "Creates a bucket policy allowing everyone all S3 actions."),
    Scenario("cspm-aws-s3-public-access-block-disabled-0165", "S3 Public Access Block Disabled", "CSPM", "AWS", "CSPM-AWS-2024-0165", "Creates a bucket with all bucket-level public-access-block settings disabled."),
    Scenario("cspm-aws-s3-no-kms-encryption", "S3 Bucket Without KMS Encryption", "CSPM", "AWS", "CSPM-AWS-2024-0368", "Creates a bucket without AWS KMS default encryption."),
    Scenario("cspm-aws-s3-website-hosting-enabled", "S3 Website Hosting Enabled", "CSPM", "AWS", "CSPM-AWS-2024-0490", "Creates a bucket with website hosting enabled."),
    Scenario("cspm-aws-s3-public-read", "S3 Public Read Permission", "CSPM", "AWS", "CSPM-AWS-2024-0609", "Creates a bucket policy allowing everyone to read objects."),
    Scenario("cspm-aws-s3-public-write", "S3 Public Write Permission", "CSPM", "AWS", "CSPM-AWS-2024-0610", "Creates a bucket policy allowing everyone to write objects."),
    Scenario("cspm-aws-s3-public-get", "S3 Public GetObject Permission", "CSPM", "AWS", "CSPM-AWS-2024-0616", "Creates a bucket policy authorizing GetObject for all principals."),
    Scenario("cspm-aws-s3-public-list", "S3 Public ListBucket Permission", "CSPM", "AWS", "CSPM-AWS-2024-0617", "Creates a bucket policy authorizing ListBucket for all principals."),
    Scenario("ciem-aws-iam-user-excessive-permissions", "IAM User With Excessive Permissions", "CIEM", "AWS", "CIEM-AWS-2024-0002", "Creates an IAM user with an inline administrator-style policy."),
    Scenario("ciem-aws-iam-empty-group", "IAM Group Without Users", "CIEM", "AWS", "CIEM-AWS-2024-0003", "Creates an IAM group without assigned users."),
    Scenario("ciem-aws-iam-group-excessive-permissions", "IAM Group With Excessive Permissions", "CIEM", "AWS", "CIEM-AWS-2024-0004", "Creates an IAM group with an inline administrator-style policy."),
    Scenario("ciem-aws-iam-unattached-managed-policy", "Unattached IAM Managed Policy", "CIEM", "AWS", "CIEM-AWS-2024-0005", "Creates an unattached customer-managed IAM policy."),
    Scenario("ciem-aws-iam-overly-permissive-managed-policy", "Overly Permissive IAM Managed Policy", "CIEM", "AWS", "CIEM-AWS-2024-0006", "Creates a customer-managed IAM policy granting all actions on all resources."),
    Scenario("ciem-aws-iam-role-excessive-permissions", "IAM Role With Excessive Permissions", "CIEM", "AWS", "CIEM-AWS-2024-0008", "Creates an IAM role with an inline administrator-style policy."),
    Scenario("ciem-aws-iam-role-overly-permissive-inline-policy", "Overly Permissive IAM Role Inline Policy", "CIEM", "AWS", "CIEM-AWS-2024-0009", "Creates a role inline policy granting all actions on all resources."),
    Scenario("ciem-aws-iam-user-overly-permissive-inline-policy", "Overly Permissive IAM User Inline Policy", "CIEM", "AWS", "CIEM-AWS-2024-0010", "Creates a user inline policy granting all actions on all resources."),
    Scenario("ciem-aws-iam-group-overly-permissive-inline-policy", "Overly Permissive IAM Group Inline Policy", "CIEM", "AWS", "CIEM-AWS-2024-0011", "Creates a group inline policy granting all actions on all resources."),
    Scenario("cspm-aws-rds-backup-disabled", "RDS Automated Backups Disabled", "CSPM", "AWS", "CSPM-AWS-2024-0107", "Creates an RDS instance with backup retention set to zero."),
    Scenario("cspm-aws-rds-auto-minor-upgrade-disabled", "RDS Auto Minor Upgrade Disabled", "CSPM", "AWS", "CSPM-AWS-2024-0109", "Creates an RDS instance with automatic minor version upgrades disabled."),
    Scenario("cspm-aws-rds-short-backup-retention", "RDS Short Backup Retention", "CSPM", "AWS", "CSPM-AWS-2024-0111", "Creates an RDS instance with one day of backup retention."),
    Scenario("cspm-aws-rds-single-az", "RDS Single-AZ Instance", "CSPM", "AWS", "CSPM-AWS-2024-0112", "Creates a single-AZ RDS instance."),
    Scenario("cspm-aws-rds-storage-unencrypted", "RDS Storage Encryption Disabled", "CSPM", "AWS", "CSPM-AWS-2024-0113", "Creates an RDS instance with storage encryption disabled."),
    Scenario("cspm-aws-rds-iam-auth-disabled", "RDS IAM Database Authentication Disabled", "CSPM", "AWS", "CSPM-AWS-2024-0333", "Creates an RDS instance without IAM database authentication."),
    Scenario("cspm-aws-rds-multiaz-disabled", "RDS Multi-AZ Disabled", "CSPM", "AWS", "CSPM-AWS-2024-0336-01", "Creates a single-AZ RDS instance."),
    Scenario("cspm-aws-rds-copy-tags-to-snapshot-disabled", "RDS Copy Tags to Snapshots Disabled", "CSPM", "AWS", "CSPM-AWS-2024-0338", "Creates an RDS instance that does not copy tags to snapshots."),
    Scenario("cspm-aws-rds-default-port", "RDS Default Database Port", "CSPM", "AWS", "CSPM-AWS-2024-0344", "Creates a PostgreSQL RDS instance on port 5432."),
    Scenario("cspm-aws-rds-default-admin-username", "RDS Default Administrator Username", "CSPM", "AWS", "CSPM-AWS-2024-0346", "Creates an RDS instance using admin as its master username."),
    Scenario("cspm-aws-rds-cluster-iam-auth-disabled", "RDS Cluster IAM Authentication Disabled", "CSPM", "AWS", "CSPM-AWS-2024-0334", "Creates an Aurora cluster without IAM database authentication."),
    Scenario("cspm-aws-rds-cluster-copy-tags-disabled", "RDS Cluster Copy Tags Disabled", "CSPM", "AWS", "CSPM-AWS-2024-0337", "Creates an Aurora cluster that does not copy tags to snapshots."),
    Scenario("cspm-aws-rds-cluster-default-admin-username", "RDS Cluster Default Administrator Username", "CSPM", "AWS", "CSPM-AWS-2024-0345", "Creates an Aurora cluster using admin as its master username."),
    Scenario("cspm-aws-rds-cluster-storage-unencrypted", "RDS Cluster Storage Encryption Disabled", "CSPM", "AWS", "CSPM-AWS-2024-0348", "Creates an Aurora cluster with storage encryption disabled."),
    Scenario("cspm-aws-rds-aurora-audit-logs-disabled", "Aurora MySQL Audit Logs Disabled", "CSPM", "AWS", "CSPM-AWS-2024-0350", "Creates an Aurora MySQL cluster without audit log exports."),
    Scenario("cspm-aws-rds-cluster-auto-minor-upgrade-disabled", "RDS Cluster Auto Minor Upgrade Disabled", "CSPM", "AWS", "CSPM-AWS-2024-0351", "Creates an Aurora cluster with auto minor version upgrade disabled."),
    Scenario("cspm-aws-rds-cluster-deletion-protection-disabled", "RDS Cluster Deletion Protection Disabled", "CSPM", "AWS", "CSPM-AWS-2024-0354", "Creates an Aurora cluster with deletion protection disabled."),
    Scenario("cspm-aws-rds-backup-plan-missing", "RDS Backup Plan Missing", "CSPM", "AWS", "CSPM-AWS-2024-0347", "Creates an RDS instance with backup retention set to zero."),
    Scenario("cspm-aws-rds-encryption-at-rest-disabled", "RDS Encryption at Rest Disabled", "CSPM", "AWS", "CSPM-AWS-2024-0349", "Creates an RDS instance with storage encryption disabled."),
    Scenario("cspm-aws-rds-enhanced-monitoring-disabled", "RDS Enhanced Monitoring Disabled", "CSPM", "AWS", "CSPM-AWS-2024-0353", "Creates an RDS instance with enhanced monitoring disabled."),
    Scenario("cspm-aws-rds-deletion-protection-disabled", "RDS Deletion Protection Disabled", "CSPM", "AWS", "CSPM-AWS-2024-0355", "Creates an RDS instance with deletion protection disabled."),
    Scenario("cspm-aws-rds-cloudwatch-logs-disabled", "RDS CloudWatch Logs Disabled", "CSPM", "AWS", "CSPM-AWS-2024-0356", "Creates a PostgreSQL RDS instance without CloudWatch log exports."),
    Scenario("cspm-aws-vpc-flow-logs-disabled", "VPC Flow Logs Disabled", "CSPM", "AWS", "CSPM-AWS-2024-0167", "Creates a VPC without a VPC Flow Log."),
    Scenario("cspm-aws-transit-gateway-auto-accept-enabled", "Transit Gateway Auto-Accept Enabled", "CSPM", "AWS", "CSPM-AWS-2024-0231", "Creates a Transit Gateway that accepts shared attachments automatically."),
    Scenario("cspm-aws-vpc-endpoint-public-policy", "VPC Endpoint Public Policy", "CSPM", "AWS", "CSPM-AWS-2024-0488", "Creates an S3 gateway VPC endpoint with a public policy."),
    Scenario("cspm-aws-vpc-invalid-name", "VPC Invalid Name", "CSPM", "AWS", "CSPM-AWS-2024-0580", "Creates a VPC with a Name tag outside the expected convention."),
    Scenario("cspm-aws-lambda-public-invoke", "Lambda Public Invoke Policy", "CSPM", "AWS", "CSPM-AWS-2024-0294", "Creates a Lambda resource policy allowing public invocation."),
    Scenario("cspm-aws-lambda-outside-vpc", "Lambda Outside VPC", "CSPM", "AWS", "CSPM-AWS-2024-0296", "Creates a Lambda function without VPC configuration."),
    Scenario("cspm-aws-lambda-single-subnet", "Lambda Single-Subnet VPC", "CSPM", "AWS", "CSPM-AWS-2024-0297", "Creates a VPC Lambda function using only one subnet."),
    Scenario("cspm-aws-lambda-environment-no-kms", "Lambda Environment Variables Without Customer KMS", "CSPM", "AWS", "CSPM-AWS-2024-0444", "Creates environment variables without a customer-managed KMS key."),
    Scenario("cspm-aws-lambda-no-customer-kms", "Lambda Without Customer KMS", "CSPM", "AWS", "CSPM-AWS-2024-0445", "Creates a Lambda function without a customer-managed KMS key."),
    Scenario("cspm-aws-lambda-unapproved-runtime", "Lambda Unapproved Runtime", "CSPM", "AWS", "CSPM-AWS-2024-0295", "Creates a Lambda using a runtime absent from the rule's approved list."),
    Scenario("cspm-aws-lambda-url-no-auth", "Lambda Function URL Without IAM Authentication", "CSPM", "AWS", "CSPM-AWS-2024-0446", "Creates a Lambda Function URL with NONE authorization."),
    Scenario("cspm-aws-lambda-public-admin-policy", "Lambda Public Administrative Policy", "CSPM", "AWS", "CSPM-AWS-2024-0546", "Creates a Lambda resource policy granting lambda:* to every principal."),
    Scenario("cspm-aws-lambda-url-enabled", "Lambda Function URL Enabled", "CSPM", "AWS", "CSPM-AWS-2024-0547", "Creates a Lambda Function URL."),
    Scenario("cspm-azure-storage-https-disabled", "Azure Storage HTTPS Disabled", "CSPM", "Azure", "CSPM-AZURE-2024-0071", "Creates a storage account without HTTPS-only transfer."),
    Scenario("cspm-azure-storage-no-cmk", "Azure Storage Without Customer-Managed Key", "CSPM", "Azure", "CSPM-AZURE-2024-0072", "Creates a storage account without a customer-managed encryption key."),
    Scenario("cspm-azure-storage-public-container", "Azure Storage Public Blob Container", "CSPM", "Azure", "CSPM-AZURE-2024-0073", "Creates a public blob container."),
    Scenario("cspm-azure-storage-public-access", "Azure Storage Public Access Enabled", "CSPM", "Azure", "CSPM-AZURE-2024-0074", "Creates a storage account permitting public blob access."),
    Scenario("cspm-azure-storage-soft-delete-disabled", "Azure Storage Soft Delete Disabled", "CSPM", "Azure", "CSPM-AZURE-2024-0075", "Creates a storage account without blob soft delete retention."),
    Scenario("cspm-azure-storage-trusted-services-disabled", "Azure Storage Trusted Services Bypass Disabled", "CSPM", "Azure", "CSPM-AZURE-2024-0076", "Creates storage network rules without trusted-services bypass."),
    Scenario("cspm-azure-storage-infrastructure-encryption-disabled", "Azure Storage Infrastructure Encryption Disabled", "CSPM", "Azure", "CSPM-AZURE-2024-0131", "Creates a storage account without infrastructure encryption."),
    Scenario("cspm-azure-storage-network-default-allow", "Azure Storage Network Default Allow", "CSPM", "Azure", "CSPM-AZURE-2024-0136", "Creates storage network rules with default access allowed."),
    Scenario("cspm-azure-storage-tls-1-0", "Azure Storage TLS 1.0 Allowed", "CSPM", "Azure", "CSPM-AZURE-2024-0141", "Creates a storage account allowing TLS 1.0."),
    Scenario("cspm-azure-storage-cross-tenant-replication", "Azure Storage Cross-Tenant Replication Enabled", "CSPM", "Azure", "CSPM-AZURE-2024-0142", "Creates a storage account allowing cross-tenant replication."),
    Scenario("cspm-azure-storage-key-expiration-policy-missing", "Azure Storage Key Expiration Policy Missing", "CSPM", "Azure", "CSPM-AZURE-2024-0132", "Creates a storage account without a key-expiration policy."),
    Scenario("cspm-azure-storage-queue-logging-disabled", "Azure Storage Queue Logging Disabled", "CSPM", "Azure", "CSPM-AZURE-2024-0134", "Creates a storage account without Queue service logging."),
    Scenario("cspm-azure-storage-critical-data-no-cmk", "Azure Storage Critical Data Without CMK", "CSPM", "Azure", "CSPM-AZURE-2024-0138", "Creates storage without customer-managed encryption keys."),
    Scenario("cspm-azure-storage-public-access-disallowed", "Azure Storage Public Access Allowed", "CSPM", "Azure", "CSPM-AZURE-2024-0260", "Creates a storage account permitting public access."),
    Scenario("cspm-azure-storage-network-unrestricted", "Azure Storage Network Unrestricted", "CSPM", "Azure", "CSPM-AZURE-2024-0303", "Creates a storage account without restricted network access."),
    Scenario("cspm-azure-storage-no-vnet-rules", "Azure Storage No VNet Rules", "CSPM", "Azure", "CSPM-AZURE-2024-0304", "Creates a storage account without virtual network rules."),
    Scenario("cspm-azure-storage-geo-redundancy-disabled", "Azure Storage Geo Redundancy Disabled", "CSPM", "Azure", "CSPM-AZURE-2024-0531", "Creates locally redundant rather than geo-redundant storage."),
    Scenario("cspm-azure-storage-secure-transfer-disabled", "Azure Storage Secure Transfer Disabled", "CSPM", "Azure", "CSPM-AZURE-2024-0792", "Creates a storage account without secure-transfer enforcement."),
    Scenario("cspm-azure-storage-customer-key-missing", "Azure Storage Customer Key Missing", "CSPM", "Azure", "CSPM-AZURE-2024-0833", "Creates storage without a customer-managed encryption key."),
    Scenario("cspm-azure-storage-infrastructure-encryption-missing", "Azure Storage Infrastructure Encryption Missing", "CSPM", "Azure", "CSPM-AZURE-2024-0858", "Creates a storage account without infrastructure encryption."),
    Scenario("cspm-azure-nsg-all-inbound", "Azure NSG All Inbound", "CSPM", "Azure", "CSPM-AZURE-2024-0025", "Creates an NSG allowing all inbound traffic."),
    Scenario("cspm-azure-nsg-public-mssql", "Azure NSG Public MSSQL", "CSPM", "Azure", "CSPM-AZURE-2024-0026", "Creates an NSG allowing public Microsoft SQL Server access."),
    Scenario("cspm-azure-nsg-public-udp", "Azure NSG Public UDP", "CSPM", "Azure", "CSPM-AZURE-2024-0027", "Creates an NSG allowing public UDP traffic."),
    Scenario("cspm-azure-nsg-public-ssh", "Azure NSG Public SSH", "CSPM", "Azure", "CSPM-AZURE-2024-0028", "Creates an NSG allowing public SSH access."),
    Scenario("cspm-azure-nsg-unrestricted-ports", "Azure NSG Unrestricted Ports", "CSPM", "Azure", "CSPM-AZURE-2024-0261", "Creates an NSG with unrestricted inbound ports."),
    Scenario("cspm-azure-vm-disk-platform-key", "Azure VM Disk Platform-Key Encryption", "CSPM", "Azure", "CSPM-AZURE-2024-0080", "Creates a managed disk using platform-managed encryption."),
    Scenario("cspm-azure-vm-unattached-disk-platform-key", "Azure VM Unattached Disk Platform-Key Encryption", "CSPM", "Azure", "CSPM-AZURE-2024-0081", "Creates an unattached platform-key encrypted disk."),
    Scenario("cspm-azure-vm-disk-no-cmk", "Azure VM Disk Without CMK", "CSPM", "Azure", "CSPM-AZURE-2024-0173", "Creates a managed disk without a customer-managed key."),
    Scenario("cspm-azure-vm-disk-no-double-encryption", "Azure VM Disk Without Double Encryption", "CSPM", "Azure", "CSPM-AZURE-2024-0824", "Creates a managed disk without double encryption."),
    Scenario("cspm-azure-vm-unattached-disk", "Azure VM Unattached Disk", "CSPM", "Azure", "CSPM-AZURE-2024-1074", "Creates an unattached managed disk."),
    Scenario("cspm-azure-sql-public-firewall", "Azure SQL Public Firewall", "CSPM", "Azure", "CSPM-AZURE-2024-0050", "Creates an Azure SQL firewall rule allowing all IPv4 addresses."),
    Scenario("cspm-azure-sql-short-auditing-retention", "Azure SQL Short Auditing Retention", "CSPM", "Azure", "CSPM-AZURE-2024-0051", "Creates an Azure SQL database without adequate auditing retention."),
    Scenario("cspm-azure-sql-auditing-disabled", "Azure SQL Auditing Disabled", "CSPM", "Azure", "CSPM-AZURE-2024-0052", "Creates an Azure SQL database with auditing disabled."),
    Scenario("cspm-azure-sql-threat-detection-disabled", "Azure SQL Threat Detection Disabled", "CSPM", "Azure", "CSPM-AZURE-2024-0053", "Creates an Azure SQL database without threat detection."),
    Scenario("cspm-azure-sql-threat-alerts-disabled", "Azure SQL Threat Alerts Disabled", "CSPM", "Azure", "CSPM-AZURE-2024-0055", "Creates an Azure SQL database without threat detection alerts."),
    Scenario("cspm-azure-sql-threat-retention-short", "Azure SQL Threat Retention Short", "CSPM", "Azure", "CSPM-AZURE-2024-0056", "Creates an Azure SQL database without adequate threat retention."),
    Scenario("cspm-azure-sql-threat-email-disabled", "Azure SQL Threat Email Alerts Disabled", "CSPM", "Azure", "CSPM-AZURE-2024-0057", "Creates an Azure SQL database without threat detection email alerts."),
    Scenario("cspm-azure-sql-entra-admin-missing", "Azure SQL Entra Administrator Missing", "CSPM", "Azure", "CSPM-AZURE-2024-0059", "Creates an Azure SQL server without an Entra administrator."),
    Scenario("cspm-azure-sql-basic-sku", "Azure SQL Basic SKU", "CSPM", "Azure", "CSPM-AZURE-2024-0167-04", "Creates an Azure SQL database using the Basic SKU."),
    Scenario("cspm-azure-sql-public-network", "Azure SQL Public Network Enabled", "CSPM", "Azure", "CSPM-AZURE-2024-0299", "Creates an Azure SQL server with public network access enabled."),
    Scenario("ciem-azure-excessive-rbac-role", "Azure Excessive RBAC Role", "CIEM", "Azure", "CIEM-AZURE-2024-0007", "Creates a custom Azure RBAC role granting all actions to the current principal."),
)


def find_scenario(scenario_id: str) -> Scenario:
    for scenario in SCENARIOS:
        if scenario.scenario_id == scenario_id:
            return scenario
    raise ValueError(f"Unknown scenario: {scenario_id}. Run 'list --module CSPM' or 'list --module CIEM' to see available scenarios.")
