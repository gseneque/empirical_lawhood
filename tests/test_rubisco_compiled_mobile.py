# SPDX-License-Identifier: MPL-2.0
"""Selected-library input guards; actual force controls run in the native engine."""
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

import pytest

from tests import test_rubisco_geometry_repair as repair_controls
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import FileEvidence
from empirical_lawhood.adapters.rubisco.rubisco_response.compiled_mobile_nonbonded import CompiledMobileNonbonded
from empirical_lawhood.domains.rubisco.rubisco_response import construction_engine as repair
from empirical_lawhood.adapters.rubisco.rubisco_response.construction_engine import authenticate_numeric_engine
from empirical_lawhood.science.records.decoding import decode_canonical_bytes


@pytest.mark.parametrize("parameters,moving,exclusions",(
    ([[.1,.3,.2]],(),()),
    ([[.1,.3,.2]],(0,0),()),
    ([[.1,.3,.2]],(.5,),()),
    ([[.1,.3,.2]],(True,),()),
    ([[.1,-.3,.2]],(0,),()),
    ([[float('nan'),.3,.2]],(0,),()),
    ([[.1,.3,.2]],(0,),((0,0),)),
    ([[.1,.3,.2]],(0,),((0,1),)),
    ([[.1,.3,.2],[.2,.3,.2]],(0,),((0,1),(1,0))),
    ([[.1,.3,.2],[.2,.3,.2]],(0,),((0,1.5),)),
))
def test_malformed_pair_census_refuses_before_any_library_load(parameters,moving,exclusions,tmp_path):
    with pytest.raises(ValueError):
        CompiledMobileNonbonded(parameters,moving,exclusions,library=tmp_path/'never-loaded.so')


def test_optional_compiled_closure_authenticates_all_selected_members(tmp_path):
    original=repair_controls.numeric_engine(tmp_path)
    raw=original.canonical_bytes()
    assert not original.compiled_mobile
    assert decode_canonical_bytes(raw,repair.GpRepairNumericEngine,maximum_bytes=2**20).canonical_bytes()==raw
    directory=tmp_path/repair.COMPILED_PACKAGE;directory.mkdir()
    code=Path(repair.__file__).with_name('mobile_pairs.c').read_bytes()
    binary=b'EXPOSED NOT EXECUTABLE LIBRARY CONTROL\n'
    (directory/'mobile_pairs.c').write_bytes(code)
    (directory/'lib_mobile_pairs.so').write_bytes(binary)
    (directory/'build.json').write_text(json.dumps(dict(exit_code=0,source_sha256=sha256(code).hexdigest(),library_sha256=sha256(binary).hexdigest())))
    extra=tuple(FileEvidence(p.relative_to(tmp_path).as_posix(),p.stat().st_size,sha256(p.read_bytes()).hexdigest())
                for p in sorted(directory.iterdir()))
    selected=replace(original,files=tuple(sorted((*original.files,*extra),key=lambda row:row.relative_path)))
    assert selected.compiled_mobile
    authenticate_numeric_engine(selected)
    with pytest.raises(ValueError,match="complete source"):
        replace(selected,files=tuple(row for row in selected.files if row.relative_path!=repair.COMPILED_PACKAGE+'/build.json'))
    (directory/'lib_mobile_pairs.so').write_bytes(b'changed')
    with pytest.raises(ValueError):authenticate_numeric_engine(selected)


def test_compiled_build_record_cannot_claim_a_different_source_or_binary(tmp_path):
    original=repair_controls.numeric_engine(tmp_path)
    directory=tmp_path/repair.COMPILED_PACKAGE;directory.mkdir()
    (directory/'mobile_pairs.c').write_bytes(Path(repair.__file__).with_name('mobile_pairs.c').read_bytes())
    (directory/'lib_mobile_pairs.so').write_bytes(b'EXPOSED NOT EXECUTABLE')
    (directory/'build.json').write_text(json.dumps(dict(exit_code=0,source_sha256='0'*64,library_sha256='0'*64)))
    extra=tuple(FileEvidence(p.relative_to(tmp_path).as_posix(),p.stat().st_size,sha256(p.read_bytes()).hexdigest())
                for p in sorted(directory.iterdir()))
    selected=replace(original,files=tuple(sorted((*original.files,*extra),key=lambda row:row.relative_path)))
    with pytest.raises(ValueError,match="successful build binding"):authenticate_numeric_engine(selected)
