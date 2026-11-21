"""Native acquisition and external-format binding for the domain science."""

from __future__ import annotations
from decimal import Decimal
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import re
import struct
import tarfile
import numpy as np
from empirical_lawhood.domains.materials.superconductivity.material_source_design_design import build_material_roster
from empirical_lawhood.domains.materials.superconductivity.material_response_reduction import WannierHopping
from empirical_lawhood.domains.materials.superconductivity.workflow_contracts import MaterialControlWorkflowProfile

from empirical_lawhood.domains.materials.superconductivity.material_operand_assessment import (
    FineShellPoint as _science_FineShellPoint,
    MAXIMUM_MEMBER_BYTES as _science_MAXIMUM_MEMBER_BYTES,
    MaterialOperandReduction as _science_MaterialOperandReduction,
    PositionOperand as _science_PositionOperand,
    RYDBERG_TO_EV as _science_RYDBERG_TO_EV,
    RealMatrix as _science_RealMatrix,
    WannierHamiltonianOperand as _science_WannierHamiltonianOperand,
    _anisotropic_slices,
    _isotropic_slices,
    assess_material_operands as _science_assess_material_operands,
)

def _archive_members(path: Path) -> dict[str, bytes]:
    if not path.is_file() or path.is_symlink():
        raise ValueError('material-gauge covariant response raw archive is unavailable')
    result: dict[str, bytes] = {}
    with tarfile.open(path, mode="r:gz") as archive:
        for member in archive:
            if not member.isfile() or member.issym() or member.islnk():
                continue
            if member.size > _science_MAXIMUM_MEMBER_BYTES:
                raise ValueError('material-gauge covariant response raw member exceeds its bound')
            name = member.name
            if not (
                name.endswith(("_hr.dat", "_r.dat", ".wout"))
                or "/egnv" in name
                or ".imag_iso_" in name
                or ".imag_aniso_" in name
                or name.endswith(".phdos")
                or "matdyn.stdout" in name
            ):
                continue
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError('material-gauge covariant response raw member cannot be read')
            payload = stream.read(member.size + 1)
            if len(payload) != member.size:
                raise ValueError('material-gauge covariant response raw member size differs')
            result[name] = payload
    return result


def _one_member(members: dict[str, bytes], suffix: str) -> tuple[str, bytes]:
    values = tuple((name, payload) for name, payload in members.items() if name.endswith(suffix))
    if len(values) != 1:
        raise ValueError(f'material-gauge covariant response archive requires exactly one {suffix} member')
    return values[0]


