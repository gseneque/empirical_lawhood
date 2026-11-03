# SPDX-License-Identifier: MPL-2.0
"""In-memory selected-source contracts for disclosed prospective test fixtures."""

from empirical_lawhood.infrastructure.source_closure import AdmittedTargetSource, CapturedTargetClosure, TrackedSourceMember
from empirical_lawhood.infrastructure.source_policy import CheckoutSourceAdmission
from empirical_lawhood.planning.study_issue import ImplementationSourceClosure, SelectedSourceManifest, SelectedSourceManifestMember, SourceClosureKind


def synthetic_capture(closure_id, implementation_sha256, *, clean=True):
    """No Git observation, clone, publication, authority or executable source."""
    member = SelectedSourceManifestMember("src/empirical_lawhood/exposed_fixture.py", "100644", 1, "1"*64)
    manifest = SelectedSourceManifest(closure_id + ".selected-source-manifest", "a"*40,
        implementation_sha256, "8"*64, (member,))
    closure = ImplementationSourceClosure(closure_id, SourceClosureKind.EXACT_SOURCE_CLOSURE, "a"*40,
        implementation_sha256, "8"*64, clean, manifest.identity)
    # The false case retains a documentary tracked change; it does not claim an
    # unobserved clean checkout or turn a new test label into fresh evidence.
    admission = CheckoutSourceAdmission(b"" if clean else b" M README.md\0", None, (member.relative_path,))
    source = AdmittedTargetSource(closure.implementation_commit, closure.implementation_sha256,
        closure.source_tree_sha256, (TrackedSourceMember(member.relative_path, member.mode, member.size_bytes, member.sha256),),
        admission, admission)
    return CapturedTargetClosure(closure, manifest, source)


class SyntheticSourceInspector:
    def __init__(self, *_args, **_kwargs):
        pass

    def observe(self, expected):
        return expected


def install_historical_source_capture(monkeypatch, module, closure):
    """Preserve literal historical output controls, not current source acceptance.

    Source capture, provenance publication and source reobservation are explicit
    seams here. New current-source controls exercise the real owners separately.
    No publication, clean-source claim or authority is manufactured.
    """
    from types import SimpleNamespace

    monkeypatch.setattr(module, "_capture_prospective_source", lambda *_args, **_kwargs: SimpleNamespace(closure=closure))
    monkeypatch.setattr(module, "_publish_source_provenance", lambda **_kwargs: None)
    monkeypatch.setattr(module, "GitStudySourceClosureInspector", SyntheticSourceInspector)
    if hasattr(module, "capture_clean_target_closure"):
        monkeypatch.setattr(module, "capture_clean_target_closure", lambda *_args, **_kwargs: closure)
