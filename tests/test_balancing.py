import unittest

import numpy as np

from samba.architecture import HardwareConfig, OptimizationConfig
from samba.balancing import apply_column_exchange, apply_split_mvmus
from samba.mapping import MVMUBlock


class BalancingTest(unittest.TestCase):
    def test_column_exchange_reduces_pair_bottleneck(self):
        hw = HardwareConfig(crossbar_size=8, weight_bits=4, bits_per_slice=2, input_bits=4)
        dense = np.ones((8, 8), dtype=np.int32) * 3
        sparse = np.zeros((8, 8), dtype=np.int32)
        sparse[:, 0] = 1
        slow = MVMUBlock("layer", 0, 0, 0, dense, dense.shape)
        fast = MVMUBlock("layer", 0, 0, 1, sparse, sparse.shape)
        before = max(
            slow.estimate(hw, reconfigurable_adc=True).latency_cycles,
            fast.estimate(hw, reconfigurable_adc=True).latency_cycles,
        )
        stats = apply_column_exchange(
            [slow, fast],
            hw,
            OptimizationConfig(max_column_exchange_iters=8, min_improvement_cycles=0.0),
        )
        after = max(
            slow.estimate(hw, reconfigurable_adc=True).latency_cycles,
            fast.estimate(hw, reconfigurable_adc=True).latency_cycles,
        )
        self.assertGreater(stats.column_swaps, 0)
        self.assertLessEqual(after, before)

    def test_split_preserves_weight_sum(self):
        hw = HardwareConfig(crossbar_size=8, weight_bits=4, bits_per_slice=2, input_bits=4)
        weights = np.zeros((8, 8), dtype=np.int32)
        weights[:, :4] = 3
        weights[:, 4:] = 1
        block = MVMUBlock("layer", 0, 0, 0, weights.copy(), weights.shape)
        blocks, stats = apply_split_mvmus(
            [block],
            hw,
            OptimizationConfig(split_extra_mvmu_fraction=1.0, min_improvement_cycles=0.0),
        )
        self.assertEqual(stats.split_mvmus, 1)
        reconstructed = sum((item.weights for item in blocks), start=np.zeros_like(weights))
        np.testing.assert_array_equal(reconstructed, weights)


if __name__ == "__main__":
    unittest.main()
