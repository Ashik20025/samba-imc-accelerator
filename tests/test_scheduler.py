import unittest

from samba.architecture import HardwareConfig
from samba.simulator import CoreRuntime, _linear_reduce, _tree_reduce


class SchedulerTest(unittest.TestCase):
    def test_tree_sorted_reduction_is_not_slower_than_linear_for_skewed_cores(self):
        hw = HardwareConfig(load_cycles=2, store_cycles=2, send_cycles=4, receive_cycles=4)
        cores = [
            CoreRuntime(0, 0, 200.0, 0.0),
            CoreRuntime(1, 0, 10.0, 0.0),
            CoreRuntime(2, 0, 220.0, 0.0),
            CoreRuntime(3, 0, 20.0, 0.0),
        ]
        linear, _ = _linear_reduce(cores, hw)
        tree, _ = _tree_reduce(cores, hw, latency_sort=True)
        self.assertLessEqual(tree, linear)


if __name__ == "__main__":
    unittest.main()