def parse_wannier_hr(payload: bytes) -> _science_WannierHamiltonianOperand:
    lines = payload.decode("ascii").splitlines()
    if len(lines) < 4:
        raise ValueError("Wannier HR payload is truncated")
    orbital_count = int(lines[1].strip())
    translation_count = int(lines[2].strip())
    if orbital_count < 2 or translation_count <= 0:
        raise ValueError("Wannier HR dimensions are invalid")
    cursor = 3
    degeneracies: list[int] = []
    while len(degeneracies) < translation_count:
        degeneracies.extend(int(value) for value in lines[cursor].split())
        cursor += 1
    if len(degeneracies) != translation_count or any(value <= 0 for value in degeneracies):
        raise ValueError("Wannier HR degeneracies are invalid")
    expected = translation_count * orbital_count * orbital_count
    data = lines[cursor:]
    if len(data) != expected:
        raise ValueError("Wannier HR matrix row count differs")
    hoppings: list[WannierHopping] = []
    block = orbital_count * orbital_count
    for index, line in enumerate(data):
        fields = line.split()
        if len(fields) != 7:
            raise ValueError("Wannier HR row shape differs")
        degeneracy = degeneracies[index // block]
        hoppings.append(
            WannierHopping(
                translation=(int(fields[0]), int(fields[1]), int(fields[2])),
                source_orbital=int(fields[3]) - 1,
                target_orbital=int(fields[4]) - 1,
                real_eV=float(fields[5]) / degeneracy,
                imag_eV=float(fields[6]) / degeneracy,
            )
        )
    return _science_WannierHamiltonianOperand(
        payload_sha256=sha256(payload).hexdigest(),
        orbital_count=orbital_count,
        hoppings=tuple(hoppings),
    )


def parse_wannier_position(
    payload: bytes,
    *,
    orbital_count: int,
    lattice_vectors_A: _science_RealMatrix,
) -> _science_PositionOperand:
    lines = payload.decode("ascii").splitlines()
    if len(lines) < 4 or int(lines[1]) != orbital_count:
        raise ValueError("Wannier position operand orbital count differs")
    translation_count = int(lines[2])
    rows = lines[3:]
    if len(rows) != translation_count * orbital_count * orbital_count:
        raise ValueError("Wannier position row count differs")
    centres_A = np.zeros((orbital_count, 3), dtype=np.float64)
    offdiagonal_norm_sq = 0.0
    for line in rows:
        fields = line.split()
        if len(fields) != 11:
            raise ValueError("Wannier position row shape differs")
        translation = tuple(int(value) for value in fields[:3])
        source = int(fields[3]) - 1
        target = int(fields[4]) - 1
        vector = np.asarray(
            [
                complex(float(fields[5 + 2 * axis]), float(fields[6 + 2 * axis]))
                for axis in range(3)
            ],
            dtype=np.complex128,
        )
        if translation == (0, 0, 0) and source == target:
            centres_A[source] = vector.real
        else:
            offdiagonal_norm_sq += float(np.vdot(vector, vector).real)
    inverse = np.linalg.inv(lattice_vectors_A.T)
    reduced_values = tuple(inverse @ centre for centre in centres_A)
    reduced = tuple(
        (
            float(value[0] % 1.0),
            float(value[1] % 1.0),
            float(value[2] % 1.0),
        )
        for value in reduced_values
    )
    characteristic_A = float(min(np.linalg.norm(value) for value in lattice_vectors_A))
    relative = (offdiagonal_norm_sq**0.5) / max(characteristic_A, 1.0e-15)
    return _science_PositionOperand(
        payload_sha256=sha256(payload).hexdigest(),
        orbital_centres_reduced=reduced,
        offdiagonal_relative_upper=relative,
    )


def parse_epw_egnv(payload: bytes) -> tuple[_science_FineShellPoint, ...]:
    """Decode EPW 6.1's little-endian direct-access stream operand."""

    stream = BytesIO(payload)

    def unpack(format_: str) -> tuple[int | float, ...]:
        size = struct.calcsize(format_)
        block = stream.read(size)
        if len(block) != size:
            raise ValueError("EPW egnv stream is truncated")
        return struct.unpack(format_, block)

    nkftot, _nk1, _nk2, _nk3, nks = (int(value) for value in unpack("<5i"))
    header = unpack("<i5d")
    band_count = int(header[0])
    # EPW writes ``ef0`` and the following eigenvalues in Rydberg.  Its reader
    # converts both to eV only after reopening this stream; do the same before
    # comparing them with the Wannier Hamiltonian, whose native unit is eV.
    reference_energy_eV = float(header[2]) * _science_RYDBERG_TO_EV
    if nkftot <= 0 or nks <= 0 or band_count < 2:
        raise ValueError("EPW egnv dimensions are invalid")
    points: list[tuple[int, _science_FineShellPoint]] = []
    for _index in range(nkftot):
        row = unpack("<4d2i")
        coordinates = (float(row[1]), float(row[2]), float(row[3]))
        shell_index = int(row[5])
        energies = tuple(
            float(unpack("<d")[0]) * _science_RYDBERG_TO_EV - reference_energy_eV for _ in range(band_count)
        )
        if shell_index > 0:
            points.append(
                (
                    shell_index,
                    _science_FineShellPoint(
                        reduced_k=coordinates,
                        energies_eV=energies,
                        reference_energy_eV=reference_energy_eV,
                    ),
                )
            )
    if stream.read(1) or len(points) != nks:
        raise ValueError("EPW egnv shell count or stream length differs")
    points.sort(key=lambda value: value[0])
    if tuple(index for index, _value in points) != tuple(range(1, nks + 1)):
        raise ValueError("EPW egnv shell indices are not contiguous")
    return tuple(value for _index, value in points)


def _numeric_rows(payload: bytes) -> tuple[tuple[float, ...], ...]:
    rows: list[tuple[float, ...]] = []
    for line in payload.splitlines():
        if not line.strip() or line.lstrip().startswith((b"#", b"!")):
            continue
        try:
            row = tuple(float(value.replace(b"D", b"E")) for value in line.split())
        except ValueError:
            continue
        if row:
            rows.append(row)
    return tuple(rows)


def _temperature_from_member(name: str) -> float | None:
    match = re.search(r"_([0-9]+(?:\.[0-9]+)?)$", name)
    return None if match is None else float(match.group(1))


def _select_gap_member(
    members: dict[str, bytes], *, prefix: str, temperature_K: float, anisotropic: bool
) -> tuple[str, bytes]:
    marker = f"{prefix}.imag_{('aniso' if anisotropic else 'iso')}_"
    candidates = tuple(
        (name, payload)
        for name, payload in members.items()
        if marker in name and "gap0" not in name
    )
    matching = tuple(
        value
        for value in candidates
        if (temperature := _temperature_from_member(value[0])) is not None
        and abs(temperature - temperature_K) < 1.0e-6
    )
    if len(matching) != 1:
        raise ValueError('material-gauge covariant response archive lacks its exact control-temperature gap member')
    return matching[0]


def _max_phonon_eV(members: dict[str, bytes]) -> float | None:
    pattern = re.compile(
        rb"freq\s*\([^)]*\)\s*=\s*[-+0-9.EeDd]+\s*\[THz\]\s*=\s*"
        rb"([-+0-9.EeDd]+)\s*\[cm-1\]",
        re.IGNORECASE,
    )
    values: list[float] = []
    for name, payload in members.items():
        if "matdyn.stdout" not in name:
            continue
        values.extend(abs(float(value.replace(b"D", b"E"))) for value in pattern.findall(payload))
    return None if not values else max(values) * 1.239_841_984e-4


def reduce_material_operands(
    *,
    raw_archive_path: Path,
    profile: MaterialControlWorkflowProfile,
    fermi_energy_eV: Decimal,
    electron_phonon_lambda: Decimal,
) -> _science_MaterialOperandReduction:
    if profile.structure_id not in {'structure.calibration-pb-fcc', 'structure.calibration-mgb2-alb2'}:
        raise ValueError('material-gauge covariant response reduction is reserved for positive controls')
    members = _archive_members(raw_archive_path)
    _hr_name, hr_payload = _one_member(members, f'{profile.prefix}_hr.dat')
    _position_name, position_payload = _one_member(members, f'{profile.prefix}_r.dat')
    hamiltonian = parse_wannier_hr(hr_payload)
    structure = next(
        value
        for value in build_material_roster().structures
        if value.structure_id == profile.structure_id
    )
    lattice = np.asarray(
        [[float(component) for component in vector] for vector in structure.lattice_vectors_A],
        dtype=np.float64,
    )
    position = parse_wannier_position(
        position_payload,
        orbital_count=hamiltonian.orbital_count,
        lattice_vectors_A=lattice,
    )
    is_mgb2 = profile.structure_id == 'structure.calibration-mgb2-alb2'
    temperature_K = 20.0 if is_mgb2 else 4.0
    gap_name, gap_payload = _select_gap_member(
        members,
        prefix=profile.prefix,
        temperature_K=temperature_K,
        anisotropic=is_mgb2,
    )
    projection_residual = 0.0
    energy_alignment_residual = 0.0
    material_fermi_eV = float(fermi_energy_eV)
    if is_mgb2:
        egnv_values = tuple(payload for name, payload in members.items() if name.endswith("/egnv"))
        if len(egnv_values) != 1:
            raise ValueError('anisotropic material-gauge covariant response reduction requires one egnv operand')
        shell = parse_epw_egnv(egnv_values[0])
        material_fermi_eV = shell[0].reference_energy_eV
        slices, projection_residual, energy_alignment_residual = _anisotropic_slices(
            _numeric_rows(gap_payload),
            hamiltonian=hamiltonian,
            shell=shell,
        )
    else:
        slices, projection_residual = _isotropic_slices(
            _numeric_rows(gap_payload),
            orbital_count=hamiltonian.orbital_count,
        )
    return _science_assess_material_operands(
        profile=profile,
        hamiltonian=hamiltonian,
        position=position,
        lattice=lattice,
        slices=slices,
        projection_residual=projection_residual,
        energy_alignment_residual=energy_alignment_residual,
        material_fermi_eV=material_fermi_eV,
        maximum_phonon_eV=_max_phonon_eV(members),
        electron_phonon_lambda=electron_phonon_lambda,
        temperature_K=temperature_K,
        gap_payload=gap_payload,
    )
