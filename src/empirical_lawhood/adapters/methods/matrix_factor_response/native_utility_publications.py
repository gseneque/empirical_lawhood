# SPDX-License-Identifier: MPL-2.0
"""Authenticate actual E2 source corpus and templates before native contact."""
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import authenticate_publication
from .configured_protected_originals import _authenticate_artifact
from .native_training_publications import _manifest_publications
from .native_utility_records import NativeUtilityRequest, validate_request


def authenticate_request(plane,request):
    if type(request) is not NativeUtilityRequest:raise TypeError("native E2 publication custody requires its own exact request")
    request.__post_init__()
    for artifact,custody in request.exposure_support:_authenticate_artifact(plane,artifact,custody)
    selected={}
    for publication,record in _manifest_publications(request.source_manifest):
        path=publication.materialization.relative_path
        if selected.setdefault(path,(publication,record))!=(publication,record):raise PermissionError("native E2 prior source publications alias different original records")
    for publication in request.template_publications:
        path=publication.materialization.relative_path
        if selected.setdefault(path,(publication,None))!=(publication,None):raise PermissionError("native E2 template aliases another scientific source")
    for _,(publication,record) in sorted(selected.items()):authenticate_publication(plane,publication,record)


def authenticate_utility_publications(plane,config_inputs):
    from .native_utility_bindings import NativeUtilityEntryConfig
    entries=tuple(row.record for row in config_inputs if type(row.record) is NativeUtilityEntryConfig)
    if len(entries)!=1:raise PermissionError("native E2 needs one actual pre-contact frozen entry")
    entry,=entries;entry.__post_init__();validate_request(entry.specification,entry.request)
    authenticate_request(plane,entry.request)
