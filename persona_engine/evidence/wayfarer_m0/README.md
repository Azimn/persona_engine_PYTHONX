# Wayfarer M0 Evidence Package

This directory is a reproducible behavioral evidence capture for Project Wayfarer before `.snp` v2 work begins.

It contains fresh-state stdout from every documented simulator script and one deterministic Pretorius session captured with the offline renderer. `manifest.json` records simulator exit codes rather than discarding a capture when a simulator's lexical oracle fails. A nonzero simulator result therefore remains visible evidence and must be classified as a runtime defect, semantic regression, or brittle expectation before it is changed.

The Pretorius JSON package includes turn outputs, selected intentions, validator/suppression traces, interpretive-belief traces, public state after each turn, the event log, final debug state, final serialized state, renderer status, and a final-state checkpoint checksum.

These files are evidence snapshots, not automatically golden prose fixtures. Natural-language surface output should become a strict regression requirement only where lexical stability is itself the intended contract. Semantic and state contracts are normally more important than incidental wording.

The checksums in `manifest.json` and the Pretorius state checkpoint are ordinary artifact integrity/comparison values. They do not imply a hash-chained continuity ledger.

Re-run this capture through the `Wayfarer Evidence Capture` workflow or by running the simulator commands and `tools/capture_wayfarer_evidence.py` locally from a clean state.
