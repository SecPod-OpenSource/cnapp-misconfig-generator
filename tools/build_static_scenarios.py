"""One-time exporter for the Terraform scenario repository.

This is a maintainer-only build tool. The runtime CLI never imports or reads
the private CSPM JSON feed; it consumes the static output produced here.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.templates import TEMPLATES


OUTPUT = ROOT / "terraform_scenarios" / "rules"


def main() -> None:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)
    for rule_id, template in TEMPLATES.items():
        destination = OUTPUT / rule_id
        destination.mkdir()
        (destination / "main.tf").write_text(template.terraform, encoding="utf-8")
        (destination / "README.md").write_text(
            f"# {rule_id}\n\n{template.description}\n\n"
            "This is an intentionally insecure Terraform test fixture. "
            "Use only in a dedicated disposable account.\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
