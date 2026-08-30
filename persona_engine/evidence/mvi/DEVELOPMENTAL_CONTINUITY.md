# Developmental Continuity Probe

Passed: `True`.

## Slow belief trajectory

Initial `trust_user`: `0.0`.  
After first identity-violation consolidation: `-0.2`.  
After second identity-violation consolidation: `-0.4`.  
After ordinary restart: `-0.4`.

## Export and replay

Canonical event types: `['input', 'input']`.  
Current root-only replay belief: `0.0`.  
Replay with one consolidation only at the end: `-0.2`.  
Replay with consolidation at the original boundaries: `-0.4`.

## Why no-change passes still matter

One repair then consolidate, repeated twice: `0.0`.  
Two repairs grouped before one consolidation: `0.15`.  
Boundary is causal: `True`.

## Findings

Restart snapshot preserves slow belief: `True`.  
Current canonical replay loses slow belief: `True`.  
One end-of-replay consolidation is insufficient: `True`.  
Recorded boundaries are sufficient under the same rules: `True`.  
No-change boundaries are causal: `True`.

## Minimum mechanism indicated by the experiment

Treat each executed slow-belief consolidation pass as a small character-owned causal root, including passes that change no belief. Replay should regenerate semantic evidence from preceding causal roots, execute consolidation at the recorded boundary, and verify the resulting belief state or digest. Routine per-turn state transitions remain derived diagnostics and do not need to return to permanent biography.
