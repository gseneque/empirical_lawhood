# SPDX-License-Identifier: MPL-2.0
"""Preparation feature counts for the exact selected configured estimators."""


def feature_counts(methods):
    # Preserve the original paired15 census labels and derive matched labels
    # from their actual methods. The raw TRAIN median has no fitted features.
    labels = {'ALL_ORIGIN_RIDGE': 'all-origin', 'SPECTRAL_RIDGE': 'spectral'}
    return tuple(sorted((labels.get(method.method_key, method.method_key.lower().replace('_', '-'))
        + '-features', method.feature_count) for method in methods if method.feature_blocks))
