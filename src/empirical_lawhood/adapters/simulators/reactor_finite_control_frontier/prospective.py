"""Native acquisition, external-format translation and custody integration."""

from dataclasses import dataclass
from functools import partial
from typing import Any, Callable
from empirical_lawhood.methods.control.finite_campaign import finite_control_services
from empirical_lawhood.methods.control.composition import ControllerStudyComposition
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.frozen_records import FrontierFrozenRoot, FrontierFrozenUse, UndeliverableSession
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.prospective_plan import ReactorFiniteControlFrontierProspectivePlan
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.records import FrontierPreparation, FrontierPrivate
from empirical_lawhood.domains.reactor.reactor_local_domain_qualification.records import LocalArrayPayload
from empirical_lawhood.domains.reactor.reactor_causal_response.measurements import NativeEpisode, TapeController
from empirical_lawhood.adapters.simulators.reactor_causal_response.acquisition import acquire_episode
from empirical_lawhood.adapters.simulators.reactor_causal_response.acquisition import acquire_with_progress
from empirical_lawhood.domains.reactor.reactor_regime_response.prepared_tape import WatchedPreparedTape
from empirical_lawhood.domains.reactor.reactor_prefix_response.batch_design import ReactorBatchSource
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.design.controller_study import ImplementationRole
from empirical_lawhood.execution.controller_runtime import DeliveryControllerTickReceipt
from empirical_lawhood.adapters.simulators.reactor_finite_control_frontier.acquisition import acquire_assay
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.native_measurements import donor_episodes, native_window, scenario_for
from empirical_lawhood.adapters.simulators.reactor_finite_control_frontier.delivery import FrontierPulseDeliveryPort, FrontierCommittedBranchOwner
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.words import pulse_tape

from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.native_acquisition_records import (
    FrontierNativeRoot as _science_FrontierNativeRoot,
    FrontierNativeUse as _science_FrontierNativeUse,
)

@dataclass
class RestoredRequest:
    frozen: FrontierFrozenUse
    delivery: FrontierPulseDeliveryPort
    services: ControllerStudyComposition

    def deliver(self, publisher: Any) -> DeliveryControllerTickReceipt:
        assert self.frozen.compiled is not None and self.frozen.commitment is not None
        tick = self.services.deliver_prepared_commitment(
            self.frozen.compiled, self.frozen.commitment
        )
        publisher.publish_record(tick.tick_id, tick)
        return tick

def acquire_prospective(
    *,
    source: ReactorBatchSource,
    preparation: FrontierPreparation,
    private: FrontierPrivate,
    frozen: FrontierFrozenRoot,
    plan: ReactorFiniteControlFrontierProspectivePlan,
    publisher: Any,
    acquire: Callable[..., NativeEpisode] = acquire_episode,
    progress: Callable[[int], None] | None = None,
) -> _science_FrontierNativeRoot:
    if (
        frozen.preparation != ObjectIdentity.from_record(preparation.record_id, preparation)
        or frozen.plan != ObjectIdentity.from_record(plan.record_id, plan)
        or source.fingerprint() != preparation.source_sha256
    ):
        raise ValueError("native macro lacks the exact complete precontact lock")
    donors = donor_episodes(preparation, private)
    scenario = scenario_for(preparation.root)
    uses = []
    completed = 0
    for use in frozen.uses:
        if use.projection is None:
            uses.append(
                _science_FrontierNativeUse(
                    use.request, LocalArrayPayload.pack({}), None, (), 0, use.reasons
                )
            )
            continue
        assert use.compiled is not None
        ca = next(c for c in preparation.contexts if c.context == use.request.context)
        assert ca.callback is not None and len(donors) == 2
        assert use.lock is not None
        evaluation = use.lock.evaluation_for(use.compiled)
        if (
            use.lock.parent.decision != use.commitment
            or evaluation.root.root_id != preparation.root
            or evaluation.policy.policy_id != f"el.{use.request.request_id}"
        ):
            raise ValueError("restored use changed its authenticated prepared design")
        delivery = FrontierPulseDeliveryPort(
            use.compiled.implementation(ImplementationRole.DELIVERY),
            UndeliverableSession(),
            use.projection,
        )
        restored = RestoredRequest(
            use, delivery, finite_control_services(use.compiled.study, evaluation, delivery)
        )
        tape = pulse_tape(
            donors[0].requests,
            ca.callback,
            use.projection.pulse,
            float(use.projection.fixed_jacket_K),
        )
        owner = FrontierCommittedBranchOwner(
            preparation.root,
            f"{preparation.root}.{use.request.request_id}",
            ca.callback,
            donors[0].observations,
            donors[0].stages,
            tape,
            restored,
            publisher,
        )
        nominal, completed = acquire_with_progress(
            source,
            scenario,
            f"{use.request.request_id}.owner",
            WatchedPreparedTape(tape),
            1.0,
            partial(acquire, owner=owner),
            completed,
            progress,
        )
        calls, failures, data = 1, [], {}
        for field, value in native_window(donors[0], nominal, ca.callback, tape).items():
            data[f"v0_{field}"] = value
        if nominal.complete and owner.delivered and not owner.failed:
            refined, completed = acquire_with_progress(
                source,
                scenario,
                f"{use.request.request_id}.refined",
                TapeController(tape),
                0.5,
                acquire,
                completed,
                progress,
            )
            calls += 1
            for field, value in native_window(donors[1], refined, ca.callback, tape).items():
                data[f"v1_{field}"] = value
            if not refined.complete:
                failures.append(refined.failure or "INCOMPLETE_REFINED_REPLAY")
        else:
            failures.append(nominal.failure or "INCOMPLETE_OWNER_DELIVERY")
        uses.append(
            _science_FrontierNativeUse(
                use.request,
                LocalArrayPayload.pack(data),
                owner.tick,
                tuple(delivery.last_deliveries),
                calls,
                tuple(failures),
            )
        )
    base = completed
    assay = acquire_assay(
        source,
        preparation,
        private,
        frozen.prediction_seal,
        acquire=acquire,
        progress=None if progress is None else lambda value: progress(base + value),
    )
    return _science_FrontierNativeRoot(
        preparation.root, ObjectIdentity.from_record(frozen.record_id, frozen), tuple(uses), assay
    )
