# Adjacent Character Architectures and Transferable Mechanisms

Date: 2026-09-02
Production checkpoint reviewed: `wayfarer` at `569db261ecf4edda50403ce09d2f2a9e5d512b69`

## Purpose

Wayfarer should not evolve in isolation. Character agents, companion systems, cognitive architectures, game-agent research, and hobbyist role-playing systems repeatedly encounter the same broad problems: persona drift, long-term memory, changing beliefs, relationship continuity, emotional coherence, model dependence, context growth, and accidental omniscience.

This note records mechanisms that appear transferable to Wayfarer after comparing them against the current authority model and minimum-mechanism rule. It is a research and experiment guide, not permission to import another architecture wholesale.

A mechanism becomes production work only after a controlled Wayfarer experiment demonstrates a behavior the current system cannot produce or preserve. The pending Phase D real-model renderer fixture remains frozen. Do not modify its requests, scoring, or production checkpoint in response to this review before collecting the planned actual-model evidence.

## Current external evidence most relevant to Wayfarer

### Long-horizon persona and trajectory must be evaluated separately

Narayanan Venkit et al., *Best Friends, Not Forever: Evaluating Long-Horizon Persona Collapse and Behavioral Drift in AI Companions* (2026), evaluates 2,008 conversations across 27 personas, nine interaction schedules, three generated-memory settings, and four models. The study separates persona enactment from trajectory recall and reports that no tested configuration reliably preserves both. It reports average trajectory accuracy of 44.4% and user-state recall near four-choice chance. The authors explicitly recommend separating persona enactment, trajectory recall, evaluator provenance, and deployment context rather than collapsing them into a single stability score.

Source: https://arxiv.org/abs/2607.28818

**Wayfarer translation:** M18 should preserve separate measures for visible persona enactment and accumulated-trajectory correctness. A system can sound exactly like the character while remembering the wrong life, or remember the correct life while a renderer performs the character poorly. Those are different failures and should remain different metrics.

**Do not copy:** Do not reduce Wayfarer evaluation to a single aggregate persona score.

### Temporal knowledge semantics are useful without a graph database

Rasmussen et al., *Zep: A Temporal Knowledge Graph Architecture for Agent Memory* (2025), uses Graphiti to preserve changing knowledge and historical relationships rather than treating retrieved facts as timeless strings. Its evaluation includes Deep Memory Retrieval and LongMemEval tasks.

Source: https://arxiv.org/abs/2501.13956

**Wayfarer translation:** borrow the semantics, not the infrastructure. The canonical experience `Alice told me the bridge is closed` should remain immutable evidence. A separate subject-owned current proposition may later be `I tentatively believe the bridge is closed`, with evidence provenance and subsequent contradiction/correction. New evidence changes the current proposition without rewriting the original experience. World Authority remains separate from subjective belief.

A compact Wayfarer implementation should initially require no graph database, embeddings service, or external dependency.

### Long-term memory needs updating, temporal reasoning, and abstention

LongMemEval identifies information extraction, multi-session reasoning, temporal reasoning, knowledge updating, and abstention as distinct long-term conversational-memory capabilities.

Source: https://arxiv.org/abs/2410.10813

**Wayfarer translation:** future M6 tests should include conflicting testimony, correction, time-bounded claims, outdated claims, and cases where the correct subject state is uncertainty rather than forced belief. Retrieval accuracy alone is insufficient.

### Associative retrieval can be tested over links Wayfarer already owns

Jiang et al., *Synapse: Empowering LLM Agents with Episodic-Semantic Memory via Spreading Activation* (Findings of ACL 2026), combines episodic and semantic memory through a dynamic graph, spreading activation, lateral inhibition, temporal decay, and hybrid retrieval.

Source: https://aclanthology.org/2026.findings-acl.1108/

**Wayfarer translation:** do not add a graph store simply to imitate Synapse. Wayfarer already has causal parents, subject ordering/time, source actors, relationship scope, memory classes, commitments, and continuity identifiers. A future ablation can test whether one or two bounded associative hops across those existing links improve recall under the same active-memory budget.

