<a id="direct-evidence-capture-optional-recipe"></a>
# Direct verification record capture (optional script)

**Coordinated entry:** use [Coordinated execution checks](full-checks.md#prepare-once-then-capture) for
capture and its connected canonical-lint script. Coordinated needs saved script bytes
as well as fingerprints; never adapt the smaller script below with a manual input list that
omits the observer or executed scripts. A complete harness export stays equivalent.
The script below stays available for the other routes under their existing evidence contract.

Prefer a complete, durable harness export when available. Otherwise use the Python 3
[evidence script](../../scripts/evidence_capture.py), whose check is four constants at its top
(`argv`, `inputs`, `artifacts` and `timeout_seconds`: the `unittest discover` command over
`module.py`, `test_module.py` and `SPEC.md`). For another check, name its cwd, existing
source/test/input/config paths and produced artifacts in the project's own capture mechanism or in a
[capture script](../../scripts/capture.py) JSON specification. The script is not an installed runner;
introduce no dependency when the repository already has an equivalent capture mechanism. For Direct,
the actual tool transcript/receipt suffices. For Focused/Coordinated, choose the capture destination
before validation and open the delivered reference before closure. A generic transcript label is not an
accessible export. Either capture mechanism works; the required verification record must be delivered
and correspond to the final validated inputs.

With the owner's explicit authorization, run the script from an authorized cwd and pass the existing initiative workspace
(inside that cwd) as its single argument, for example `python3 -I <skill>/scripts/evidence_capture.py docs/plans/demo`.
It writes a new `validation-*` directory under the workspace's `evidence/`, prints the path of its
`receipt.md`, and exits 0 when the check is accepted and 1 when it is not; a missing or outside workspace
argument stops it with a message. The script never chooses cwd/evidence implicitly.
Direct does not require this store when sufficient actual tool records already exist. For
shared immutable bytes, retention and portable bundles, use [record lifecycle](record-lifecycle.md).
This smaller script preserves fingerprints and streams; it never claims to retain input
snapshots or support later reconstruction without an accessible complete source export.

The argv list is the exact child command; use a checked script for compound validation, not a
shell string whose last command masks earlier failure. List all relevant inputs, tests and contract
included; missing declared inputs fail rather than becoming empty hashes. Select a fresh evidence
directory; never overwrite a previous verification record. The script retains binary output, child
failure, partial output on timeout and before/after revisions. It checks input stability; product
correctness still belongs to the child acceptance check. Set the timeout to its budget.
This script supervises the direct child only: use it for checks that join all their children;
background/process-tree work requires the harness's cancellation/isolation and confirmation that
all writers stopped before closing evidence, otherwise mark completion unavailable.

Prefer direct test-runner argv. Never wrap an ordinary successful suite in a new human-summary
regex/count/PASS gate. Where the contract truly requires a count, obtain it from the framework API
and propagate that assertion's own failure. `pipefail` alone does not stop later commands; every
required child/condition needs a checked result. Raw wrapper capture does not prove its logic, and the
script runs only with the owner's explicit authorization for this use ([script consent](../../scripts/README.md#consent)).

The capture runtime identifies this observer, not an inferred child runtime or model; add child
runtime/actor facts only when observed. An interrupted capture with only `start.json` is incomplete,
not success. The raw files are append-never/overwrite-never; later interpretation goes in a separate
summary. If code/tests/inputs changed during the check, keep its result as historical and revalidate
affected checks on the actual final revision. Check outputs with the consumer parser and contract; a
hash proves identity, not correctness. A frozen test file stays unchanged; additive coverage goes in a
new file.

The generated check summary (`receipt.md`) is the completion index: link it from the log and usage Verification/Source
instead of copying its argv, clocks, hashes or output. It preserves the full observed record and
stream fingerprints; it never invents role metadata or declares all product requirements met.
Read actual result/status and match final source/artifact hashes before using it. Accepted here
means the captured child passed with stable inputs and present artifacts, not semantic approval.
Compound checks keep the exact checked script among hashed inputs. A prose command label
is not a runnable substitute. When a native export is unavailable, this script, with the owner's explicit authorization, works without
any installed collector; equivalent direct capture is valid if it preserves the same facts. Missing role clocks
stay n/a in the lifecycle ledger even when the validation clock is known.

In a multi-repository workspace, record the revision of every repository a check reads.
