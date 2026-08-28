# Contributing

Thanks for improving the project.

## Before opening a pull request

- Keep fixtures self-contained and place each scenario in its own
  `terraform_scenarios/rules/<rule-id>/` directory.
- Include a `README.md` beside every fixture that clearly states the
  misconfiguration it creates and its operational risk.
- Preserve the `allow_unsafe_apply` guard. Do not add resources that can be
  created without explicit acknowledgement.
- Do not commit Terraform state, provider directories, cloud credentials,
  account IDs, or subscription IDs.
- Update the scenario catalog and tests when adding or removing a fixture.

## Local validation

Run the test suite from the repository root:

```powershell
python -m unittest discover -s tests -v
```

For changed Terraform fixtures, run `terraform fmt -check -recursive terraform_scenarios`
and inspect the generated plan only in a disposable cloud
environment.

## Pull requests

Explain the scenario, its intended detection, cloud-provider impact, and the
cleanup command. Pull requests that create intentionally insecure resources
must include a safety review by a maintainer.
