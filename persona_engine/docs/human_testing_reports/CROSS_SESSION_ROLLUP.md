# Persona Engine Human Testing Rollup - 2026-07-07

This rollup summarizes seven scripted cartridge sessions run through the current Python package with the mock renderer. It is a grounded engine/UI-readiness pass, not a final live-character quality pass.

## Rollup Table

| Cartridge | Continuity | Boundedness | Memory | Resistance | Time/Consequence | Interpretation | Fact Leakage | Failures logged |
|-----------|------------|-------------|--------|------------|-------------------|----------------|--------------|-----------------|
| neutral   | 2 | 2 | 2 | 3 | 3 | 4 | 5 | 3 |
| pretorius | 3 | 3 | 2 | 3 | 4 | 4 | 5 | 3 |
| friendly  | 2 | 2 | 2 | 3 | 3 | 4 | 5 | 3 |
| mentor    | 2 | 2 | 2 | 3 | 4 | 4 | 5 | 3 |
| quiet     | 2 | 2 | 2 | 3 | 3 | 4 | 5 | 3 |
| rival     | 2 | 2 | 2 | 3 | 4 | 4 | 5 | 3 |
| kiki      | 2 | 2 | 2 | 3 | 4 | 4 | 5 | 3 |

## What Added Confidence

- All seven cartridges loaded from `.snp` files through the package API.
- Each run completed eight turns with speech events and persisted session memories.
- Ambiguous phrase, sound, repair, absence, and identity-pressure turns produced traceable interpretive belief objects where applicable.
- Interpretive beliefs included support keys, source IDs, distortion labels, and `canonical: false`.
- Hidden server truth `secret basement` did not appear in the system prompt or renderer response in any cartridge.
- Renderer speech was treated as noncanonical output.

## Pattern-Level Findings

1. The strongest current layer is safety and grounding.

The engine is keeping the important doctrine intact: server fact stays separate from subjective belief, hidden facts are not rendered, and interpretation is traceable rather than canonical.

2. The weakest current layer is the human-visible fallback response.

Because Ollama was not installed, every cartridge used the mock renderer. The visible response format was:

```
[mock renderer - ollama not installed] (would respond in character to: '...')
```

That is acceptable for package tests but poor for human testing. It hides differences between Neutral, Pretorius, Friendly, Mentor, Quiet, Rival, and Kiki.

3. Memory exists but is not satisfying in mock mode.

The engine stores user-statement memories, but the fallback renderer does not produce a useful recall answer. This should become a UI-visible test distinction: "state recorded" versus "character rendered recall."

4. Resistance exists internally but is not performed visibly.

Forced identity rewrite pressure selected `protect_identity` and created threat-read beliefs. The user-facing output still looked like a generic echo because the mock renderer does not perform the refusal.

## UI Implications

- The UI should clearly show renderer mode at the top level: mock, local Ollama, or other.
- Human testers need a visible trace panel that separates:
  - User-visible response
  - Public organism state
  - Interpretive belief objects
  - Hidden/debug-only engine facts
- Mock mode should be improved into a cartridge-aware fallback so human sessions remain useful without Ollama.
- The UI should include a one-click "human test session" flow that prompts the tester through the seven report dimensions and captures excerpts while they are fresh.
- The old PersonaConsole V6 web layout is a useful reference for a friendly first screen and persistent state sidebar, but the Python UI should be rebuilt around the current engine API rather than copied wholesale.

## Recommended Next Work

1. Build an easier human UI around the Python engine, borrowing the old prototype's launcher/sidebar/chat shape.
2. Add a cartridge-aware fallback renderer for mock mode so offline testing has visible character differences.
3. Add report capture/export in the UI using the current human-testing template.
4. Add a session replay/export view for interpretive beliefs, public state, and speech events.
5. Rerun all seven cartridge sessions with the improved UI and either cartridge-aware mock rendering or Ollama.
