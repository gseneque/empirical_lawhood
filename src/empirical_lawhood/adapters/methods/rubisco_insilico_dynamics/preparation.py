# SPDX-License-Identifier: MPL-2.0
"""Pure, explicit parameter derivation; no coordinate or native construction."""

from hashlib import sha256
from itertools import product
import re

from . import contracts as c


def _prepi_rows(text):
    rows = []
    in_atoms = False
    for line in text.splitlines(keepends=True):
        tokens = tuple(re.finditer(r"\S+", line))
        if len(tokens) >= 2 and tokens[1].group() == "INT":
            in_atoms = True
            continue
        if in_atoms and line.strip() in ("LOOP", "IMPROPER", "DONE", "STOP"):
            in_atoms = False
        if in_atoms and tokens and tokens[0].group().isdigit():
            if len(tokens) != 11:
                raise ValueError("invalid selected Amber prepi atom row")
            rows.append((line, tokens))
    if not rows:
        raise ValueError("empty selected Amber prepi")
    return rows


def scoped_kcx_stock(prepi, frcmod, *, existing_atom_types):
    """Rename only custom KCX types, preserving every original non-type token.

    This custom stock still requires separately copied/authenticated boundary
    terms. It is not by itself a complete native force field.
    """
    aliases = dict(c.KCX_ALIASES)
    if set(aliases.values()) & set(existing_atom_types):
        raise ValueError("KCX alias collides with an existing native atom type")
    found = set()
    charges = []
    output = []
    atom_lines = {line: tokens for line, tokens in _prepi_rows(prepi)}
    for line in prepi.splitlines(keepends=True):
        if line not in atom_lines:
            output.append(line)
            continue
        tokens = atom_lines[line]
        typ = tokens[2].group()
        if typ == "DU":
            output.append(line)
            continue
        if typ not in aliases:
            raise ValueError("KCX stock includes an undeclared atom type")
        found.add(typ)
        charges.append((tokens[1].group(), tokens[10].group()))
        token = tokens[2]
        output.append(line[: token.start()] + aliases[typ] + line[token.end() :])
    if found != set(aliases) or len({name for name, _ in charges}) != len(charges):
        raise ValueError("KCX stock omits or duplicates the frozen atom inventory")

    # Amber's fixed-width type tuples keep atom names and numerical/comment
    # tokens intact. Blank lines do not end a frcmod section.
    sections = {
        "MASS": 1,
        "BOND": 2,
        "ANGLE": 3,
        "ANGL": 3,
        "DIHE": 4,
        "IMPROPER": 4,
        "IMPR": 4,
        "NONBON": 1,
        "NONB": 1,
    }
    section = None
    frc_output = []
    for line in frcmod.splitlines(keepends=True):
        stripped = line.strip()
        if stripped in sections:
            section = stripped
            frc_output.append(line)
        elif not stripped or section is None:
            frc_output.append(line)
        elif sections[section] == 1:
            tokens = tuple(re.finditer(r"\S+", line))
            typ = tokens[0].group()
            if typ not in aliases:
                raise ValueError("KCX frcmod includes an undeclared atom type")
            t = tokens[0]
            frc_output.append(line[: t.start()] + aliases[typ] + line[t.end() :])
        else:
            count = sections[section]
            width = 3 * count - 1
            types = tuple(x.strip() for x in line[:width].split("-"))
            if len(types) != count or any(x not in aliases for x in types):
                raise ValueError("KCX frcmod type tuple is incomplete or undeclared")
            frc_output.append("-".join(aliases[x] for x in types) + line[width:])
    return c.DerivedParameterStock(
        sha256(prepi.encode()).hexdigest(),
        sha256(frcmod.encode()).hexdigest(),
        c.KCX_ALIASES,
        "".join(output),
        "".join(frc_output),
        tuple(charges),
    )


