# SPDX-License-Identifier: MPL-2.0
"""Authenticated root inquiry projection; shared services own preview and commit."""

from dataclasses import dataclass
from pathlib import Path

from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_policy import initial_root_inquiry_menu, initial_root_inquiry_specification
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.api.recursive_authoring import load_authored_wave
from empirical_lawhood.api.recursive_execution import read_recursive_wave
from empirical_lawhood.api.recursive_inquiry import project_inquiry_state
from empirical_lawhood.science.inquiry.recursive_inquiry import identity
from empirical_lawhood.science.inquiry.recursive_inquiry_policy import RobustInquirySpecification, WorkBoundInquiryState
from empirical_lawhood.science.models.time import CausalPhase, InformationCutoff
from empirical_lawhood.design.recursive_authoring import RecursiveStudyDraft
from empirical_lawhood.design.recursive_inquiry_policy import RobustInquiryMenu, RobustInquiryPolicy
from empirical_lawhood.execution.recursive_inquiry import InquiryStateSources, InquiryWaveSource


@dataclass(frozen=True, slots=True)
class InitialRootInquiry:
    specification: RobustInquirySpecification
    state: WorkBoundInquiryState
    sources: InquiryStateSources
    menu: RobustInquiryMenu
    policy: RobustInquiryPolicy
    draft: RecursiveStudyDraft
    successor: RecursiveStudyDraft | None


def project_initial_root_inquiry(*, directory, information_cutoff, artifact_writer):
    exact(information_cutoff, InformationCutoff)
    if information_cutoff.phase is not CausalPhase.POST_OUTCOME:
        raise ValueError('retained initial root requires an explicit post-outcome cutoff')
    packet, draft, _, _ = load_authored_wave(directory=directory, artifact_writer=artifact_writer, lazy_payloads=True)
    specification = initial_root_inquiry_specification(draft)
    if information_cutoff.clock_id != specification.endpoint.clock_id:
        raise ValueError('initial root inquiry changes its selected closure clock')
    root = Path(artifact_writer.root.contract.canonical_path)
    path = Path(directory).resolve(strict=True)
    sources = InquiryStateSources((InquiryWaveSource(path.relative_to(root).as_posix(), identity(packet, packet.packet_id), True),))
    state = project_inquiry_state(specification=specification,
        state_id='state.' + specification.specification_id + '.' + information_cutoff.fingerprint()[:24],
        information_cutoff=information_cutoff, sources=sources, artifact_writer=artifact_writer)
    _, products, actual_draft, _ = read_recursive_wave(directory=directory, artifact_writer=artifact_writer, include_products=True)
    if actual_draft != draft:
        raise ValueError('initial root changed during authenticated inquiry projection')
    menu, policy, successor = initial_root_inquiry_menu(draft, specification, state, products)
    return InitialRootInquiry(specification, state, sources, menu, policy, draft, successor)
