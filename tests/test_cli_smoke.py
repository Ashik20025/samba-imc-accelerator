import tempfile
import unittest
from pathlib import Path

from samba.reporting import write_reports
from samba.simulator import load_config, run_experiment


class CLISmokeTest(unittest.TestCase):
    def test_smoke_config_generates_reports(self):
        root = Path(__file__).resolve().parents[1]
        config = load_config(root / "configs" / "smoke.json")
        result = run_experiment(config)
        with tempfile.TemporaryDirectory() as temp_dir:
            write_reports(result, temp_dir)
            self.assertTrue((Path(temp_dir) / "metrics.json").exists())
            self.assertTrue((Path(temp_dir) / "metrics.csv").exists())
            self.assertTrue((Path(temp_dir) / "report.md").exists())


if __name__ == "__main__":
    unittest.main()
