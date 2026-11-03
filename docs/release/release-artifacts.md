# Select exact release artifacts

SPDX-License-Identifier: CC-BY-4.0

This guide gives the source-identity procedure for software artifacts and their evidence packet.
It provides the software evidence bound by the external release selection.
Use it to build, examine and select exact artifact bytes before owner review.

## Prerequisites and first action

Use the [tested environment](../using/environments.md) and the selected committed source.
During consolidation, empty Git status is not a prerequisite: disclose the local
plan and actual status separately, and verify the selected executable and input
bytes against their declared identities.
Complete any public-history collapse before selecting that commit for verification.
The packet must bind the exact root or other commit intended for delivery; a later squash, reword, amend or merge creates a different source identity.
Select a new absolute output directory outside the checkout.
Keep sufficient space for the fresh environments and full worked example.
The runner uses the selected checkout and discloses local plans separately.
No local work plan is a packaged prerequisite or an additional acceptance gate.
Select explicit packet, cache and environment destinations on suitable external storage.
Verify the actual mount, write access and capacity before substantial output.
The maintainer's EL selection is documented separately in the
[local storage guidance](../development/maintainer-environment.md#storage-and-retained-evidence).
Researchers select their own paths and storage profile.
Keep the selected checkout unchanged while source-bound scientific processes remain active.
Prepare documentation corrections in the external maintainer packet during those processes.
Apply and review them after the bound processes exit.
Regenerate affected references from their owners.
Run the documentation checks on the final candidate.

Settle the candidate and select the release's software and scientific evidence scope.
The portable gate verifies software conformance with exposed controls and an installed worked example.
Select additional native or held profiles only for the execution claims that require them.
Omitted profiles remain unverified for that candidate.
Software release acceptance creates no requirement to acquire replacement scientific cohorts.

A separately selected scientific programme retains its own complete design, assignments and eligibility rules.
Historical TRAIN or exposed fixtures cannot supply fresh evidence.
Use a documented [Matrix continuation](../../programmes/foundations/emergent-structure/workflows/matrix-programme/guide.md) when its exact prerequisites apply.
Preserve the original producing source and completed or uncertain contacts.
A changed implementation does not make retained observations fresh or license another acquisition.

After science, use the authenticated retained-data read and selected export without repeating native work.
Reuse accepted checks only where their exact source and scope remain applicable.
A changed candidate requires its affected checks and an exact final artifact binding.
After source settles and actual storage checks pass, run:

```sh
uv run --no-sync python scripts/release_check.py --profile portable --output-dir /path/to/new-release-packet
```

The output directory must not already exist.
If its filesystem does not support Python environment symlinks, add
`--environment-root /path/on-posix-filesystem/new-release-environments`.
This directory must be new and outside the source checkout and packet.
It holds the fresh environments and temporary files. The packet retains their paths.
Keep sufficient free space on both filesystems.
Use `--offline` only with a complete verified dependency and interpreter cache.
The [test profile guide](../development/testing.md) gives native and held prerequisites.
Select native profiles for each execution claim that requires them.
An absent selected prerequisite fails its profile.
The portable gate excludes historical custody inspections and C25/E6 native acquisition controls.
Record omitted profiles as unverified and limit release claims to accepted evidence.
Do not acquire replacement historical fixtures or additional scientific cohorts for a portable release.


## Bounded CI and explicit test partitions

The `ci` profile uses the same source, generator, documentation, artifact and installed-wheel owners.
Its test selector contains only the explicitly reviewed bounded modules.
It does not run or claim the complete portable critical-coverage gate.
The `integration` and `scale` profiles run their selected portable modules without distribution construction.
They support deterministic module shards through `--shard-index` and `--shard-count`.
Every shard requires its own new packet directory.
All profiles retain their software evidence limit and required-skip refusal.

Partitioned packets bind `test-selection.json` from the actual collection, including failed test runs.
The manifest and status state the profile, shard and evidence scope.
Require every shard of an explicitly selected profile with the same source and eligible census hash.
Do not interpret a bounded CI pass as complete portable coverage or scientific qualification.
The [test guide](../development/testing.md) gives commands and membership rules.
The [CI guide](../development/ci.md) gives hosted job selection and retention.

`--portable-evidence` remains exclusive to the complete `portable` profile.
Original full-suite results retain their exact source identity and outcome.
After a focused correction, bind affected checks separately; do not relabel an earlier failed gate as passed.

## What the runner produces

For a once-only precommit portable gate, settle and stage the intended source, then run `uv run --no-sync python scripts/release_candidate_check.py --output-dir /absolute/new-candidate-packet`. It records actual loaded bytes and executable modes, the staged tree, exact environment, one complete portable selection with required-skip checks, sealed logs and coverage. It refuses changes to selected release inputs and records the local plan separately. The candidate checker retains passed and failed pytest fixture bodies in its explicit `test-artifacts` directory.
This supports the required exposure census.
Later disposable-fixture retirement follows the declared retention policy after required census closure.
Without reused portable evidence, the release runner retains passed and failed fixture bodies in its own explicit packet directory.
Native and held profiles use the same custody policy.
Both release routes select these pytest options through one shared owner.

Commit that exact unchanged candidate. Run the release runner with `--portable-evidence /absolute/new-candidate-packet/precommit-portable-evidence.json` in addition to its normal portable packet options. This option authenticates the original logs/inventory/coverage against the final selected commit, preserves their precommit attribution and runs artifact/static/installed checks without invoking pytest again. A changed candidate, filtered/collect-only selector, failed check or altered evidence refuses reuse. Preserve failed packets and use focused repair checks; another full suite requires a new explicit decision.

The candidate runner and evidence verifier share the exact fixture-retention
policy and pytest options. Copied evidence retains its original absolute fixture
and cache destinations. Older packets without the current all-retention policy
remain historical evidence and cannot select this reuse route.

The candidate checker saves its progress before each subprocess and after each sealed log.
A catchable interruption records `INTERRUPTED` with an unobserved exit code.
An abrupt termination can leave `RUNNING` evidence.
Neither state permits artifact-gate reuse.

The [release runner](../../scripts/release_check.py) verifies the selected committed
source in the frozen root checkout and retains its independently verified source
bundle in the new packet. It records raw checkout status and the local plan
separately from admission of exact committed release inputs. It uses this sole
project checkout throughout the gate.
It installs the locked environment and retains the actual Python, distribution and backend versions.
Before testing or building, it verifies the executing package belongs to that
checkout and that source, module and distribution versions agree.
The runner examines static errors, all registered generators and shipped-document targets before expensive tests.
The generator check stops source drift before the complete portable suite.
The portable profile retains the complete portable tests and required critical coverage.
Coverage checks configured paths separately from the actual measured critical
owners, including the active catalog migration.
Selected skips fail.

The runner builds the wheel through its newly produced sdist. It compares every package source/resource member with the selected Git source. It installs those exact artifact bytes in a separate wheel environment. Installed checks cover leaf help, metadata, packaged notices, native refusals and the full public reactor example.

They also cover partial failure, existing-output refusal and console bootstrap before NumPy import. These are software and exposed-development checks. They grant no scientific authority or admission.

## Examine the packet

Read `release-manifest.json`.
Require `status=PASSED` and the exact selected source identity.
Compare its tree-inventory and lock hashes with that source.
Read its actual tags, host and uv version.
Compare every required check's command, exit status and log hash.
Keep the environment log with the packet.

Each bound log is a new snapshot containing at most the bytes observed after
the direct child returned or its wait was interrupted. `unbound_live_log` names
the original diagnostic log; descendants may continue writing it, so its later
bytes are not part of the bound evidence. Successful and failed checks use
sealed snapshots. Catchable gate failures record `FAILED` and retain the
attempted command, exception type and an unobserved/null exit code where needed,
then propagate the original failure.

Read the three inventories against their exact `release-manifest.json` hash fields.

| Inventory | Exact scope | Manifest hash field |
| --- | --- | --- |
| `package-inventory.json` | Wheel package members | `package_inventory_sha256` |
| `sdist-source-inventory.json` | Every shipped committed source member in the sdist | `sdist_source_inventory_sha256` |
| `researcher-input-inventory.json` | Shipped researcher guides and copied inputs | `researcher_input_inventory_sha256` |

Compare each selected member's byte count and SHA-256.
Select the wheel and sdist from the manifest's `artifacts` entries.
Those entries bind path, byte count and hash.

Exclude every Markdown work plan from the wheel, source distribution and other
release archives, including `WTF.md` and all superseded plans wherever located.
Keep historical records in the checkout or external custody. Public guides and
scientific specifications must stand on their own; move required scientific
definitions to their supported owner before excluding an obsolete plan.
The unshipped workspace blog at `docs/blog/` also remains excluded. Git's local
ignore rules alone do not control build selection. Inspect exact artifact
inventories and bind every shipped member to its selected committed blob.

Inspect the retained committed-source archive inventory as well as the sdist and
wheel inventories. The archive selected for release must also exclude Markdown
plans; separate archival custody may retain the complete historical source.
Targeted exclusion controls establish
the rule, not the contents of a future artifact; the final exact artifacts and
archive still require their recorded checks.

Build-source metadata travels unchanged from the committed build into the source
distribution and wheel metadata. It records the source commit, archive and tree
identities, exact package members, and selected lockfile. The installed source
owner authenticates the actual distribution against those bytes; source/config
paths still belong to the matching selected source distribution. Worker
admission observes its actual interpreter and numerical runtime. These source
observations grant no scientific qualification or execution/reveal authority.

Use the packet's `wheel-requirements.txt` for a separate exact wheel installation. The packet also retains critical-coverage evidence and its subprocess-measurement limit. The [testing guide](../development/testing.md) defines that coverage scope.

`release-status.json` binds the original manifest hash and the same source/artifact identities.
Its scientific qualification status is `NOT_PERFORMED`.
Keep that snapshot unchanged.
The later [external selection record](release-status.md#selection-record-contract) binds the software snapshot with separate paper, qualification and review evidence.
It owns the release stage and selected evidence.

When a workflow uses original scientific workers and separately sealed metadata
code, retain their distinct source identities in its acceptance evidence. A pass
for the minimal recovery source does not verify an unrelated full architecture
release, and neither source's software checks promote historical science to a
new producing source. Bind release checks to the actual final release commit.

The paper binding is separate from software artifact construction.
For the selected published preprint, retain the supplied archive, PDFs, figures and historical producing identities unchanged.
The selection contract accepts an original publication build manifest or the [as-is preservation receipt](../../paper/source/source-preservation.json), together with exact asset, numerical/document-check and visual-review bindings.
That receipt states which original recipe, validation and tool records exist and which remain unavailable; it does not invent a build by the selected software.
Neither a new PDF build nor a preprint experiment rerun is required to select `SOURCE_READY`.
New derivatives and later experimental results retain separate identities and reviews.

## Selection and stopping conditions

A failed packet is retained diagnostic evidence.
It cannot select a passing candidate.
An incomplete packet without terminal manifest/status records is also
nonpassing. Abrupt termination, power loss or failed final storage writes may
prevent finalization; do not interpret a missing terminal record as success.
For a source correction, commit the reviewed change and use a new packet directory.
Keep earlier failure evidence unchanged.
Never select an artifact by its familiar filename or from an old ignored build directory.
A rebuilt artifact needs verification of its own bytes.

The source migration does not move existing campaign elapsed journals.
The default store refuses an existing original journal root before it can initialize a new ledger.
Continue an existing campaign only through a separately verified custody-preserving migration
that retains every snapshot, transition, envelope binding and accumulated time.
Selecting an explicit root does not make incompatible records valid or grant execution authority.

Historical tags and artifacts retain their original identities and custody.
They do not qualify a later source.
The runner creates no release tag and performs no publication.
Fresh qualification uses the separately authorized [operator lifecycle](../../programmes/foundations/measurement-and-response/workflows/reactor-response/operation.md).
The external selection binds those later acts without changing the qualified source.

## References and research

The [release runner](../../scripts/release_check.py) owns the packet and artifact construction.
The [environment guide](../using/environments.md) and [test profiles](../development/testing.md) own their actual prerequisites.
The [release selection contract](release-status.md) owns the final evidence join and stage conditions.
The [paper build guide](../development/paper-build.md) owns publication-asset consistency and visual review.
The [scientific integrity guide](../reference/scientific-integrity.md) states the separate scientific and authority boundaries.
