from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
from typing import Iterable

from .scenarios import SCENARIOS, Scenario, find_scenario

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS_ROOT = PROJECT_ROOT / "terraform_scenarios" / "rules"


def fixture_source(scenarios_root: Path, rule_id: str) -> Path:
    source = scenarios_root / rule_id
    if not (source / "main.tf").is_file():
        raise ValueError(f"Static Terraform fixture was not found: {source}")
    return source


def generate(scenarios_root: Path, output: Path, rule_id: str) -> Path:
    """Copy a prebuilt fixture; no CSPM feed is read at runtime."""
    source = fixture_source(scenarios_root, rule_id)
    destination = output / rule_id
    destination.mkdir(parents=True, exist_ok=True)
    for file in source.iterdir():
        if file.is_file():
            shutil.copy2(file, destination / file.name)
    return destination


def command_list(scenarios_root: Path) -> int:
    for fixture in sorted(scenarios_root.iterdir()):
        if fixture.is_dir() and (fixture / "main.tf").is_file():
            print(fixture.name)
    return 0


def command_generate_all(scenarios_root: Path, output: Path) -> int:
    for fixture in sorted(scenarios_root.iterdir()):
        if fixture.is_dir() and (fixture / "main.tf").is_file():
            print(generate(scenarios_root, output, fixture.name))
    return 0


def run_command(command: list[str], cwd: Path, capture_output: bool = False) -> subprocess.CompletedProcess[str]:
    executable = shutil.which(command[0])
    # On Windows, CreateProcess cannot directly launch the .cmd wrapper that
    # Azure CLI installs.  PowerShell resolves it transparently, whereas Python
    # subprocess does not, so delegate batch-wrapper resolution to cmd.exe.
    is_azure_cli_batch_wrapper = (
        os.name == "nt"
        and command[0].lower() == "az"
        and executable
        and Path(executable).suffix.lower() in {".bat", ".cmd"}
    )
    return subprocess.run(command, cwd=cwd, check=True, text=True, capture_output=capture_output, shell=is_azure_cli_batch_wrapper)


def verified_account_id(region: str) -> str:
    if shutil.which("aws") is None:
        raise RuntimeError("AWS CLI is required for account confirmation. Install it and configure test-account credentials.")
    try:
        result = run_command(
            ["aws", "sts", "get-caller-identity", "--query", "Account", "--output", "text", "--region", region],
            Path.cwd(),
            capture_output=True,
        )
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or error.stdout or "AWS CLI returned no diagnostic output.").strip()
        raise RuntimeError(
            "Unable to confirm the AWS account. Run `aws sts get-caller-identity --region "
            f"{region}` to check your AWS CLI credentials. AWS CLI error: {detail}"
        ) from None
    return result.stdout.strip()


def verified_subscription_id() -> str:
    if shutil.which("az") is None:
        raise RuntimeError("Azure CLI is required for Azure subscription confirmation. Install it and run `az login`.")
    try:
        result = run_command(["az", "account", "show", "--query", "id", "--output", "tsv"], Path.cwd(), capture_output=True)
    except FileNotFoundError:
        raise RuntimeError("Azure CLI could not be launched. Install Azure CLI, restart the terminal, then run `az login`.") from None
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or error.stdout or "Azure CLI returned no diagnostic output.").strip()
        raise RuntimeError(f"Unable to confirm the Azure subscription. Run `az login` and `az account show`. Azure CLI error: {detail}") from None
    return result.stdout.strip()