**Acceptance gate:** associative retrieval earns production status only if it measurably improves a held-out multi-hop or indirect-recall task without unacceptable interference, state growth, or dependency cost.

### Appraisal has empirical support as a causal intermediate representation

Croissant et al., *An appraisal-based chain-of-emotion architecture for affective language model game agents* (PLOS ONE, 2024), compares no-memory, memory, and appraisal-prompting conditions and reports improvements in emotional-intelligence tasks and several user-experience measures for appraisal-driven game agents.

Source: https://doi.org/10.1371/journal.pone.0301033

This aligns with earlier appraisal-oriented agent architectures such as FAtiMA, while Wayfarer has different authority and resource requirements.

**Wayfarer translation:** M8 should treat appraisal as a compact typed description of what an event means to this subject, not as generated emotional prose and not as sentiment analysis. Candidate dimensions already named in the roadmap include novelty, goal relevance, relationship relevance, identity relevance, control, threat/opportunity, expected outcome, and social meaning. Start with only dimensions whose removal produces a measurable behavioral difference.

A model may propose semantic appraisal features when needed, but a model-generated appraisal has no direct canonical write authority. Deterministic fallback must remain possible.

### Personality-conditioned memory encoding can create deeper character diversity

Dua, Kriplani, and Devgan, *Engram: Personality-Parameterized Schema Memory for NPC Cognitive Diversity* (FDG 2026), reports preliminary results in which OCEAN personality parameters influence how otherwise identical experiences are structurally encoded. High-Neuroticism configurations store more threat-tagged memories, high-Extraversion configurations amplify social encoding, and low-Openness configurations resist belief revision.

Sources:
- https://fdg2026.org/abstracts/
- DOI: 10.1145/3815598.3815701

**Wayfarer translation:** the useful idea is not OCEAN itself. The same canonical external event can produce different subjective experience projections because different subjects appraise and encode it differently. Pretorius may encode a social event primarily as a boundary violation, Friendly as a repairable interpersonal disruption, and Rival as a challenge. Their canonical event evidence can remain equivalent while later cognition receives character-specific subjective traces.

**Do not copy:** do not add a Big Five runtime subsystem merely because the Engram implementation uses one. Existing Wayfarer phenotype/disposition state should be tested first as the conditioning source.

### Dialogue evaluation should be multi-turn and pairwise where possible

The RAIDEN benchmark contains more than 40,000 multi-turn utterances across 135 characters and evaluates role-playing conversational agents through measurement-driven dialogues targeted at specific character dimensions.

Source: https://aclanthology.org/2025.coling-main.735/

**Wayfarer translation:** future held-out human evaluation should use paired outputs where practical. Useful comparisons include the same developed subject rendered by two different models, Wayfarer versus prompt-only using the same model, and different Wayfarer characters using the same model. Evaluators should rate both character enactment and historical/trajectory correctness separately.

### POV-aware memory is a practical anti-omniscience mechanism

OpenVault is an open-source SillyTavern memory extension that records structured events with involved characters and witnesses, then filters retrieval by point of view.

Source: https://github.com/unkarelian/openvault

**Wayfarer translation:** Society Lab and future multi-character hosts should distinguish world occurrence from subject experience. An event that happened is not automatically something every subject experienced. Witness/perception scope should determine which subject receives direct experiential evidence. A non-witness may later acquire testimony or inference about the same event.

This belongs at the perception/evidence boundary, not as a renderer prompt convention.

### Companion systems demonstrate useful state machines, but persona rewriting conflicts with Wayfarer authority

Shikigami Protocol is a local-first companion framework with persistent emotion, energy, affinity, fact/vector memory, summaries, reflection, proactivity, and persona evolution. Its persona evolution preserves the authored original and a core anchor while periodically rewriting an evolved persona representation with an audit trail and rollback.

Source: https://github.com/Shikigami-Lab/Shikigami-Protocol

**Wayfarer translation:** its local state machines, proactivity, auditability, and explicit relationship state are useful comparative examples. The persona-rewriting mechanism should not be copied into Wayfarer as identity authority. Wayfarer's authored origin plus typed developmental state and evidence-backed offsets provide the safer equivalent. Generated prose may describe development, but it must not silently become the new canonical person.

