# Online Dialogue Alpha

## Product Standard

Online dialogue is the primary open-ended character experience. The local
model supplies flexible wording and imagination, but it does not replace the
organism. Identity, memory, relationship state, activity, action, performance,
the physical diary, and participant isolation remain shared with offline mode.

The practical alpha standard is player-facing:

- the character remains recognizable without a large pasted transcript;
- direct questions receive complete answers rather than canned acknowledgements;
- remembered events are grounded when the player explicitly asks for recall;
- opinions and speculation may use memories without being forced into recital;
- online and offline turns share topic depth, participant history, open loops,
  memories, and diary entries;
- silence and gesture remain legitimate observable turns;
- unknown or deliberately retained questions can become first-person diary
  notes and participant-bound follow-ups;
- model prose cannot become objective World Authority merely by being vivid.

The project favors the illusion of a living character over sterile factual
timidity. Imagination, disagreement, humor, vanity, uncertainty, and conflict
are welcome in speech. Objective world mutation still uses approved channels.

## Current Realization Path

```text
observable input
-> portable input act and topic recognition
-> organism appraisal, memory, continuity, and synthesis
-> canonical ActionDecision
-> deterministic PerformancePlan
-> online WorkspaceFrame
-> local model wording
-> bounded echo, grounding, and assistant-tail checks
-> observable speech or nonverbal performance
```

The online workspace now includes:

- the selected action and performance;
- the actual activity and relationship state;
- the current interlocutor by actor-registry identity;
- relevant memories and current autobiographical meaning;
- conversational obligation and optional move;
- a small set of cartridge-authored voice examples;
- explicit permission for character-specific resistance and imagination.

The model is instructed not to invent a substitute activity, copy the
interlocutor's cadence, append generic service language, or discuss a present
interlocutor as though absent. Exact whole-turn echoes fall back to authored
realization. A few terminal assistant invitations are removed without changing
the character's substantive answer.

## Diary Contract

The diary is a private inventory object, not a chat feature or recurring prop.
Characters may read and write it through World Authority. An explicit request
to retain a subject can create:

- a first-person diary entry;
- a participant-bound `promised_followup` open loop;
- continuity that remains available after a renderer or modality change.

Characters need not mention the diary. They may do so when the act of recording
is itself observable or conversationally relevant.

## July 2026 Local Baseline

The live alpha probe used local Ollama with `qwen3:14b`, thinking disabled, a
512-token generation budget, and deterministic private cognition.

Observed successes:

- sustained Jay/Pretorius and Jay/Kiki visits used the live model;
- Kiki answered technical and artificial-identity questions in character;
- Pretorius discussed Henry, fictional origins, digital continuity, and moral
  disagreement without becoming uniformly apologetic;
- explicit retention wrote Kiki's diary and created a promised follow-up;
- Kiki and Pretorius maintained isolated memory stores in online crossplay;
- nonverbal crossplay passed structured performance rather than fake speech;
- exact model echo and generic terminal assistant phrasing are bounded.

Known alpha limitations:

- an explicit autobiographical answer may fall back offline when a model
  paraphrase fails the deliberately conservative grounding check;
- `qwen3:14b` can still simplify difficult science or borrow a nearby metaphor;
- crossplay can become rhetorically self-reinforcing without new world events;
- current activity is only as convincing as the life state supplied to the
  renderer;
- this is an experience checkpoint, not evidence that every installed model
  will inhabit both characters equally well.

## Next Evaluation

Do not add another cognitive subsystem. Hold this architecture steady and
compare model sizes against the same recorded visits:

1. establish the `qwen3:14b` transcript as the capable local baseline;
2. run the same turns with `qwen3:8b`;
3. test one smaller model only after the 8B result is understood;
4. score identity, direct answers, memory use, repetition, assistant drift,
   diary continuity, and subjective desire to continue the visit;
5. retain validated actor moves and causal traces so model quality is not
   confused with different scenarios.

The smallest acceptable model is the smallest one that preserves the
experience, not the smallest one that returns syntactically valid text.