def _frcmod_sections(text):
    """Read type-bearing original lines without fitting or rounding numbers."""
    names = {
        "MASS": "MASS",
        "BOND": "BOND",
        "ANGL": "ANGLE",
        "ANGLE": "ANGLE",
        "DIHE": "DIHE",
        "IMPROPER": "IMPROPER",
        "IMPR": "IMPROPER",
        "NONB": "NONBON",
        "NONBON": "NONBON",
    }
    sections = {
        name: [] for name in ("MASS", "BOND", "ANGLE", "DIHE", "IMPROPER", "NONBON")
    }
    section = None
    for line in text.splitlines(keepends=True)[1:]:
        stripped = line.strip()
        if stripped in names:
            section = names[stripped]
        elif stripped:
            if section is None:
                raise ValueError("unsupported selected frcmod layout")
            sections[section].append(line)
    return sections


def _parm_dat_sections(text):
    """Read the selected Amber parm.dat blocks, including LJ equivalence.

    The selected source has no nonzero 10-12 or LJEDIT potentials. An unfamiliar
    layout refuses rather than manufacturing a missing force-field term.
    """
    lines = text.splitlines(keepends=True)
    index = 1

    def block():
        nonlocal index
        rows = []
        while index < len(lines) and lines[index].strip():
            rows.append(lines[index])
            index += 1
        index += 1
        return rows

    sections = {"MASS": block()}
    if index >= len(lines):
        raise ValueError("truncated Amber parameter source")
    index += 1  # Source hydrophobic-type census, not force-field coefficients.
    for name in ("BOND", "ANGLE", "DIHE", "IMPROPER"):
        sections[name] = block()
    if block():
        raise ValueError("selected boundary stock has unsupported 10-12 terms")
    equivalences = block()
    if index >= len(lines) or lines[index].split() != ["MOD4", "RE"]:
        raise ValueError("selected Amber source lacks explicit RE nonbonded convention")
    index += 1
    sections["NONBON"] = block()
    if any(line.strip() not in ("", "END") for line in lines[index:]):
        raise ValueError("unsupported trailing Amber parameter source")
    nonbonded = {line.split()[0]: line for line in sections["NONBON"]}
    for line in equivalences:
        types = line.split()
        if not types or types[0] not in nonbonded:
            raise ValueError("unresolved source nonbonded equivalence")
        original = nonbonded[types[0]]
        token = next(re.finditer(r"\S+", original))
        for typ in types[1:]:
            if typ not in nonbonded:
                nonbonded[typ] = (
                    original[: token.start()] + typ + original[token.end() :]
                )
    sections["NONBON"] = list(nonbonded.values())
    return sections


def scoped_boundary_stock(parm_dat, ff14sb_frcmod):
    """Copy authenticated baseline terms into new KCX type names only.

    Every nonempty subset of eligible positions is copied, so a peptide crossing
    the residue boundary keeps its ordinary standard parameters. Original
    numerical/comment tokens and multi-periodic torsion continuation signs are
    retained. Load this stock before the renamed custom KCX frcmod. No all-
    standard tuple is emitted, hence this derivation cannot globally override
    the standard protein model.
    """
    aliases = dict(c.KCX_ALIASES)
    sources = (_parm_dat_sections(parm_dat), _frcmod_sections(ff14sb_frcmod))
    existing = {line.split()[0] for source in sources for line in source["MASS"]}
    if not set(aliases).issubset(existing) or set(aliases.values()) & existing:
        raise ValueError("missing baseline type or colliding KCX alias")
    output = ["Source-derived KCX boundary aliases; standard tuples unchanged\n"]
    census = []
    for section, count in (
        ("MASS", 1),
        ("BOND", 2),
        ("ANGLE", 3),
        ("DIHE", 4),
        ("IMPROPER", 4),
        ("NONBON", 1),
    ):
        output.extend((section + "\n",))
        copied = 0
        for source in sources:
            groups = _bonded_line_groups(source[section], section)
            for lines in groups:
                line = lines[0]
                if count == 1:
                    token = next(re.finditer(r"\S+", line))
                    typ = token.group()
                    if typ in aliases:
                        output.append(
                            line[: token.start()] + aliases[typ] + line[token.end() :]
                        )
                        copied += 1
                    continue
                width = 3 * count - 1
                types = tuple(x.strip() for x in line[:width].split("-"))
                if len(types) != count or any(not x for x in types):
                    raise ValueError("invalid authenticated boundary type tuple")
                choices = tuple(
                    (typ, aliases[typ]) if typ in aliases else (typ,) for typ in types
                )
                for renamed in product(*choices):
                    if renamed != types:
                        for term in lines:
                            output.append(
                                "-".join(f"{typ:<2}" for typ in renamed) + term[width:]
                            )
                            copied += 1
        output.append("\n")
        census.append((section, copied))
    if any(not count for _, count in census):
        raise ValueError("derived boundary stock omits a parameter category")
    return c.BoundaryParameterStock(
        sha256(parm_dat.encode()).hexdigest(),
        sha256(ff14sb_frcmod.encode()).hexdigest(),
        c.KCX_ALIASES,
        "".join(output),
        tuple(census),
    )


