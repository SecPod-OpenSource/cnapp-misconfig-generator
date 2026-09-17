# Cloud Security Misconfiguration Scenarios

A Python CLI and reviewed Terraform fixtures for creating reproducible CSPM and
CIEM test scenarios in **dedicated, disposable AWS or Azure subscriptions**.
Use it to validate cloud-security detections, alerting, and remediation
workflows without relying on production resources.

> [!WARNING]
> These scenarios intentionally weaken security controls and can create
> publicly accessible resources or excessive permissions. Never use them in a
> production account or subscription. Review the Terraform plan, use a
> disposable environment, and destroy every deployment when testing is done.
>
> 
## Use cases

This repository provides repeatable Terraform scenarios that intentionally model cloud-security misconfigurations. Use them only in approved, disposable cloud environments.

- **Validate CSPM and CIEM tooling:** confirm that security platforms identify known configuration and identity risks.
- **Test detection rules:** verify that new or updated rules detect the intended resources before release.
- **Run regression and integration tests:** check that findings, alerts, ticketing, SIEM ingestion, and remediation workflows continue to work after changes.
- **Build security labs and demonstrations:** create temporary, realistic examples for hands-on training, product demos, and control validation.
- **Support compliance testing:** exercise controls for public exposure, insecure transport, weak encryption settings, and overly broad permissions.


## Safety model

- Every Terraform resource is inert until the CLI passes
  `allow_unsafe_apply=true`.
- Cloud-changing commands require the explicit `--apply` acknowledgement.
- AWS deployments verify the supplied account ID with AWS STS before each
  provision or destroy operation.
- Azure deployments verify the supplied subscription ID with Azure CLI before
  each provision or destroy operation.
- Terraform state and provider files are created under `deployments/`, never in
  the reusable fixture source.

## Prerequisites

- Python 3.10 or later
- Terraform on `PATH`
- For AWS scenarios: AWS CLI authenticated to a dedicated test account
- For Azure scenarios: Azure CLI authenticated to a dedicated test subscription

No third-party Python packages are required.

## Quick start

Run these commands from the repository root.

```powershell
python -m src.cli scenario-list --module CSPM --provider AWS
python -m src.cli scenario-list --module CSPM --provider AZURE
python -m src.cli describe cspm-aws-ec2-public-ip
```

Provision and clean up an AWS scenario:

```powershell
python -m src.cli provision cspm-aws-ec2-public-ip --region ap-south-1 --expected-account-id 123456789012 --apply
python -m src.cli destroy cspm-aws-ec2-public-ip --region ap-south-1 --expected-account-id 123456789012 --apply
```

Provision and clean up an Azure scenario:

```powershell
az login
python -m src.cli provision ciem-azure-excessive-rbac-role --location centralindia --expected-subscription-id <subscription-id> --apply
python -m src.cli destroy ciem-azure-excessive-rbac-role --location centralindia --expected-subscription-id <subscription-id> --apply
```

Replace all account and subscription placeholders with the dedicated test
environment you intend to use. Some scenarios create billable resources.

## Validate

```powershell
python -m unittest discover -s tests -v
```

## Project layout

- `src/` - CLI and scenario catalog
- `terraform_scenarios/rules/` - self-contained, static Terraform fixtures
- `tests/` - unit tests
- `docs/ARCHITECTURE.md` - lifecycle, commands, and design notes
- `docs/USAGE.md` - sequential setup, provision, validation, and cleanup guide

Fixtures may also live in a separate checkout; use the global
`--scenarios-root <path-to-rules>` option to point the CLI at it.

For the complete prerequisite checks and cloud-specific command sequence, see
[the usage guide](docs/USAGE.md).

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md) for development and pull-request
guidance. Report vulnerabilities privately as described in
[SECURITY.md](SECURITY.md); do not open public issues for them.

## License

This project is licensed under the [Apache License 2.0](LICENSE).
