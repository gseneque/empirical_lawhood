# SPDX-License-Identifier: MPL-2.0
"""Names of the separately selected prospective curve/mechanism contract.

The measured FACTOR58 response target is unchanged. These choices identify a
new prediction comparison and feature construction, never an old K claim.
"""
from fractions import Fraction

CURVE_LOSS_RULE = 'ROOT_RMS_POSTPROCESSED_LOG1P_PAIRED58_OVER_LOG1P_EPSILON_001'
CURVE_SELECTION_RULE = 'TWO_FOLD_COMMON_COMPLETE_PAIRED58_RIDGE_PENALTIES_1_10_CURVE_RMS'
CURVE_IMPROVEMENT_RULE = 'MATCHED_NORMALIZED_ROOT_CURVE_RMS_REDUCTION_AT_LEAST_01'
CURVE_RELATION_LOSS_RULE = 'EQUAL_NINE_COORDINATE_NORMALIZED_ROOT_CURVE_RMS'
CURVE_TRANSFER_PROCEDURE = 'EXACT_PAIRED_E5_AND_ASSIGNED_CURVE_WIN_E6'
CURVE_MARGIN = Fraction(1, 10)
MECHANISM_FEATURES = ('d_hessian_block', 'd_hessian_mix')
CURVE_RELATION_METHODS = ('BR', 'PHYSICAL', 'RAW_DEV_MEDIAN', 'RELATION_BASE', 'SR')
