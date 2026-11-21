# SPDX-License-Identifier: MPL-2.0
"""Project authenticated retained Rubisco work through the existing inquiry API."""

from dataclasses import dataclass
from pathlib import Path

from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.retained_inquiry import retained_inquiry_specification
from empirical_lawhood.api.recursive_authoring import load_authored_wave
from empirical_lawhood.api.recursive_inquiry import project_inquiry_state
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_inquiry_policy import RobustInquirySpecification, WorkBoundInquiryState
from empirical_lawhood.science.models.time import CausalPhase, InformationCutoff
from empirical_lawhood.execution.recursive_inquiry import InquiryStateSources, InquiryWaveSource


@dataclass(frozen=True, slots=True)
class RetainedResponseInquiry:
    specification: RobustInquirySpecification
    state: WorkBoundInquiryState
    sources: InquiryStateSources


def project_retained_response_inquiry(*, directory, information_cutoff, artifact_writer):
    """Read existing outcomes only at an explicitly post-outcome cutoff.

    This does not commit an admission, choose a future policy or enter workers.
    It cannot be used to recast an already observed reference as prospective.
    """
    exact(information_cutoff, InformationCutoff)
    if information_cutoff.phase is not CausalPhase.POST_OUTCOME:
        raise ValueError("retained outcome projection requires an explicit post-outcome cutoff")
    packet, draft, _, _ = load_authored_wave(directory=directory, artifact_writer=artifact_writer, lazy_payloads=True)
    specification = retained_inquiry_specification(draft)
    if information_cutoff.clock_id != specification.endpoint.clock_id:
        raise ValueError("retained response inquiry changes the selected physical clock")
    root = Path(artifact_writer.root.contract.canonical_path)
    path = Path(directory).resolve(strict=True)
    sources = InquiryStateSources((InquiryWaveSource(path.relative_to(root).as_posix(),
        ObjectIdentity.from_record(packet.packet_id, packet), True),))
    state_id = "state." + specification.specification_id + "." + information_cutoff.fingerprint()[:24]
    state = project_inquiry_state(specification=specification, state_id=state_id,
        information_cutoff=information_cutoff, sources=sources, artifact_writer=artifact_writer)
    return RetainedResponseInquiry(specification, state, sources)
