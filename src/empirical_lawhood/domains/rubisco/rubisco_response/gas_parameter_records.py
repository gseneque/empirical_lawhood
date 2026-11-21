# SPDX-License-Identifier: MPL-2.0
"""Complete operands for two source-selected gas parameter transformations."""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import FileEvidence
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.durable_preparation import file_chunks
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.domains.rubisco.rubisco_response.gas_amber_stock import GasAmberStock
from empirical_lawhood.domains.rubisco.rubisco_response.construction_engine import GpRepairNumericEngine
from empirical_lawhood.adapters.rubisco.rubisco_response.construction_engine import authenticate_numeric_engine
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact


MAX_SOURCE = 128*2**20
MAX_METADATA = 8*2**20
GASES = ('CO2', 'O2')


@dataclass(frozen=True, slots=True)
class GasParameterEngine(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/gas-parameter-engine'
    numeric: GpRepairNumericEngine
    parmed_files: tuple[FileEvidence, ...]

    def __post_init__(self):
        exact(self.numeric, GpRepairNumericEngine)
        if self.numeric.compiled_mobile:
            raise ValueError('gas parameter construction does not select the geometry-repair kernel')
        if (type(self.parmed_files) is not tuple or not self.parmed_files
                or tuple(row.relative_path for row in self.parmed_files)
                    != tuple(sorted({row.relative_path for row in self.parmed_files}))
                or any(not row.relative_path.startswith('parmed/') for row in self.parmed_files)):
            raise ValueError('gas parameter engine requires its complete selected ParmEd package')
        for row in self.parmed_files:
            exact(row, FileEvidence)

    @property
    def identity(self):
        return ObjectIdentity.from_record('engine.gas-parameters.'+self.fingerprint(), self)


def authenticate_gas_parameter_engine(engine, *, loaded=False):
    """Reuse the complete numerical stock owner and add the selected ParmEd files."""
    exact(engine, GasParameterEngine)
    authenticate_numeric_engine(engine.numeric)
    root = Path(engine.numeric.site_packages)
    directory = root/'parmed'
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError('gas parameter engine changes its selected ParmEd root')
    actual = []
    for path in directory.rglob('*'):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError('gas parameter engine contains an undeclared link or special file')
        if path.is_file():
            actual.append(path.relative_to(root).as_posix())
    if tuple(sorted(actual)) != tuple(row.relative_path for row in engine.parmed_files):
        raise ValueError('gas parameter engine changes its complete ParmEd file census')
    for row in engine.parmed_files:
        for _ in file_chunks(root/row.relative_path, expected=row):
            pass
    if loaded:
        from empirical_lawhood.adapters.rubisco.rubisco_insilico_dynamics.durable_native_entry import authenticate_loaded_engine_modules
        return authenticate_loaded_engine_modules({'entries': [dict(kind='file', actual_path=str(root/row.relative_path),
            size=row.byte_count, sha256=row.sha256) for row in (*engine.numeric.files, *engine.parmed_files)]})
    return ()


@dataclass(frozen=True, slots=True)
class GasParameterSource(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/gas-parameter-source'
    topology: ObjectIdentity
    topology_ascii: str
    stocks: tuple[GasAmberStock, ...]
    engine: GasParameterEngine

    def __post_init__(self):
        exact(self.topology, ObjectIdentity)
        exact(self.engine, GasParameterEngine)
        if (type(self.topology_ascii) is not str or not self.topology_ascii or not self.topology_ascii.isascii()
                or len(self.topology_ascii) > MAX_SOURCE
                or sha256(self.topology_ascii.encode('ascii')).hexdigest() != self.topology.object_fingerprint):
            raise ValueError('gas parameter source substitutes its complete original topology bytes')
        if type(self.stocks) is not tuple or tuple(row.gas for row in self.stocks) != GASES:
            raise ValueError('gas parameter source requires both complete source-selected gas alternatives')
        for stock in self.stocks:
            exact(stock, GasAmberStock)

    @property
    def identity(self):
        return ObjectIdentity.from_record('source.gas-parameters.'+self.fingerprint(), self)


def prepare_gas_parameter_source(*, topology, original_topology_bytes, stocks, engine):
    """Freeze exact operands without importing or calling a native library."""
    if type(original_topology_bytes) is not bytes:
        raise ValueError('gas parameter preparation requires the original topology bytes')
    return GasParameterSource(topology, original_topology_bytes.decode('ascii'), tuple(stocks), engine)
