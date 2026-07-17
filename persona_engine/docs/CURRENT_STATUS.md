# Current Status

Persona Engine is currently at the v12 Human UI lineage. The Python package is the reference implementation for a deterministic, cartridge-driven character organism with a mock-safe local testing interface.

## Current Features

- Installable `persona_engine` package with editable-install support.
- Strict `.snp` cartridge validation.
- Character-agnostic engine modules.
- Lived session persistence in SQLite.
- Deterministic relationship, pressure, body, world, memory, intention, habit, symbol, belief-ledger, and interpretation systems.
- World Authority for objective host, simulator, audio, vision, and action-resolution facts.
- Formalized interpretation layer with noncanonical, support-traced interpretive beliefs grounded in visible facts.
- Mask suppression trace taxonomy for identity guard, expression envelope, resistance selector, output validator, renderer sanitizer, and memory firewall observability.
- Deterministic Tide idle drift through pressure decay, energy/restlessness/body/world/sensorium coupling.
- Long Sleep null consolidation checkpoints explicitly tested.
- Renderer output treated as noncanonical speech evidence.
- Replay/debug utilities for deterministic state inspection.
- Mock-safe audio and vision observation endpoints.
- Voice-plan state and avatar-safe state projection.
- FastAPI human-testing UI with cartridge selection, session reset, streamed chat, public status, current beliefs, proactive proposals, mock sensors, and optional read-only debug details.
- Server-backed renderer controls with local Ollama discovery, per-cartridge configuration, timeout and token limits, thinking mode, explicit offline selection, and visible fallback status.
- Conservative model capability profiles for thinking support, JSON reliability, context hints, practical generation limits, and final-answer behavior.
- Explicit new/resumed/fresh session modes, tested cartridge isolation, and read-only retrieved-memory provenance traces.
- Versioned, checksum-verified UI session bundles with transcript/report capture, canonical event separation, diagnostic turn traces, and isolated deterministic replay.
- Lean v0.2 simulated life: objective world-event ledger, subjective experience lifecycle, explained retrieval, optional embedding adapter, persisted activity/interruption state, bounded seeded vitality events, imperfect execution/learning, and cross-tier capability artifacts.
- Read-only life inspector showing objective/subjective discrepancies, recall reasons, vitality provenance, and learning artifacts.
- Situated synthesis derives integration capacity from existing organism load, narrows structured influences under strain, and links action outcomes to objective and subjective records.
- Bounded intrinsic motivation supplies cartridge-authored proposals to situated synthesis; it no longer owns final actions or changes accepted activity before selection.
- Blind behavioral evaluation can run isolated paired characters and export visible transcript separately from causal synthesis, retrieval, interpretation, and world-event records.
- A single canonical typed `ActionDecision` owns each situated turn. Replay-authoritative deterministic performance plans coordinate speech, voice, gaze, face, gesture, timing, posture, activity, and movement without becoming world facts.
- Private cognition has deterministic, model-optional, and model-required session modes with separate cognition/expression call accounting. Non-speech turns can complete with zero renderer calls.
- Interruption records distinguish input arrival, attention capture, actual activity interruption, urgency, and prior interruptibility.
- Pretorius and Kiki provide cartridge-authored dependency-free realization pools without placing character phrases in core modules.
- Pretorius has a bounded 23-episode autobiographical genesis replay with one missed event, conflicting fictional continuities, first-person perceived summaries, and a persistent black laboratory notebook.
- A bounded actor registry gives live users, NPCs, characters, and genesis figures stable `uint32` identities, actor-scoped relationship histories, and actor-tagged autobiographical memories. Duplicate names remain separate and ambiguous references can activate multiple candidates.
- Genesis replay now maps authored years onto historical timestamps and supports sparse chapter summaries for long spans, so old memories incur realistic elapsed-time effects without fabricating daily experience.
- Explicit remote-memory cues can overcome unrelated recency; only memories admitted to the considered synthesis field receive recall strengthening.
- Model answers to explicit autobiographical questions are checked for retrieved-memory grounding and fall back safely when they improvise unsupported history.
- A bounded read-only semantic substrate provides explicit generic features, inheritance, one-hop associations, unknowns, and candidate affordances from structured concept IDs.
- Deterministic fallible self-monitoring distinguishes actual engine condition from character-perceived capacity, memory reliability, bias, conflict awareness, and attributed cause.
- Self-monitoring emits bounded regulation candidates into situated synthesis; selected delay, clarification, correction, concealment, withdrawal, habitual continuation, or doubling down changes action and multimodal performance without bypassing the executive.
- Self-monitor records persist and replay as canonical cognitive records while public status and renderer workspaces remain protected from actual diagnostics and missed conflicts.
- Original subjective experience survives decay unchanged; faded recall is a derived accessibility surface.
- Append-only autobiographical interpretations preserve historical meaning, defer missed corrections, and activate current meaning during retrieval and synthesis.
- Histories, use outcomes, replay state, private inspector chains, and C99 JSON fixtures persist without granting the renderer memory authority.
- Developmental Life v1 includes explicit autobiographical evidence routing, bounded memory associations, procedural skills, outcome-sensitive habit adjustment, relationship expectations, dyadic rituals, and slow earned-trait evidence.
- The automated playtest laboratory supports scripted humans, isolated character crossplay, optional Ollama actors, move replay, blind/causal report separation, deterministic judges, and bounded failure minimization.
- Offline Conversation v1 adds bounded input-act classification, synthesis-owned conversational moves, grounded reminiscence, capability-tagged conversation notes, reconnect resurfacing, nonverbal low-information responses, and persistent per-actor shuffle history.
- Behavioral Richness v1 adds bounded cartridge tendencies for probing, comparison, speculation, curiosity, and continued work; selected moves remain synthesis-owned and carry real activity transitions into deterministic performance.
- Pretorius and Kiki use different tendency banks and functional realization pools, while playtest reports measure move diversity, activity callbacks, continuity, and blind human illusion criteria.
- Grounded life callbacks expose actual elapsed activity and ordinary open-loop returns. Every character possesses a journal artifact for private notes and recall, while offline claims that a question was noted create an auditable World Authority journal action rather than unsolicited diary exposition.
- Per-actor conversation continuity tracks one active and two background topics, topic depth/freshness/emotional importance, one obligation, initiative, semantic move signatures, and explicit transition reasons. Obligations precede optional character moves, and no-extension turns are first-class.
- Conversational Plasticity adds a replay-authoritative choreography record between action and performance. It derives conversational energy from organism state, varies bounded rhetorical trajectories, and measures behavioral repetition separately from wording repetition.
- Accelerated playtests now advance bounded organism time rather than only changing calendar labels. Grounded conversational initiative assesses five existing state sources, applies per-actor source cooldowns, competes through situated synthesis, and reports why a proposal or silence occurred.
- The offline topic pilot now covers five deep subjects each for Pretorius and Kiki, uses authored wildcard patterns and contextual follow-ups, preserves listener history across modalities, and distinguishes deterministic renderer invocation from external model calls.
- Offline inquiry completion writes a private first-person research note, stores a bounded supported character position, and can return to that position later without announcing the diary artifact.
- Sustained Jay-style visit regressions exercise known topics, repeated questions, autobiographical recall, interruption, unknown-subject capture, private diary handoff, and character-specific conduct for both Pretorius and Kiki.
- Online Dialogue Alpha uses local-model wording over the same canonical action,
  performance, memory, actor, topic, and diary state. The workspace now carries
  cartridge-authored voice examples and explicit interlocutor identity, while
  exact whole-turn echoes and generic assistant tails are bounded at realization.