def deploy(scenarios_root: Path, rule_id: str, deployment_root: Path, region: str, expected_account_id: str, apply: bool, ami_id: str | None = None, availability_zone: str | None = None) -> Path:
    if not apply:
        raise ValueError("Deployment requires --apply. This prevents an accidental cloud change.")
    if not expected_account_id.isdigit() or len(expected_account_id) != 12:
        raise ValueError("--expected-account-id must be the 12-digit AWS test account ID.")
    if shutil.which("terraform") is None:
        raise RuntimeError("Terraform was not found on PATH.")

    actual_account_id = verified_account_id(region)
    if actual_account_id != expected_account_id:
        raise RuntimeError(f"AWS account mismatch: expected {expected_account_id}, got {actual_account_id}.")

    fixture = generate(scenarios_root, deployment_root, rule_id)
    run_command(["terraform", "init", "-input=false"], fixture)
    variables = ["-var=allow_unsafe_apply=true", f"-var=aws_region={region}"]
    if ami_id:
        variables.append(f"-var=ami_id={ami_id}")
    if availability_zone:
        variables.append(f"-var=availability_zone={availability_zone}")
    run_command(["terraform", "plan", "-input=false", *variables], fixture)
    run_command(["terraform", "apply", "-auto-approve", *variables], fixture)
    return fixture


def deploy_azure(scenarios_root: Path, rule_id: str, deployment_root: Path, location: str, expected_subscription_id: str, apply: bool) -> Path:
    if not apply:
        raise ValueError("Deployment requires --apply. This prevents an accidental cloud change.")
    actual_subscription_id = verified_subscription_id()
    if actual_subscription_id.lower() != expected_subscription_id.lower():
        raise RuntimeError(f"Azure subscription mismatch: expected {expected_subscription_id}, got {actual_subscription_id}.")
    if shutil.which("terraform") is None:
        raise RuntimeError("Terraform was not found on PATH.")
    fixture = generate(scenarios_root, deployment_root, rule_id)
    variables = ["-var=allow_unsafe_apply=true", f"-var=azure_location={location}", f"-var=azure_subscription_id={expected_subscription_id}"]
    run_command(["terraform", "init", "-input=false"], fixture)
    run_command(["terraform", "plan", "-input=false", *variables], fixture)
    run_command(["terraform", "apply", "-auto-approve", *variables], fixture)
    return fixture


def scenario_status(deployment_root: Path, scenario: Scenario) -> str:
    return "deployed" if (deployment_root / scenario.scenario_id / scenario.rule_id / "terraform.tfstate").is_file() else "not-deployed"


def command_scenario_list(module: str | None, deployment_root: Path, service: str | None = None, services: bool = False, provider: str | None = None) -> int:
    matching = [
        scenario for scenario in SCENARIOS
        if (module is None or scenario.module.lower() == module.lower())
        and (service is None or scenario.service.lower() == service.lower())
        and (provider is None or scenario.platform.lower() == provider.lower())
    ]
    if services:
        for service_name in sorted({scenario.service for scenario in matching}):
            print(service_name)
        return 0
    print("SCENARIO ID\tSCENARIO NAME\tPLATFORM\tMODULE\tSERVICE\tSTATUS")
    for scenario in matching:
        print(f"{scenario.scenario_id}\t{scenario.name}\t{scenario.platform}\t{scenario.module}\t{scenario.service}\t{scenario_status(deployment_root, scenario)}")
    return 0


def command_describe(scenario_id: str) -> int:
    scenario = find_scenario(scenario_id)
    print(f"Scenario ID: {scenario.scenario_id}")
    print(f"Name: {scenario.name}")
    print(f"Platform: {scenario.platform}")
    print(f"Module: {scenario.module}")
    print(f"CSPM rule: {scenario.rule_id}")
    print(f"Description: {scenario.description}")
    return 0


