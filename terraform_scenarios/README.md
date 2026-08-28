# AWS CSPM Terraform Scenarios

This directory is a static Terraform fixture repository. Each subdirectory of
`rules/` is self-contained and contains only Terraform and scenario documentation.
It deliberately contains no CSPM feed JSON.

The `terraform_misconfig_generator` CLI can use this directory directly or use
another checkout of it through `--scenarios-root`.

Do not run Terraform in this repository directly for normal testing. The CLI
copies the selected fixture into a deployment workspace so Terraform state and
provider artifacts remain separate from the reusable scenario source.
