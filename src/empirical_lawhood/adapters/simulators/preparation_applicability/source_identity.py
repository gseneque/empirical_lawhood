"""Reusable scientific records, designs and calculations extracted from native binding.

Native acquisition and external-format effects belong to the corresponding adapter.
Original scientific schemas and numerical definitions are preserved.
"""

from hashlib import sha256
from importlib.resources import files
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import canonical_json_bytes


NATIVE_SOURCE_PATHS = (
    "domains/matrix/preparation_applicability/words.py",
    "domains/matrix/preparation_applicability/phase_records.py",
    "domains/matrix/preparation_applicability/dynamics.py",
    "domains/matrix/constructed_preparation_applicability/phase_records.py",
    "domains/matrix/prepared_response/source.py",
    "domains/matrix/prepared_response/contracts.py",
    "domains/matrix/prepared_response/instruments.py",
    "domains/matrix/finite_response_law/instruments.py",
    "domains/matrix/finite_response_law/preparation_policy_instruments.py",
    "domains/matrix/finite_response_law/preparation_policy_contracts.py",
    "domains/matrix/six_matrix_response/model.py",
    "domains/matrix/six_matrix_response/passive_probe.py",
    "domains/matrix/six_matrix_response/response_observer.py",
)


def current_native_implementation():
    package=files("empirical_lawhood")
    entries=[]
    for path in NATIVE_SOURCE_PATHS:
        with package.joinpath(path).open("rb") as handle:
            raw=handle.read(2*1024**2+1)
        if len(raw)>2*1024**2:
            raise ValueError("native source owner exceeds its fixed scan bound")
        entries.append((path,len(raw),sha256(raw).hexdigest()))
    return ObjectIdentity("preparation-applicability.current-native-implementation",
        "empirical-lawhood/preparation-applicability/native-implementation","1.0.0",
        sha256(canonical_json_bytes(tuple(entries))).hexdigest())