def _bonded_line_groups(lines, section):
    """Keep Amber's signed multi-periodic torsion continuation contiguous."""
    if section != "DIHE":
        return tuple((line,) for line in lines)
    groups = []
    group = []
    for line in lines:
        if group and line[:11] != group[0][:11]:
            raise ValueError("source torsion continuation changes its type tuple")
        group.append(line)
        try:
            continues = float(line[11:].split()[3]) < 0
        except (ValueError, IndexError) as error:
            raise ValueError(
                "source torsion has invalid periodicity declaration"
            ) from error
        if not continues:
            groups.append(tuple(group))
            group = []
    if group:
        raise ValueError("truncated source multi-periodic torsion")
    return tuple(groups)


def controlled_constructs(*, gp_lsu, gp_ssu_m1, gp_ssu_v1, te_lsu, te_ssu):
    """Construct the exact full six-material roster from authenticated sequences."""
    if tuple(map(len, (gp_lsu, gp_ssu_m1, gp_ssu_v1, te_lsu, te_ssu))) != (
        493,
        138,
        138,
        475,
        118,
    ):
        raise ValueError("original controlled sequences are incomplete")
    if gp_ssu_m1 != "M" + gp_ssu_v1[1:] or gp_ssu_v1[0] != "V":
        raise ValueError("M1/V1 alternatives alter another residue or numbering")
    if gp_ssu_m1[94] != "I" or te_lsu[414] != "P" or te_ssu[97] != "V":
        raise ValueError("original source does not contain the selected intervention")
    donor = te_lsu[:414] + "A" + te_lsu[415:]
    rows = [
        c.Construct(
            "gp.i95m.m1", gp_lsu, gp_ssu_m1[:94] + "M" + gp_ssu_m1[95:], (), (95,)
        ),
        c.Construct(
            "gp.i95m.v1", gp_lsu, gp_ssu_v1[:94] + "M" + gp_ssu_v1[95:], (), (95,)
        ),
        c.Construct("gp.wt.m1", gp_lsu, gp_ssu_m1, (), ()),
        c.Construct("gp.wt.v1", gp_lsu, gp_ssu_v1, (), ()),
        c.Construct(
            "te.p415a.v98m", donor, te_ssu[:97] + "M" + te_ssu[98:], (415,), (98,)
        ),
        c.Construct("te.p415a.wt-ssu", donor, te_ssu, (415,), ()),
    ]
    return tuple(rows)


def validate_controlled_constructs(rows, originals):
    """A full regenerated comparison forbids an unnoticed second intervention."""
    expected = controlled_constructs(**originals)
    if rows != expected:
        raise ValueError("controlled material roster substitutes a source/background")
    return rows
