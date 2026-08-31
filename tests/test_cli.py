import shutil
import subprocess
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch
from contextlib import redirect_stdout

from src.cli import DEFAULT_SCENARIOS_ROOT, command_count, command_describe, command_scenario_list, deploy, destroy_batch, generate, provision, provision_batch, run_command, verified_account_id
from src.scenarios import SCENARIOS


SCENARIOS_ROOT = DEFAULT_SCENARIOS_ROOT


class GeneratorTests(unittest.TestCase):
    def setUp(self):
        self.output = Path(__file__).parent / ".test-output"
        shutil.rmtree(self.output, ignore_errors=True)
        self.addCleanup(shutil.rmtree, self.output, True)

    def test_copies_static_fixture_without_feed_json(self):
        fixture = generate(SCENARIOS_ROOT, self.output, "CSPM-AWS-2024-0033-08")
        terraform = (fixture / "main.tf").read_text(encoding="utf-8")
        self.assertIn("count       = var.allow_unsafe_apply ? 1 : 0", terraform)
        self.assertFalse((fixture / "source_rule.json").exists())

    def test_rejects_missing_static_fixture(self):
        with self.assertRaisesRegex(ValueError, "Static Terraform fixture"):
            generate(SCENARIOS_ROOT, self.output, "CSPM-AWS-2024-0001")

    def test_ec2_templates_reference_their_expected_insecure_setting(self):
        cases = {
            "CSPM-AWS-2024-0020": "aws_default_security_group",
            "CSPM-AWS-2024-0023": "encrypted         = false",
            "CSPM-AWS-2024-0032": 'protocol    = "icmp"',
            "CSPM-AWS-2024-0033-01": "from_port   = 3306",
            "CSPM-AWS-2024-0034-02": "from_port   = 23",
            "CSPM-AWS-2024-0035": "to_port     = 2000",
            "CSPM-AWS-2024-0476": "all outbound traffic",
            "CSPM-AWS-2024-0152": 'http_tokens = "optional"',
            "CSPM-AWS-2024-0018": 'group    = "all"',
        }
        for rule_id, expected in cases.items():
            terraform = (SCENARIOS_ROOT / rule_id / "main.tf").read_text(encoding="utf-8")
            self.assertIn(expected, terraform)

    def test_public_ip_ec2_fixture_is_supported(self):
        fixture = generate(SCENARIOS_ROOT, self.output, "CSPM-AWS-2024-0027")
        terraform = (fixture / "main.tf").read_text(encoding="utf-8")
        self.assertIn("associate_public_ip_address = true", terraform)
        self.assertIn("egress      = []", terraform)

    @patch("src.cli.run_command")
    @patch("src.cli.generate")
    @patch("src.cli.verified_account_id", return_value="123456789012")
    @patch("src.cli.shutil.which", return_value="terraform")
    def test_deploy_requires_account_match_and_runs_plan_before_apply(self, _, __, mocked_generate, mocked_run):
        mocked_generate.return_value = self.output
        deploy(SCENARIOS_ROOT, "CSPM-AWS-2024-0027", self.output, "ap-south-1", "123456789012", True)
        commands = [call.args[0] for call in mocked_run.call_args_list]
        self.assertEqual(commands[0], ["terraform", "init", "-input=false"])
        self.assertEqual(commands[1][0:2], ["terraform", "plan"])
        self.assertEqual(commands[2][0:3], ["terraform", "apply", "-auto-approve"])

    def test_scenario_catalog_lists_and_describes_public_ip_fixture(self):
        output = StringIO()
        with redirect_stdout(output):
            command_scenario_list("CSPM", self.output)
            command_describe("cspm-aws-ec2-public-ip")
        text = output.getvalue()
        self.assertIn("SCENARIO ID", text)
        self.assertIn("cspm-aws-ec2-public-ip", text)
        self.assertIn("CSPM-AWS-2024-0027", text)

    def test_count_reports_static_fixture_breakdown(self):
        output = StringIO()
        with redirect_stdout(output):
            command_count(SCENARIOS_ROOT)
        self.assertEqual(
            output.getvalue().splitlines(),
            [
                "CLOUD\tCSPM\tCIEM\tTOTAL",
                "AWS\t70\t9\t79",
                "Azure\t40\t1\t41",
                "TOTAL\t110\t10\t120",
            ],
        )

    def test_cnapp_style_ec2_scenarios_are_listed(self):
        output = StringIO()
        with redirect_stdout(output):
            command_scenario_list("CSPM", self.output)
        text = output.getvalue()
        self.assertIn("cspm-aws-ec2-imds-v1-enabled", text)
        self.assertIn("cspm-aws-ec2-open-public", text)
        self.assertIn("cspm-aws-ec2-ami-public-volume", text)

    def test_service_filter_and_service_list(self):
        output = StringIO()
        with redirect_stdout(output):
            command_scenario_list("CSPM", self.output, service="S3")
        self.assertIn("cspm-aws-s3-public-read", output.getvalue())
        self.assertNotIn("cspm-aws-ec2-open-public", output.getvalue())

        output = StringIO()
        with redirect_stdout(output):
            command_scenario_list("CSPM", self.output, services=True)
        self.assertEqual(set(output.getvalue().splitlines()), {"Compute", "EC2", "Lambda", "Network", "RDS", "S3", "SQL", "Storage", "VPC"})

    def test_provider_filter(self):
        output = StringIO()
        with redirect_stdout(output):
            command_scenario_list("CSPM", self.output, provider="Azure")
        self.assertIn("cspm-azure-storage-https-disabled", output.getvalue())
        self.assertNotIn("cspm-aws-ec2-open-public", output.getvalue())

    def test_every_static_fixture_has_one_friendly_scenario(self):
        fixture_ids = {
            path.name for path in SCENARIOS_ROOT.iterdir()
            if path.is_dir() and (path / "main.tf").is_file()
        }
        scenario_rule_ids = {scenario.rule_id for scenario in SCENARIOS}
        self.assertEqual(len(SCENARIOS), 120)
        self.assertEqual(scenario_rule_ids, fixture_ids)

    def test_rds_batch_one_scenarios_are_listed(self):
        output = StringIO()
        with redirect_stdout(output):
            command_scenario_list("CSPM", self.output, service="RDS")
        text = output.getvalue()
        self.assertIn("cspm-aws-rds-backup-disabled", text)
        self.assertIn("cspm-aws-rds-default-port", text)

    @patch("src.cli.provision")
    def test_provision_batch_filters_by_module_and_service(self, mocked_provision):
        provision_batch(SCENARIOS_ROOT, "CIEM", "IAM", self.output, "us-east-1", "123456789012", True)
        self.assertEqual(mocked_provision.call_count, 9)

    @patch("src.cli.destroy")
    def test_destroy_batch_only_selects_deployed_scenarios(self, mocked_destroy):
        scenario = SCENARIOS[0]
        state = self.output / scenario.scenario_id / scenario.rule_id / "terraform.tfstate"
        state.parent.mkdir(parents=True)
        state.write_text("{}", encoding="utf-8")
        destroy_batch("CSPM", None, self.output, "us-east-1", "123456789012", True)
        mocked_destroy.assert_called_once_with(self.output, scenario.scenario_id, "us-east-1", "123456789012", True, "centralindia", None)

    def test_ciem_iam_scenarios_are_listed(self):
        output = StringIO()
        with redirect_stdout(output):
            command_scenario_list("CIEM", self.output, service="IAM")
        text = output.getvalue()
        self.assertIn("ciem-aws-iam-user-excessive-permissions", text)
        self.assertNotIn("cspm-aws-ec2-open-public", text)

    def test_scp_compatible_scenarios_do_not_use_denied_data_sources(self):
        for rule_id in ("CSPM-AWS-2024-0027", "CSPM-AWS-2024-0029", "CSPM-AWS-2024-0152", "CSPM-AWS-2024-0018", "CSPM-AWS-2024-0023"):
            terraform = (SCENARIOS_ROOT / rule_id / "main.tf").read_text(encoding="utf-8")
            self.assertNotIn("aws_ssm_parameter", terraform)
            self.assertNotIn("aws_availability_zones", terraform)

    def test_open_public_rejects_hardcoded_east_region_defaults_in_another_region(self):
        with self.assertRaisesRegex(ValueError, "uses us-east-1 defaults"):
            provision(SCENARIOS_ROOT, "cspm-aws-ec2-open-public", self.output, "us-west-1", "123456789012", True)

    @patch("src.cli.run_command")
    @patch("src.cli.shutil.which", return_value="aws")
    def test_aws_authentication_error_includes_aws_cli_diagnostic(self, _, mocked_run):
        mocked_run.side_effect = subprocess.CalledProcessError(
            254, ["aws", "sts", "get-caller-identity"], stderr="Unable to locate credentials"
        )
        with self.assertRaisesRegex(RuntimeError, "Unable to locate credentials"):
            verified_account_id("us-east-1")

    @patch("src.cli.subprocess.run")
    @patch("src.cli.shutil.which", return_value=r"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd")
    @patch("src.cli.os.name", "nt")
    def test_windows_batch_wrapper_runs_through_cmd(self, mocked_which, mocked_run):
        run_command(["az", "account", "show"], self.output, capture_output=True)
        self.assertEqual(mocked_run.call_args.args[0], ["az", "account", "show"])
        self.assertTrue(mocked_run.call_args.kwargs["shell"])


if __name__ == "__main__":
    unittest.main()
