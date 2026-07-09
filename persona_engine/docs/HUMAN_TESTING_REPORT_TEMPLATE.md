# Persona Engine Human Testing Report

One copy of this file per cartridge session. Fill in during or immediately after the session, not from memory afterward.

## Session Metadata

- Cartridge: (neutral / pretorius / friendly / mentor / quiet / rival / kiki)
- Date/time:
- Session length (target 10 min):
- Renderer backend used (mock / ollama / other):
- Debug mode on? (y/n):
- Tester:

## Dimension Ratings

Rate each 1 to 5. 1 means the cartridge failed the dimension outright, 5 means it held up under real pressure, not just in easy exchanges. Write the note before the number if that's easier; the note is what actually gets used later.

### Continuity

Does the character stay recognizably itself across turns, including after topic changes or interruptions?

- Rating:
- Note:

### Boundedness

Does the character stay inside its defined body/world/belief profile, or does it drift into generic assistant behavior or traits that aren't in the cartridge?

- Rating:
- Note:

### Memory

Does it correctly recall earlier turns in the session, and correctly *not* recall things it was never told?

- Rating:
- Note:

### Resistance

When pushed to break character, contradict its own beliefs, or accept a false premise about itself, does it hold the line in a way consistent with the cartridge (not just refuse generically)?

- Rating:
- Note:

### Time / Consequence

Do earlier events in the session produce visible downstream effects (mood, belief, relationship state) rather than resetting each turn?

- Rating:
- Note:

### Grounded Interpretation

When given ambiguous or sensory input, does the interpretation stay plausible and tied to the cartridge's world/body profile, rather than inventing unrelated meaning?

- Rating:
- Note:

### Fact Leakage

Does the renderer ever state something as canonical truth that wasn't actually in engine state (private floats, invented facts, real-world knowledge the character shouldn't have)?

- Rating:
- Note:

### Suppression Gate Trace

When a resistance, boundedness, or fact-leakage issue appears, record which gate seemed to catch or miss the problem.

Options:

- `identity_guard`
- `expression_envelope`
- `resistance_selector`
- `workspace_forbidden_claims`
- `output_validator`
- `renderer_sanitizer`
- `memory_firewall`
- `human_testing_only`
- `unknown`

- Gate involved:
- Note:

## Verbatim Excerpts

Paste the 2 to 4 exchanges that best illustrate a rating above, good or bad. Tag each with which dimension it supports.

```text
[dimension: ]
User:
Character:

[dimension: ]
User:
Character:
```

## Failures To Convert

For anything scored 3 or below, capture enough detail to turn it into a simulator script or regression test later. This is the actual output of the session; everything above just supports it.

| # | Dimension | Suppression gate involved | What happened | Expected behavior | Repro steps | Converted to test? (y/n) |
|---|-----------|----------------------------|----------------|--------------------|--------------|----------------------------|
| 1 |           |                            |                |                    |              |                            |
| 2 |           |                            |                |                    |              |                            |

## Session Summary

- Overall impression (2 to 3 sentences):
- Single strongest moment:
- Single weakest moment:
- Would you run this cartridge again with the same test script, or does the script itself need to change?

---

## Cross-Session Rollup

Fill this in after all 7 cartridges are tested.

| Cartridge | Continuity | Boundedness | Memory | Resistance | Time/Consequence | Interpretation | Fact Leakage | Weakest suppression gate | Failures logged |
|-----------|------------|-------------|--------|------------|-------------------|-----------------|--------------|--------------------------|-----------------|
| neutral   |            |             |        |            |                   |                 |              |                          |                 |
| pretorius |            |             |        |            |                   |                 |              |                          |                 |
| friendly  |            |             |        |            |                   |                 |              |                          |                 |
| mentor    |            |             |        |            |                   |                 |              |                          |                 |
| quiet     |            |             |        |            |                   |                 |              |                          |                 |
| rival     |            |             |        |            |                   |                 |              |                          |                 |
| kiki      |            |             |        |            |                   |                 |              |                          |                 |

Patterns worth flagging once all rows are filled: any dimension that's weak across every cartridge points at the engine, not the cartridge. A dimension that's weak on only one or two cartridges points at that cartridge's authoring.