## Candidate experiments after the current frozen Phase D collection

### A. Epistemic proposition and evidence layer

Highest-priority architecture experiment.

Test the current gap using testimony and correction. The baseline should ask whether Wayfarer can represent all of these simultaneously without conflation:

- I experienced Alice telling me X.
- Alice's statement is evidence, not World Authority.
- I currently believe, doubt, or remain uncertain about X.
- I know why my current stance changed.
- A later correction can change my current proposition without rewriting the original Alice event.

The smallest candidate representation is a derived subject-owned proposition plus bounded evidence references. Do not start with a knowledge graph.

Potential minimal fields, subject to the baseline experiment:

- stable proposition key or compact canonical proposition form;
- current stance such as unknown, tentative, believed, or disbelieved;
- confidence only if a graded value proves necessary;
- bounded evidence references;
- evidence/source class;
- subject acquisition/update time;
- verification/contradiction state where justified.

World Authority remains authoritative for established world facts. The proposition layer describes what the subject currently thinks, not what reality is.

### B. Typed appraisal ablation

Create one scenario in which identical input should mean something different to contrasting characters because of existing relationship/value/disposition state. Freeze current behavior first. Add the smallest appraisal object that produces the missing causal distinction. Do not begin with a full emotion taxonomy.

### C. Character-mediated subjective encoding

After appraisal exists, test whether the same canonical event should produce different subjective tags/salience/interpretive traces for contrasting characters. Use existing cartridge state before considering any new personality vector.

### D. Bounded associative retrieval

Construct a held-out recall case that cannot be solved well by direct lexical/semantic similarity but can be solved through an existing causal, relationship, commitment, entity, or temporal link. Compare zero-hop against one-hop and two-hop retrieval under the same context and memory budget. Reject the mechanism if it mainly increases interference.

### E. Speech delivery receipt

Wayfarer's action architecture already distinguishes intention from host/world resolution. Speech should eventually receive the same treatment in hosts where generation and actual delivery can diverge.

Candidate causal path:

`SpeechPlan -> Renderer -> Host Delivery -> DeliveryReceipt -> Subject Experience`

The receipt should describe what was actually delivered/perceived, not simply echo the generated text. This matters for interruption, TTS failure, partial streaming, game events, network loss, muting, and embodied hosts. A character that was interrupted halfway through a confession must not later remember having completed the confession.

### F. Witness and perspective scope

Before uncontrolled multi-agent Society Lab work, test explicit witness scope. A world event becomes first-person experiential evidence only for subjects with an authorized perception path. Other subjects may learn of it later through testimony or inference.

## Evaluation changes to retain

Future long-horizon reports should separately record:

1. **Persona enactment:** does the subject's behavior/voice still match its current identity and developmental state?
2. **Trajectory correctness:** does the system accurately preserve what happened, what changed, and what the subject currently knows/believes about that history?
3. **Cross-model variance:** how far does one subject move behaviorally when only the renderer/model changes?
4. **Cross-character distance:** how different are contrasting subjects under the same model and stimulus?
5. **Evaluator provenance:** human/model evaluator identity, prompt/rubric version, blinding state, and evaluation checkpoint.

Do not allow excellent surface imitation to hide corrupted continuity, and do not allow correct database state to stand in for recognizable character behavior.

## Explicit non-adoptions

This review does **not** justify adding:

- a graph database;
- a general OCEAN/Big Five execution engine;
- a large BDI or cognitive-module stack;
- many new emotion variables;
- arbitrary forgetting curves;
- automatic persona-prompt rewriting as canonical development;
- model fine-tuning as the primary identity store;
- an LLM judge with hidden authority over subject state.

Each may be revisited only if a future controlled failure establishes a requirement that a smaller mechanism cannot satisfy.

## Production freeze note

At the time of this review, `wayfarer` production is intentionally frozen for the first actual-model Phase D smoke collection at merge checkpoint `569db261ecf4edda50403ce09d2f2a9e5d512b69`. Documentation may advance, but runtime changes intended for the candidate mechanisms above must remain on an experimental branch until the frozen actual-model result has been collected or the experiment is explicitly re-versioned.
