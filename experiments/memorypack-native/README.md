# CORA x MemoryPack - native falsification boundary F4

This experiment is NOT part of MemoryPack and does not imply maintainer approval. It is a controlled third-party verification in the CORA repository. It checks out `Cysharp/MemoryPack` at pinned commit `239ffa0df2f7ccad63d276457557b49e88acae4b`, never pushes there, runs its .NET 8 test project with three new tests, changes ONE expression in the temporary runner checkout, and reruns both the focused tests and the existing full .NET test project.

## Expected falsifiable signature

- Original: the two `UInt16` cross-width tests **FAIL**, byte-wire control **PASS**; `dotnet test` returns nonzero.
- Isolated repair: all three **PASS**; `dotnet test` returns zero.
- Full existing `MemoryPack.Tests` suite: **PASS** after the repair (a bounded regression claim, not all of MemoryPack).
- Every test result must appear in an independent TRX file. Missing, skipped or inconclusive results fail closed. The original file SHA-256 and Git commit are pinned.

A green workflow means precisely `PASS_SCOPED_NATIVE_NET8`. It does not establish `.NET 9/10`, Unity, full ABI compatibility, security, memory-safety, or a release. The F3 source model and Node.js proof remain separate evidence. To reproduce on a host with .NET 8 SDK and network access for package restore:

```sh
python3 experiments/memorypack-native/run.py --source /path/to/pinned/MemoryPack-checkout --output /tmp/cora-memorypack-F4
```

The runner intentionally mutates ONLY the checkout given with `--source`. Use a disposable checkout; do not point it at a shared source tree. This is a destructive local experiment for that disposable checkout, not an upstream change.

## Trust and evidence limits

- `MemoryPack` is an external MIT-licensed project and explicitly targets trusted input. This is a correctness/stream-alignment issue, NOT a claimed vulnerability.
- The CI job executes third-party code in GitHub's isolated runner with `contents: read` permissions and no secrets transmitted to MemoryPack.
- Source-layer disagreement is directly observed; *native* C# evidence exists only after the CI receipts are actually returned.
- F4 offers no causal claim that CORA is superior to an ordinary coding agent.
