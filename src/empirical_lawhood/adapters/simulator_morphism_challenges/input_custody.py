"""Authenticate issued RC payload and prerequisite custody against current runtime ownership."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Mapping
from empirical_lawhood.storage.contracts.artifacts import ArtifactWriter
from empirical_lawhood.domains.history.simulator_morphism_challenges.contracts import SimulatorMorphismChallengePhase
from empirical_lawhood.domains.history.simulator_morphism_challenges.retained_results import RCChallengeRetainedResult

from empirical_lawhood.domains.history.simulator_morphism_challenges.issued_inputs import RCChallengeIssuedInputs
from empirical_lawhood.adapters.simulator_morphism_challenges.numeric_inputs import authenticate_numeric_input

@dataclass(frozen=True, slots=True)
class RCChallengeRuntimeInputPort:
    """Code-injected exact source bytes and existing guarded artifact verifier."""

    source_files: Mapping[str, bytes] = field(repr=False, compare=False)
    artifact_writer: ArtifactWriter = field(repr=False, compare=False)
    prerequisite_access_verifier: Callable[[RCChallengeRetainedResult], None] | None = field(default=None, repr=False, compare=False)

    def authenticate(self, issued: RCChallengeIssuedInputs) -> None:
        from empirical_lawhood.adapters.simulator_morphism_challenges.runtime_provider import implementation_closures
        from empirical_lawhood.domains.history.simulator_morphism_challenges.runtime_contracts import SimulatorMorphismChallengeEvaluationDesignFreeze

        closures = implementation_closures(self.source_files)
        if closures.complete_sha256 != issued.implementation_source_closure_sha256:
            raise ValueError("issued RC producing source closure differs from the exact current owner bytes")
        if issued.numeric_input is not None:
            authenticate_numeric_input(issued.numeric_input, self.artifact_writer)
        for retained in issued.prerequisite_custody:
            if retained.requires_outcome_authority:
                if self.prerequisite_access_verifier is None:
                    raise PermissionError("RC protected prerequisite requires actual current outcome authority")
                self.prerequisite_access_verifier(retained)
            retained.authenticate(self.artifact_writer)
        if issued.config.phase is SimulatorMorphismChallengePhase.EVALUATION:
            designs = tuple(value.record for value in issued.external_records() if isinstance(value.record, SimulatorMorphismChallengeEvaluationDesignFreeze))
            if len(designs) != 1:
                raise ValueError("evaluation requires one exact authenticated design freeze")
            design = designs[0]
            method = design.method_freeze
            if (design.implementation_source_closure_sha256, method.observer_implementation_sha256,
                method.generator_implementation_sha256, method.evaluator_implementation_sha256) != (
                closures.complete_sha256, closures.observer_sha256, closures.generator_sha256, closures.evaluator_sha256):
                raise ValueError("evaluation design/method freeze differs from the actual current producing-code closures")