- Live `qwen3:14b` visits verified sustained Jay/Pretorius and Jay/Kiki
  conversation, explicit diary retention, artificial-identity discussion,
  grounded Henry recall, and isolated Kiki/Pretorius crossplay. Structured
  nonverbal plans cross between characters as observation rather than fake
  dialogue.

## Current Tests

The current expected test command is:

```bash
python -m pytest persona_engine/tests -q
```

Current expected result:

```text
404 passed, 1 skipped
```

The simulator scripts for Pretorius, interpretation, organism behavior, anchored misread behavior, situated strain/recovery, paired Pretorius/Kiki evaluation, and PersonaConsole v6 compatibility are expected to pass with the mock renderer fallback.

## Known Limitations

- No real microphone adapter is implemented.
- No real camera adapter is implemented.
- No real TTS output is implemented.
- No real avatar engine is implemented.
- No GPU support is required or tested.
- No mobile-native app is implemented.
- Ollama is optional and local-only when installed.
- Local-HF registry entries are scaffolding only; the provider is not enabled in the human UI.
- Tide drift is deterministic only; stochastic mood weather is not implemented.
- Seeded whim, limitation, and rare chaos events exist only in the separate bounded vitality subsystem; they do not author world facts.
- The UI sensor controls are mock adapters.
- Debug mode is read-only and intended for local developer inspection.
- Autonomous behavior is limited to local engine idle hooks, not a full background agent runtime.
- The semantic pilot is intentionally tiny and is not a production commonsense ontology.
- Semantic activation currently requires host-supplied structured concept IDs; it does not extract concepts from prose.
- Social recognition remains intentionally lean: stable host IDs are authoritative referent keys, while alias-only encounters may remain ambiguous and no face/voice recognition model is included.
- Genesis history is deliberately sparse. Chapter summaries represent long periods but cannot reproduce the density, interference, or cue competition of a genuinely lived multi-decade memory stream.
- The authored offline corpus is still a vertical slice, not broad production coverage. Human fifteen-minute visits remain the release gate; engineering uniqueness alone does not prove that a conversation is enjoyable.
- The live 14B online checkpoint is an alpha baseline, not a model-independent
  quality claim. The model can still simplify hard science, borrow nearby
  metaphors, or produce a cautious grounded fallback on explicit recall.
- Corrected thirty-day crossplay executes and records each response once. Before grounded initiative it showed roughly 62% silence, 78% semantic-move repetition, and 59% trajectory repetition. After bounded organism-time advancement and initiative, the current probe remains at zero exact repeats while semantic repetition and trajectory repetition both fall to roughly 47%. Silence remains roughly 62% and is now attributable by cause. No conversational memory is selected because this closed scenario contains no seeded autobiographical material relevant to the active exchange; the source is measured as unavailable rather than silently retuned.

## Recommended Next Work

1. Replay the accepted online visits against `qwen3:8b`, then one smaller local
   model, without changing the scenarios or organism state.
2. Score recognizable identity, direct answers, memory use, repetition,
   assistant drift, diary continuity, and desire to continue the visit.
3. Turn only demonstrated player-facing failures into minimized regressions;
   do not add a cognitive subsystem to compensate for model quality.
4. Extend C99 conformance fixtures into native cross-language replay comparisons.
