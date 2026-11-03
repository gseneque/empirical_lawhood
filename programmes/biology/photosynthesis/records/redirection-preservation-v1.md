# Minimal redirection preservation inventory v1

SPDX-License-Identifier: CC-BY-4.0

The supplied files are in [`preservation/redirection-v1`](preservation/redirection-v1).
The original capture used that directory under the maintainer's checkout.
This is a durable **partial source/ordinary-metadata handoff**, not an installable
checkout, native environment or authentic evidence replica. Originals remain
primary; copied audit observations do not acquire new receipt authority.
See the [bounded result](redirection-result-v1.md) and
[decision](redirection-decision-v1.md).
The [completion record](preservation/redirection-v1/completion.json) gives the
elapsed engineering scope, retained output census, checks and unknown tails.

## Written selection and byte verification

The [source/metadata ZIP](preservation/redirection-v1/source-metadata.zip) has
**96 members / 5,705,316 expanded bytes / 1,080,339 stored bytes**, SHA256
`23a5b28b35ec8260d4780d388f245a6872f3e4d1c536df94f47bf6f54b5c7a78`.
The [complete member index](preservation/redirection-v1/member-index.json)
is **31,991 bytes**, SHA256
`338bd82e08919a1dc6786d051ba51608e5c338d955b81e9ebb48389488508c44`.
Every member has its original absolute locator, byte count and SHA256; archive
CRC and all expanded member hashes passed. Files are read-only. ZIP bytecode
members preserve historical data only and must not be executed or used as
native source guards.

| Selected content | Original owner / current state |
|---|---|
| Pure coupled-return encoder and portable tests | EL adapter/test snapshots, untracked at the original capture; 9,399/6,284 bytes. This is historical capture status, not the current checkout status. |
| Prospective assessment, integration tests, exact diff and implementation handoff | Complete seven-file `/tmp/rubisco-qmmm-redirection-v1` snapshot; unfrozen software without native authority. |
| Complete R1 provenance study | All 35 files from `/tmp/rubisco-redirection-provenance-v1`, including original refusals, exact producing parent sources, complete source census, main/supplement observations and closure register. |
| Both complete closed v3 audits | All 23 custody-audit files and all ten scientific-audit files; negative checker outcomes and original bytecode data retained. |
| Selected maintained electronic/preparation/embedding owners | Exact current `rr_qmmm_xtb.py`, `rr_xtb_repair.py`, `rr_coupled_preparation.py`, `rr_coupled_embedding.py`; source snapshots, not retroactive producers of old records. |
| Locked environment specification | Exact current `pyproject.toml` and `uv.lock`; no sync/install occurred. |
| Historical source-bound helpers/config/profile | Exact native coupling, old assessment, bounded executor, custody bridge, source guard, geometry assessor, C4 owner, v3 launcher/worker/config, v3b config builder, source-profile manifest and v3b scientific protocol. Config-bound sources are checked against their frozen bindings before copying. |

The expanded selection is a partial dependency graph. It does not include
all EL packages, native libraries, source packets, topology/held geometry or
receipt ancestry. Neither the dirty checkout observed at capture nor these copies
replace sealed producing snapshots. Original v8/v11 helpers, v3b protocol and
all historical packets were left untouched.

Run this command from the selected checkout root.
It verifies the archive without extracting files or entering native science:

```bash
python - <<'PY'
from pathlib import Path
from hashlib import sha256
import json
from zipfile import ZipFile
root = Path.cwd() / 'programmes/biology/photosynthesis/records/preservation/redirection-v1'
index_raw = (root / 'member-index.json').read_bytes()
assert sha256(index_raw).hexdigest() == '338bd82e08919a1dc6786d051ba51608e5c338d955b81e9ebb48389488508c44'
index = json.loads(index_raw)
raw = (root / 'source-metadata.zip').read_bytes()
assert len(raw) == index['archive']['bytes']
assert sha256(raw).hexdigest() == index['archive']['sha256']
with ZipFile(root / 'source-metadata.zip') as archive:
    assert archive.testzip() is None
    assert sorted(archive.namelist()) == sorted(r['member'] for r in index['members'])
    for row in index['members']:
        value = archive.read(row['member'])
        assert len(value) == row['bytes']
        assert sha256(value).hexdigest() == row['sha256']
print('96 selected source/metadata members verified; no native execution')
PY
```

