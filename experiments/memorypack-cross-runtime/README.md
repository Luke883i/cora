# MemoryPack F5 — cross-process, cross-.NET-runtime binary compatibility

This is a third-party **read-only upstream** experiment in CORA PR #92. Source `Cysharp/MemoryPack` is pinned to commit `239ffa0df2f7ccad63d276457557b49e88acae4b`. No upstream branch, issue, security advisory or PR is created.

## What F5 actually does

1. Generate ten binary fixture pairs with an independent Python Gregorian/two's-complement/little-endian oracle. Include negative time zone offsets to distinguish .NET 9 and .NET 10 native layouts.
2. Compile one native console app for net8.0, net9.0 and net10.0 against the **original unmodified** MemoryPack.Core source.
3. Run **three independent producer processes**; each writes 10 `Net10DateTimeOffset` and 10 `UnityDateTimeOffset` binary files plus observed local-only native `DateTimeOffset` bytes. Python compares all 60 stable-wrapper files against oracle bytes.
4. Run **nine new consumer processes**, covering the 3x3 directed runtime matrix; each reads persisted producer files and independently checks typed deserialization, ticks, offsets and independent byte goldens. Reading the .NET 9 historical layout with `Net10DateTimeOffset` is separately checked.
5. Run native consumers on isolated corrupted and missing-file producer directories; require contract-specific failures. Neither mutation changes original target files.
6. Feed the fail-closed run receipt to CORA's `assess_cut` and require external release to remain blocked.

All **12** producer and consumer app processes are distinct process IDs. Build is separately executed. A green gate is `PASS_SCOPED_DOTNET_8_9_10_CROSS_PROCESS`, **not** MemoryPack release readiness.

## Negative scope

The experiment makes NO claim of a common native `DateTimeOffset` wire ABI across frameworks: layout changes between .NET 9 and 10 are documented and intentionally not treated as wire equivalence. Unity actual runtime/IL2CPP and security qualification are **not tested**; the `UnityDateTimeOffset` wrapper is exercised under .NET, not Unity. This experiment is independent of F4 VarInt repair and does **not** apply that patch. It does not show that CORA outperforms other coding agents or that an external maintainer accepts a change.

Use the dedicated GitHub Actions workflow `CORA | MemoryPack cross-runtime F5`. The GitHub artifact `cora-memorypack-cross-runtime-f5` contains oracle, 60 stable binary files, 30 native-local-only files, per-process receipts and logs, two negative controls, and the CORA reticulum. Pre-execution status remains HOLD.
