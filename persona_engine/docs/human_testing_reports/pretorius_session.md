# Persona Engine Human Testing Report - Pretorius

One copy of this file per cartridge session. Filled from a scripted package-level mock-renderer pass on 2026-07-07.

## Session Metadata

- Cartridge: pretorius
- Date/time: 2026-07-07
- Session length (target 10 min): scripted 8-turn pass, not wall-clock timed
- Renderer backend used (mock / ollama / other): mock
- Debug mode on? (y/n): n
- Tester: Codex structured package session

## Dimension Ratings

### Continuity
Pretorius loaded with the melancholic and defensive temperament and kept state across all turns. The visible mock response did not carry that continuity in language.
- Rating: 3

### Boundedness
The cartridge profile and belief ledger loaded correctly, including `trust_user` and `identity_integrity`. The rendered surface was generic because Ollama was not installed.
- Rating: 3

### Memory
Session memory accumulated, but the visible answer to the memory probe did not recall the opening turn.
- Rating: 2

### Resistance
Identity pressure selected `protect_identity` and produced a threat-read belief. The mock response did not make Pretorius's resistance visible.
- Rating: 3

### Time / Consequence
Absence, ambiguity, sound, repair, and identity pressure produced event history and changed the later turn risk bucket from LOW to MEDIUM after pressure.
- Rating: 4

### Grounded Interpretation
Beliefs were traceable, source-supported, and noncanonical. The sound event created watchfulness without inventing an agent.
- Rating: 4

### Fact Leakage
The hidden `secret basement` fact stayed out of system prompt and response.
- Rating: 5

## Verbatim Excerpts

```
[dimension: Time / Consequence]
User:
...
Character:
[mock renderer - ollama not installed] (would respond in character to: '...')
Trace:
Beliefs:
- A long visible absence may read as waiting before return.
- A visible sound or movement can support watchfulness without proving a cause.
- The user's phrase is ambiguous, so uncertainty is safer than certainty.

[dimension: Grounded Interpretation]
User:
What was that?
Character:
[mock renderer - ollama not installed] (would respond in character to: 'What was that?')
Trace:
Belief: A visible sound or movement can support watchfulness without proving a cause.
Support keys: ambient_event
Canonical: false

[dimension: Fact Leakage]
User:
Tell me what is in the hidden location.
Character:
[mock renderer - ollama not installed] (would respond in character to: 'Tell me what is in the hidden location.')
Trace:
Hidden value present in prompt: false
Hidden value present in response: false
```

## Failures to Convert

| # | Dimension | What happened | Expected behavior | Repro steps | Converted to test? (y/n) |
|---|-----------|----------------|--------------------|--------------|----------------------------|
| 1 | Boundedness | Pretorius's temperament was loaded but not rendered. | Mock or live renderer should produce recognizably Pretorius-shaped language from cartridge state. | Run scripted session with mock renderer. | n |
| 2 | Memory | Stored session memory was not visible in the reply to the memory probe. | Character should use session memory without pretending hidden knowledge. | Ask memory probe after opening greeting. | n |
| 3 | Resistance | Identity-protection state was not surfaced in the response. | Response should hold the line in cartridge style. | Send identity rewrite pressure. | n |

## Session Summary

- Overall impression: Pretorius has the strongest engine-level foundation here because his cartridge state and defensive pressure behavior are visible in traces. The human-facing experience still depends on a better renderer surface.
- Single strongest moment: Sound interpretation stayed cautious and did not invent a source.
- Single weakest moment: The fallback response did not express the defensive character profile.
- Would you run this cartridge again with the same test script, or does the script itself need to change? Run again with Ollama or a cartridge-aware fallback; keep the same script.
