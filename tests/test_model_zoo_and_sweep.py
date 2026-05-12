import tempfile
import unittest
from pathlib import Path

from samba.design_space import run_design_space, write_design_space
from samba.simulator import load_config
from samba.workload import build_workload


class ModelZooAndSweepTest(unittest.TestCase):
    def test_model_zoo_generates_vgg_layers(self):
        root = Path(__file__).resolve().parents[1]
        config = load_config(root / "configs" / "vgg19_cifar100_ablation.json")
        workload = build_workload(
            config.workload,
            seed=config.seed,
            crossbar_size=config.hardware.crossbar_size,
        )
        self.assertEqual(len(workload.layers), 8)
        self.assertTrue(workload.layers[0].name.startswith("vgg19_conv"))

    def test_design_space_writes_csv_and_markdown(self):
        root = Path(__file__).resolve().parents[1]
        config = load_config(root / "configs" / "smoke.json")
        rows = run_design_space(
            config,
            crossbar_sizes=[16],
            cores_per_tile=[2],
            mvmus_per_core=[2, 4],
        )
        self.assertEqual(len(rows), 6)
        with tempfile.TemporaryDirectory() as temp_dir:
            write_design_space(rows, temp_dir)
            self.assertTrue((Path(temp_dir) / "design_space.csv").exists())
            self.assertTrue((Path(temp_dir) / "design_space.md").exists())


if __name__ == "__main__":
    unittest.main()
