# SPDX-License-Identifier: MPL-2.0
"""Authenticate exact compact E1 prior publications; create no authority."""
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import authenticate_publication
from .compact_bindings import E1CompactCommitmentConfig


def authenticate_prior_publications(plane,config_inputs):
    entries=tuple(row.record for row in config_inputs if type(row.record) is E1CompactCommitmentConfig)
    if not entries:return
    if len(entries)!=1:raise ValueError('compact E1 needs one actual prior manifest')
    authenticate_manifest_publications(plane,entries[0].manifest)


def authenticate_manifest_publications(plane,manifest):
    from .compact_records import E1CompactManifest
    if type(manifest) is not E1CompactManifest:raise TypeError('compact E1 publication replay needs its exact original manifest')
    manifest.__post_init__()
    for publication,record in ((manifest.reservation.publication,manifest.reservation.allocation),
            (manifest.specification.publication,manifest.specification.selection),(manifest.scalar_publication,manifest.scalar_definition)):
        authenticate_publication(plane,publication,record)
