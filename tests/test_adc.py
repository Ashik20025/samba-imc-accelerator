import unittest

import numpy as np

from samba.adc import column_precisions, estimate_mvmu, required_adc_precision
from samba.architecture import HardwareConfig


class ADCTest(unittest.TestCase):
    def test_zero_column_needs_no_adc_precision(self):
        hw = HardwareConfig(crossbar_size=4, weight_bits=4, bits_per_slice=2, input_bits=2)
        weights = np.array(
            [
                [0, 1],
                [0, 2],
                [0, 0],
                [0, 3],
            ],
            dtype=np.int32,
        )
        precisions = column_precisions(weights, hw)
        self.assertTrue(np.all(precisions[:, 0] == 0))
        self.assertGreater(int(np.max(precisions[:, 1])), 0)

    def test_reconfigurable_adc_reduces_sparse_energy(self):
        hw = HardwareConfig(crossbar_size=8, weight_bits=4, bits_per_slice=2, input_bits=4)
        weights = np.zeros((8, 8), dtype=np.int32)
        weights[0, 0] = 1
        fixed = estimate_mvmu(weights, hw, reconfigurable_adc=False)
        sparse = estimate_mvmu(weights, hw, reconfigurable_adc=True)
        self.assertLess(sparse.energy_pj, fixed.energy_pj)

    def test_required_precision_is_capped(self):
        hw = HardwareConfig(crossbar_size=4, weight_bits=4, bits_per_slice=2)
        self.assertEqual(required_adc_precision(0, hw), 0)
        self.assertLessEqual(required_adc_precision(10_000, hw), hw.full_precision_adc_bits)


if __name__ == "__main__":
    unittest.main()