def provision(scenarios_root: Path, scenario_id: str, deployment_root: Path, region: str | None, expected_account_id: str | None, apply: bool, ami_id: str | None = None, availability_zone: str | None = None, location: str = "centralindia", expected_subscription_id: str | None = None) -> Path:
    scenario = find_scenario(scenario_id)
    if scenario.platform == "Azure":
        if not expected_subscription_id:
            raise ValueError("Azure deployment requires --expected-subscription-id.")
        return deploy_azure(scenarios_root, scenario.rule_id, deployment_root / scenario.scenario_id, location, expected_subscription_id, apply)
    if not region or not expected_account_id:
        raise ValueError("AWS deployment requires --region and --expected-account-id.")
    instance_rules = {"CSPM-AWS-2024-0027", "CSPM-AWS-2024-0029", "CSPM-AWS-2024-0152"}
    zone_only_rules = {"CSPM-AWS-2024-0018", "CSPM-AWS-2024-0023"}
    if scenario.rule_id in instance_rules and region != "us-east-1" and not (ami_id and availability_zone):
        raise ValueError(f"{scenario_id} uses us-east-1 defaults. Use --region us-east-1 or override both --ami-id and --availability-zone.")
    if scenario.rule_id in zone_only_rules and region != "us-east-1" and not availability_zone:
        raise ValueError(f"{scenario_id} uses a us-east-1 default. Use --region us-east-1 or override --availability-zone.")
    return deploy(
        scenarios_root, scenario.rule_id, deployment_root / scenario.scenario_id,
        region, expected_account_id, apply, ami_id, availability_zone,
    )


def provision_batch(scenarios_root: Path, module: str, service: str | None, deployment_root: Path, region: str | None, expected_account_id: str | None, apply: bool, location: str = "centralindia", expected_subscription_id: str | None = None) -> list[Path]:
    """Provision every reviewed scenario matching a module and optional service."""
    matching = [
        scenario for scenario in SCENARIOS
        if scenario.module.lower() == module.lower()
        and (service is None or scenario.service.lower() == service.lower())
    ]
    if not matching:
        raise ValueError(f"No scenarios match module={module!r} and service={service!r}.")
    return [
        provision(scenarios_root, scenario.scenario_id, deployment_root, region, expected_account_id, apply, location=location, expected_subscription_id=expected_subscription_id)
        for scenario in matching
    ]


def destroy(deployment_root: Path, scenario_id: str, region: str | None, expected_account_id: str | None, apply: bool, location: str = "centralindia", expected_subscription_id: str | None = None) -> Path:
    if not apply:
        raise ValueError("Destroy requires --apply. This prevents an accidental cloud change.")
    scenario = find_scenario(scenario_id)
    fixture = deployment_root / scenario.scenario_id / scenario.rule_id
    if not (fixture / "terraform.tfstate").is_file():
        raise ValueError(f"No Terraform state exists for {scenario_id} at {fixture}.")
    if scenario.platform == "Azure":
        if not expected_subscription_id:
            raise ValueError("Azure destroy requires --expected-subscription-id.")
        actual_subscription_id = verified_subscription_id()
        if actual_subscription_id.lower() != expected_subscription_id.lower():
            raise RuntimeError(f"Azure subscription mismatch: expected {expected_subscription_id}, got {actual_subscription_id}.")
        variables = ["-var=allow_unsafe_apply=true", f"-var=azure_location={location}", f"-var=azure_subscription_id={expected_subscription_id}"]
    else:
        if not region or not expected_account_id or not expected_account_id.isdigit() or len(expected_account_id) != 12:
            raise ValueError("AWS destroy requires --region and a 12-digit --expected-account-id.")
        actual_account_id = verified_account_id(region)
        if actual_account_id != expected_account_id:
            raise RuntimeError(f"AWS account mismatch: expected {expected_account_id}, got {actual_account_id}.")
        variables = ["-var=allow_unsafe_apply=true", f"-var=aws_region={region}"]
    if shutil.which("terraform") is None:
        raise RuntimeError("Terraform was not found on PATH.")
    run_command(["terraform", "destroy", "-auto-approve", *variables], fixture)
    return fixture


