# Usage guide

This guide provides the safe, sequential workflow for one scenario at a time. It creates intentional misconfigurations, so use only a disposable AWS account or Azure subscription.

> [!CAUTION]
> `provision --apply` runs `terraform apply -auto-approve` after safety checks. It may create publicly accessible, excessively privileged, and billable resources. Verify the target environment and always clean up.


## Use cases

This repository provides repeatable Terraform scenarios that intentionally model cloud-security misconfigurations. Use them only in approved, disposable cloud environments.

- **Validate CSPM and CIEM tooling:** confirm that security platforms identify known configuration and identity risks.
- **Test detection rules:** verify that new or updated rules detect the intended resources before release.
- **Run regression and integration tests:** check that findings, alerts, ticketing, SIEM ingestion, and remediation workflows continue to work after changes.
- **Build security labs and demonstrations:** create temporary, realistic examples for hands-on training, product demos, and control validation.
- **Support compliance testing:** exercise controls for public exposure, insecure transport, weak encryption settings, and overly broad permissions.


## 1. Prerequisites

Install Python 3.10+, Terraform

Install the cloud CLI for the scenario you will run: AWS CLI for AWS or Azure CLI for Azure. 

Open a new PowerShell terminal, change to the repository root, and run:

```powershell
python --version
terraform version
python -m unittest discover -s tests -v
```

Do not run Terraform directly inside `terraform_scenarios/rules`. The CLI copies the selected fixture to `deployments/` and runs Terraform from that workspace.

## 2. Select a scenario

List scenarios and inspect one before provisioning it:

```powershell
python -m src.cli scenario-list --module CSPM --provider AWS
python -m src.cli scenario-list --module CSPM --provider AZURE
python -m src.cli scenario-list --module CIEM --provider AWS
python -m src.cli scenario-list --module CIEM --provider AZURE
python -m src.cli describe cspm-aws-ec2-public-ip
python -m src.cli describe ciem-azure-excessive-rbac-role
```

The `STATUS` column reads local Terraform state from `deployments/`. Do not provision a scenario marked `deployed` unless you intend to reuse its workspace.

## 3. AWS lifecycle

Authenticate using the organization-approved method. 

Run "aws confiugre" command on the AWS CLI and set the keys correctly

OR

If you use a named profile, set it in the current terminal and verify the disposable account:

```powershell
$env:AWS_PROFILE = "your-disposable-test-profile"
aws sts get-caller-identity --query Account --output text --region ap-south-1
$awsAccountId = "123456789012"
```

The returned ID must be the same as `$awsAccountId`. Provision one scenario:

```powershell
python -m src.cli provision cspm-aws-ec2-public-ip --region ap-south-1 --expected-account-id $awsAccountId --apply
```

The CLI verifies the account, copies the fixture, then runs Terraform init, plan, and apply. After your security tool collects the finding, destroy the same scenario from the same checkout:

```powershell
python -m src.cli destroy cspm-aws-ec2-public-ip --region ap-south-1 --expected-account-id $awsAccountId --apply
python -m src.cli scenario-list --module CSPM --provider AWS
```

RDS and Aurora scenarios need a unique disposable database password in the current session:

```powershell
$env:TF_VAR_db_password = "<unique-test-password>"
```

Some EC2 scenarios outside `us-east-1` require an approved `--ami-id` and `--availability-zone`; follow the CLI error when either is required.

## 4. Azure lifecycle

Sign in and explicitly set the disposable subscription:

```powershell
az login
$azureSubscriptionId = "00000000-0000-0000-0000-000000000000"
az account set --subscription $azureSubscriptionId
az account show --query id --output tsv
```

The final command must print exactly `$azureSubscriptionId`. Provision only after confirming it:

```powershell
python -m src.cli provision ciem-azure-excessive-rbac-role --location centralindia --expected-subscription-id $azureSubscriptionId --apply
```

After your security platform collects the result, destroy it with the same subscription and location:

```powershell
python -m src.cli destroy ciem-azure-excessive-rbac-role --location centralindia --expected-subscription-id $azureSubscriptionId --apply
python -m src.cli scenario-list --module CIEM --provider AZURE
```

The signed-in Azure identity must have the permissions required by the chosen scenario.

## 5. Batch commands

Batch provisioning is sequential and stops at the first failure. Use it only after a single-scenario test succeeds, and keep AWS and Azure operations separate.

```powershell
python -m src.cli provision-batch --module CIEM --service IAM --region ap-south-1 --expected-account-id $awsAccountId --apply
python -m src.cli destroy-batch --module CIEM --service IAM --region ap-south-1 --expected-account-id $awsAccountId --apply
```

## 6. Troubleshooting

| Symptom | Resolution |
| --- | --- |
| Terraform is not on `PATH` | Install Terraform, restart PowerShell, and run `terraform version`. |
| AWS account mismatch | Re-run `aws sts get-caller-identity` and use its account ID only if it is your disposable account. |
| Azure subscription mismatch | Run `az login`, `az account set --subscription <id>`, then `az account show --query id --output tsv`. |
| Azure CLI cannot launch on Windows | Install Azure CLI, open a new terminal, and verify `az --version`. |
| Terraform apply fails | Inspect the deployment-workspace error. Typical causes are missing permissions, policy restrictions, quotas, or unavailable regions. |
| Scenario still shows `deployed` | Run its matching `destroy --apply` command. Do not delete Terraform state to avoid cleanup. |

## 7. Use fixtures from another checkout

By default, the CLI reads `terraform_scenarios/rules` in this repository. To use an external fixture checkout, supply its `rules` directory before the CLI command and use the same value for provision and destroy:

```powershell
python -m src.cli --scenarios-root C:\Repos\cloud-security-terraform-scenarios\rules scenario-list --module CSPM
```