Archived README files and protocols retain their original locators and relative links.
Resolve their documentary links through the main [Rubisco index](progress.md#availability-of-historical-procedures) and the member index.
Do not rewrite archive members to match a new host.

## Dependencies still outside this handoff

| Required retained dependency | Explicit locator and identity / resource |
|---|---|
| Primary v3 packet and receipt ancestry | `/tmp/empirical-lawhood-rubisco-20261009/retained-execution/rr-qmmm-retained-reference-v3`: 177 files / 89,852,484 bytes; census SHA256 `92c6c63cc5dad115cdf2e8e34cd129e82bc6cad2fd4ab006370201a3c5efaaa3`. Actual 25 publications and eleven ancestor packets remain required. |
| Native prepared topology and witness | Preparation-v2 packet under the same `retained-execution` root. `reference-v2-derived.prmtop`: 5,967,591 bytes, SHA256 `adc479e815481d4174024c28eb1f27ce85ea67bd5af0a646a34bb92982280fcd`; reload witness 738,709 bytes, SHA256 `1e8c487557fb43d480bc5aff0320d88203aa23aef8f7e6758dddc63081b06d25`. |
| Held reactive context and ordered source plan | `/tmp/rubisco-xtb-inputs-software-v1b/initial-contexts/unedited-reference.v2.json`: 3,065,848 bytes, SHA256 `fbb6858ccb92685c2f0d7d07dd8e819d0c837fd3a8e4c41033327df3f259406c`; v8 ordered plan and bounded parts remain in the authentic v8 packet. Whole plan: 19,041,817 bytes, SHA256 `a2540a4dab133d7931d6bfc73e0da2c38e3f3b6c6e72b3894ed0122cd5fcd90e`. |
| Original Amber completion and archived relaxed coordinates | Canonical parent native envelope at `/media/chevre/SEMIOS/icf-yolo/programmes/rubisco-el/r02s-m1-pilot-v5/runs/rubisco-r02s-m1-native-v5.pilot.production/outputs/rubisco-r02s-m1-native-v5.native-protocol/native-result.canonical.json`: 55,092,530 bytes, SHA256 `8dbc9e528e341cee554128bcedc9876f2f3141c2e4b62a22b737f9b5bcef855a`. Embedded archive: 41,295,643 bytes, SHA256 `a22c4fb687e88ff36d92d06378f3b3176b565fd1281b83cccad52454b0f1a653`, 42 members / 180,758,177 expanded bytes. The R1 copied archive census records each relaxed member's exact hash. |
| Original selected source core | `/tmp/empirical-lawhood-rubisco-20261009/public-inputs/followup-rr-amber-core-v1`: 44 files / 13,788,149 bytes. The copied R1 observations bind all members; a relaxed-coordinate successor must have a new source/preparation identity. |
| Parent locked native interpreter and installed source profile | `/home/chevre/gs-ml/icf-yolo/.venv/bin/python`; copied profile SHA256 `0a6af7677efb3c2f6b3b13b655bb6814684e48acf7b58c4a5f02a204acabaafa` describes 7,078 declared entries / 490,843,698 bytes. The manifest is preserved, the environment bytes are not. Cache/source-import and system-library rules remain dependencies. |
| Actual xTB executable and parameters | `/tmp/rubisco-xtb-6.7.1-native-env/native/bin/xtb`: 63,253,248 bytes, SHA256 `debf27a9e0fa4bfb5ca75aafe4b90d8211f08ec2f4a482f375a4987212eaa12a`; parameters at its `native/share/xtb/param_gfn2-xtb.txt`: 35,849 bytes, SHA256 `f6f05c6c5264cb2f75c54f8ac6838044541c1e493b16f1a4d4ee4fa64de5f545`. The actual frozen config uses `param_gfn2-xtb.txt` with its retained spelling; use the indexed config locator. |

All absolute locators require explicit successor rebinding and byte validation
on a future host; use the preserved config's exact parameter locator. The copied private
tests still select their original `/tmp` helper locator; moving them requires
a reviewed loader change or intentional original-path materialization.
Software tests use the already selected electronic profile at
`/tmp/rubisco-electronic-20261010-env` with `uv run --no-sync`. No environment
reconstruction or native replay command is authorized by this inventory.

For broader durable custody, propose a separately allocated local evidence
root `/home/chevre/gs-ml/empirical_lawhood/.local/rubisco-evidence/native-v1`
with at least **1.5 GiB available**, copying the complete 38-root 787,643,240-byte
native/helper selection, its later audit roots, exact parent envelope and
profile-selected installed bytes with aliases/deduplication recorded. This is
an explicit future destination/resource proposal, not a selected copy, new
scientific allowance or promise of a portable environment. Retain the original
packets and receipts. The current two-hour/16 MiB engineering scope writes
only the minimal archive, index and current completion metadata; full bulky
preservation remains open.

The missing rejected v3 full return is permanently absent from this evidence.
Recovery cannot manufacture it or give exposed evidence a fresh label.
