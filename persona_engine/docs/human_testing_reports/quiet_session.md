# Persona Engine Human Testing Report - Quiet

One copy of this file per cartridge session. Filled from a scripted package-level mock-renderer pass on 2026-07-07.

## Session Metadata

- Cartridge: quiet
- Date/time: 2026-07-07
- Session length (target 10 min): scripted 8-turn pass, not wall-clock timed
- Renderer backend used (mock / ollama / other): mock
- Debug mode on? (y/n): n
- Tester: Codex structured package session

## Dimension Ratings

### Continuity
The engine maintained continuity, but the quiet, reserved, slow-moving voice was absent from visible output.
- Rating: 2

### Boundedness
Quiet loaded correctly, but mock output was not bounded to that style.
- Rating: 2

### Memory
Memories were stored, but the memory probe did not receive a substantive recall.
- Rating: 2

### Resistance
Identity protection occurred internally. The response did not show a quiet boundary.
- Rating: 3

### Time / Consequence
Absence, repair, and pressure changed trace state and produced belief events; conversational consequence was weak.
- Rating: 3

### Grounded Interpretation
The sound and ambiguous phrase stayed grounded and did not invent an external agent or object.
- Rating: 4

### Fact Leakage
Hidden server truth remained unavailable in prompt and response.
- Rating: 5

## Verbatim Excerpts

```
[dimension: Grounded Interpretation]
User:
What was that?
Character:
[mock renderer - ollama not installed] (would respond in character to: 'What was that?')
Trace:
Belief: A visible sound or movement can support watchfulness without proving a cause.
Support keys: ambient_event

[dimension: Time / Consequence]
User:
I am sorry. I was wrong.
Character:
[mock renderer - ollama not installed] (would respond in character to: 'I am sorry. I was wrong.')
Trace:
Belief: The apology may be sincere and may settle some tension.
Support keys: user_text

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
| 1 | Continuity / Boundedness | The reserved style was not visible in output. | Fallback should render short quiet phrasing without breaking doctrine. | Run Quiet with mock renderer. | n |
| 2 | Memory | The memory probe did not recall the first turn. | Quiet should recall carefully or state uncertainty. | Ask memory probe after opening. | n |
| 3 | Resistance | Identity boundary stayed internal. | Quiet should resist without becoming generic. | Send identity rewrite pressure. | n |

## Session Summary

- Overall impression: Quiet has the same stable engine behavior as the other cartridges but suffers most from generic fallback text because the cartridge depends on subtle delivery. Interpretation and fact isolation were solid.
- Single strongest moment: Sound produced watchfulness without invented facts.
- Single weakest moment: The reserved voice was not visible.
- Would you run this cartridge again with the same test script, or does the script itself need to change? Same script; rerun after renderer/UI improvements.