def destroy_batch(module: str, service: str | None, deployment_root: Path, region: str | None, expected_account_id: str | None, apply: bool, location: str = "centralindia", expected_subscription_id: str | None = None) -> list[Path]:
    """Destroy deployed scenarios matching a module and optional service."""
    matching = [
        scenario for scenario in SCENARIOS
        if scenario.module.lower() == module.lower()
        and (service is None or scenario.service.lower() == service.lower())
        and (deployment_root / scenario.scenario_id / scenario.rule_id / "terraform.tfstate").is_file()
    ]
    if not matching:
        raise ValueError(f"No deployed scenarios match module={module!r} and service={service!r}.")
    return [
        destroy(deployment_root, scenario.scenario_id, region, expected_account_id, apply, location, expected_subscription_id)
        for scenario in matching
    ]


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Provision prebuilt Terraform CSPM misconfiguration fixtures.")
    parser.add_argument("--scenarios-root", type=Path, default=DEFAULT_SCENARIOS_ROOT, help="Directory or checkout containing static rule fixture directories.")
    commands = parser.add_subparsers(dest="command", required=True)
    list_parser = commands.add_parser("list", help="List fixtures or scenarios in a module.")
    list_parser.add_argument("--module", choices=["CSPM", "CIEM"])
    list_parser.add_argument("--service", help="Filter scenarios by service, for example S3.")
    list_parser.add_argument("--provider", type=str.upper, choices=["AWS", "AZURE"], help="Filter scenarios by cloud provider.")
    list_parser.add_argument("--services", action="store_true", help="List services available in the selected module.")
    list_parser.add_argument("--deployment-root", type=Path, default=Path("deployments"))
    scenario_list_parser = commands.add_parser("scenario-list", help="List reviewed scenario catalog entries.")
    scenario_list_parser.add_argument("--module", choices=["CSPM", "CIEM"])
    scenario_list_parser.add_argument("--service", help="Filter scenarios by service, for example S3.")
    scenario_list_parser.add_argument("--provider", type=str.upper, choices=["AWS", "AZURE"], help="Filter scenarios by cloud provider.")
    scenario_list_parser.add_argument("--services", action="store_true", help="List services available in the selected module.")
    scenario_list_parser.add_argument("--deployment-root", type=Path, default=Path("deployments"))
    describe_parser = commands.add_parser("describe", help="Show a scenario and its backing CSPM rule.")
    describe_parser.add_argument("scenario_id")
    generate_parser = commands.add_parser("generate")
    generate_parser.add_argument("rule_id")
    generate_parser.add_argument("--output", type=Path, default=Path("generated"))
    generate_all_parser = commands.add_parser("generate-all")
    generate_all_parser.add_argument("--output", type=Path, default=Path("generated"))
    deploy_parser = commands.add_parser("deploy", help="Deploy one fixture after verifying the AWS account.")
    deploy_parser.add_argument("rule_id")
    deploy_parser.add_argument("--region", required=True)
    deploy_parser.add_argument("--expected-account-id", required=True)
    deploy_parser.add_argument("--apply", action="store_true", help="Required acknowledgement for an AWS change.")
    deploy_parser.add_argument("--ami-id")
    deploy_parser.add_argument("--availability-zone")
    deploy_parser.add_argument("--deployment-root", type=Path, default=Path("deployments"))
    provision_parser = commands.add_parser("provision", help="Provision a named AWS test scenario.")
    provision_parser.add_argument("scenario_id")
    provision_parser.add_argument("--region")
    provision_parser.add_argument("--expected-account-id")
    provision_parser.add_argument("--location", default="centralindia")
    provision_parser.add_argument("--expected-subscription-id")
    provision_parser.add_argument("--apply", action="store_true")
    provision_parser.add_argument("--ami-id", help="Pre-approved AMI ID; required for EC2 instance scenarios.")
    provision_parser.add_argument("--availability-zone", help="Pre-approved zone, for example us-west-1a.")
    provision_parser.add_argument("--deployment-root", type=Path, default=Path("deployments"))
    provision_batch_parser = commands.add_parser("provision-batch", help="Provision every reviewed scenario in a module or service.")
    provision_batch_parser.add_argument("--module", choices=["CSPM", "CIEM"], required=True)
    provision_batch_parser.add_argument("--service", help="Optional service filter, for example S3, VPC, RDS, or IAM.")
    provision_batch_parser.add_argument("--region")
    provision_batch_parser.add_argument("--expected-account-id")
    provision_batch_parser.add_argument("--location", default="centralindia")
    provision_batch_parser.add_argument("--expected-subscription-id")
    provision_batch_parser.add_argument("--apply", action="store_true", help="Required acknowledgement for AWS changes.")
    provision_batch_parser.add_argument("--deployment-root", type=Path, default=Path("deployments"))
    destroy_parser = commands.add_parser("destroy", help="Destroy a previously provisioned named scenario.")
    destroy_parser.add_argument("scenario_id")
    destroy_parser.add_argument("--region")
    destroy_parser.add_argument("--expected-account-id")
    destroy_parser.add_argument("--location", default="centralindia")
    destroy_parser.add_argument("--expected-subscription-id")
    destroy_parser.add_argument("--apply", action="store_true")
    destroy_parser.add_argument("--deployment-root", type=Path, default=Path("deployments"))
    destroy_batch_parser = commands.add_parser("destroy-batch", help="Destroy deployed scenarios in a module or service.")
    destroy_batch_parser.add_argument("--module", choices=["CSPM", "CIEM"], required=True)
    destroy_batch_parser.add_argument("--service", help="Optional service filter, for example S3, VPC, RDS, or IAM.")
    destroy_batch_parser.add_argument("--region")
    destroy_batch_parser.add_argument("--expected-account-id")
    destroy_batch_parser.add_argument("--location", default="centralindia")
    destroy_batch_parser.add_argument("--expected-subscription-id")
    destroy_batch_parser.add_argument("--apply", action="store_true", help="Required acknowledgement for AWS changes.")
    destroy_batch_parser.add_argument("--deployment-root", type=Path, default=Path("deployments"))
    args = parser.parse_args(argv)

    if args.command == "list" and args.module is None and args.service is None and args.provider is None and not args.services:
        return command_list(args.scenarios_root)
    if args.command == "list":
        return command_scenario_list(args.module, args.deployment_root, args.service, args.services, args.provider)
    if args.command == "scenario-list":
        return command_scenario_list(args.module, args.deployment_root, args.service, args.services, args.provider)
    if args.command == "describe":
        return command_describe(args.scenario_id)
    if args.command == "generate":
        print(generate(args.scenarios_root, args.output, args.rule_id))
        return 0
    if args.command == "deploy":
        print(deploy(args.scenarios_root, args.rule_id, args.deployment_root, args.region, args.expected_account_id, args.apply, args.ami_id, args.availability_zone))
        return 0
    if args.command == "provision":
        print(provision(args.scenarios_root, args.scenario_id, args.deployment_root, args.region, args.expected_account_id, args.apply, args.ami_id, args.availability_zone, args.location, args.expected_subscription_id))
        return 0
    if args.command == "provision-batch":
        for fixture in provision_batch(args.scenarios_root, args.module, args.service, args.deployment_root, args.region, args.expected_account_id, args.apply, args.location, args.expected_subscription_id):
            print(fixture)
        return 0
    if args.command == "destroy":
        print(destroy(args.deployment_root, args.scenario_id, args.region, args.expected_account_id, args.apply, args.location, args.expected_subscription_id))
        return 0
    if args.command == "destroy-batch":
        for fixture in destroy_batch(args.module, args.service, args.deployment_root, args.region, args.expected_account_id, args.apply, args.location, args.expected_subscription_id):
            print(fixture)
        return 0
    return command_generate_all(args.scenarios_root, args.output)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError) as error:
        print(f"Error: {error}")
        raise SystemExit(1)
