#!/usr/bin/env python3
"""One-time documentation synchronization after contextual cold-biography integration."""

from pathlib import Path


def replace_once(path: str, old: str, new: str, label: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"{label} seam not found")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    progress = "persona_engine/docs/WAYFARER_PROGRESS.md"
    replace_once(
        progress,
        """Current production/evidence head before this documentation update:\n\n```text\nbba9e8474c9bd1900440afcfcc6a26e332b56f7c\nBound active WorldAuthority without losing fallback semantics\n```\n\nThe latest phase-sized Python 3.11 integration run completed with:\n\n```text\nFocused world + continuity tests: 26 passed\nFull suite: 297 passed, 1 skipped, 1 warning\n```\n\nThat integration also passed a 1,000-turn production WorldAuthority churn check, a semantics-preserving expiry/visibility compaction probe, and canonical-history preservation checks. The remaining warning is the existing Starlette/httpx TestClient deprecation, not a Wayfarer behavioral failure.\n\nThis documentation commit is intended to trigger the ordinary Python 3.11/3.12 Wayfarer CI path against the committed production state because GitHub intentionally does not recursively trigger workflows from the bot-authored integration commit.\n""",
        """Current production/evidence head before this documentation update:\n\n```text\n46110470b756c1cb893407b13c019aa094162fa2\nIntegrate grounded contextual cold biography\n```\n\nThe latest phase-sized Python 3.11 integration run completed with:\n\n```text\nFocused contextual/history/offline-renderer tests: 27 passed\nFull suite: 302 passed, 1 skipped, 1 warning\n```\n\nThe integration makes grounded contextual cold-biography read-through observable in the deterministic renderer while keeping the recovered episode transient and interlocutor-scoped. The remaining warning is the existing Starlette/httpx TestClient deprecation, not a Wayfarer behavioral failure.\n\nThis documentation commit is intended to trigger the ordinary Python 3.11/3.12 Wayfarer CI path against the committed production state because GitHub intentionally does not recursively trigger workflows from the bot-authored integration commit.\n""",
        "progress checkpoint",
    )

    replace_once(
        progress,
        """Explicit recall requests may now consult canonical cold biography for the active interlocutor and receive transient recall candidates for the current turn. Cold candidates do not automatically write themselves into identity, slow beliefs, earned traits, commitments, or the hot autobiographical cache. Canonical continuity remains authoritative history.\n\nA false-recall adversarial probe initially showed that nonzero generic similarity could make a real but unrelated memory answer a question about something that never happened. Recall admission now requires a topical lexical anchor after removing generic recall scaffolding. Semantic similarity ranks only candidates that pass that grounding gate. A nonexistent brass-telescope memory therefore fails closed rather than returning the nearest unrelated memory.\n""",
        """Explicit recall requests may consult canonical cold biography for the active interlocutor and receive transient recall candidates for the current turn. Cold candidates do not automatically write themselves into identity, slow beliefs, earned traits, commitments, or the hot autobiographical cache. Canonical continuity remains authoritative history.\n\nA second experiment established a separate ordinary-context gap. After an old lighthouse fact was pushed out of an experimental hot set, the question `Is the lighthouse lens color still the same?` could not recover it through live top-K memory even though the old canonical input remained intact. A grounded contextual reader recovered `cobalt-blue` using only the topical anchors `lighthouse`, `lens`, and `color`. A never-happened harbor/telescope/serial-number query returned no candidate, and the anchorless `Is it still the same?` query failed closed.\n\nThat result earned a narrow production contextual read-through. It runs only for non-explicit questions with a continuation cue and at least two substantive topical anchors. All anchors must occur in the old canonical statement. At most one contextual cold candidate is admitted, one retrieval slot is reserved for it while the other slots remain live evidence, and the candidate is tagged `contextual_readthrough` without being rehydrated into resident memory. The deterministic offline renderer now exposes that grounded memory instead of hiding successful recollection behind a generic question fallback. Contextual cold access remains scoped to the active interlocutor.\n\nA false-recall adversarial probe initially showed that nonzero generic similarity could make a real but unrelated memory answer a question about something that never happened. Recall admission now requires topical lexical grounding after removing generic retrieval scaffolding. Semantic similarity ranks only candidates that pass that grounding gate. A nonexistent brass-telescope memory therefore fails closed rather than returning the nearest unrelated memory.\n""",
        "progress cold readthrough",
    )

    replace_once(
        progress,
        """This is strong evidence for the architectural proposition that the size of a character's life does not need to determine the size of the character's causally sufficient present. It is **not** evidence that production Wayfarer should retain exactly one hot memory. The current scenario has not yet tested multiple simultaneous unresolved relationships, obligations, active goals, conflicting evidence chains, or other cases that may require a larger active autobiographical set.\n\n## Bounded WorldAuthority\n""",
        """This is strong evidence for the architectural proposition that the size of a character's life does not need to determine the size of the character's causally sufficient present. It is **not** evidence that production Wayfarer should retain exactly one hot memory.\n\nA subsequent causal-pressure probe demonstrated why. With one hot memory, unresolved-history conduct survived but the existing reflection mechanism lost a real two-memory consolidation effect. Budgets 2, 3, 4, and 8 preserved both effects in that fixture. More surprisingly, an unconstrained 24-memory resident store performed worse: routine catalog memories occupied the top-K retrieval set, causing both trust qualification and reflection to miss unresolved memories that were physically present. The experiment also exposed and fixed an equal-strength `MemoryUnit` ordering defect that only appears with multiple equally scored memories.\n\nThe conclusion is therefore not that `2` is the correct capacity. It is that active autobiography is an attentional/causal working set, and unlimited resident history is not a valid gold standard. Production admission/eviction must be derived from the evidence demands of actual consumers rather than from an arbitrary item count.\n\n## Bounded WorldAuthority\n""",
        "progress hot pressure",
    )

    replace_once(
        progress,
        """Cold biography is production-capable. WorldAuthority active-history compaction is production. Relevance-gated rehearsal is production. The exact hot autobiographical working-set size remains experimental.\n""",
        """Explicit cold recall and grounded contextual cold-biography read-through are production-capable. WorldAuthority active-history compaction is production. Relevance-gated rehearsal is production. The exact hot autobiographical working-set admission/eviction policy remains experimental.\n""",
        "progress resource interpretation",
    )

    start = "## Immediate next actions\n\n"
    end = "\n## Contributor rule\n"
    target = Path(progress)
    text = target.read_text(encoding="utf-8")
    i = text.find(start)
    j = text.find(end, i)
    if i < 0 or j < 0:
        raise SystemExit("progress immediate-actions seam not found")
    new_actions = """## Immediate next actions\n\n1. Verify this documentation commit and the committed `46110470...` contextual cold-biography integration through ordinary Wayfarer CI on Python 3.11 and 3.12.\n2. Do **not** turn the pressure fixture's smallest passing budget (`2`) into a production capacity constant.\n3. Audit every active consumer of autobiographical memory and derive the minimum evidence each can use: ordinary turn retrieval, `HistoryDecisionEvidence`, reflection/consolidation, renderer grounding, and any other current reader.\n4. Design a production hot-memory admission/eviction candidate from those consumer contracts. It should protect currently causal unresolved/evidence-bearing memories, prevent routine history from crowding them out, and rely on canonical cold biography plus grounded transient read-through for inactive history.\n5. Stress that candidate with several distinct simultaneous causal roles rather than duplicate copies of one event type. Preserve repair semantics, unresolved-history conduct, explicit recall, contextual continuation, identity protection, commitments, restart, and cross-interlocutor boundaries.\n6. If and only if that policy passes, integrate it and repeat the 5,000-turn plateau measurement with no experimental compaction helper. That will be the first defensible production resident-state measurement.\n7. After the production measurement, translate the surviving state families into a C99-oriented compact layout and estimate the character-kernel hardware floor separately from the optional language-generation floor. Continue targeted MVI scenarios for interpretation, habits, symbols, and body only where a longitudinal behavior gives them something concrete to explain.\n"""
    target.write_text(text[:i] + new_actions + text[j:], encoding="utf-8")

    master = "persona_engine/docs/WAYFARER_MASTER_PLAN.md"
    replace_once(
        master,
        """A memory record should be able to preserve:\n\n- what was observed,\n- source and source actor,\n- confidence/evidence,\n- interpretation at the time,\n- affective state,\n- relationship relevance,\n- identity relevance,\n- goal relevance,\n- action taken,\n- outcome,\n- unresolved status,\n- later reinterpretations,\n- causal event IDs.\n\nTasks:\n""",
        """A memory record should be able to preserve:\n\n- what was observed,\n- source and source actor,\n- confidence/evidence,\n- interpretation at the time,\n- affective state,\n- relationship relevance,\n- identity relevance,\n- goal relevance,\n- action taken,\n- outcome,\n- unresolved status,\n- later reinterpretations,\n- causal event IDs.\n\nCurrent implementation evidence:\n\n- [x] Canonical input continuity can serve as cold biography without rehydrating the whole archive into active autobiographical state.\n- [x] Explicit recall has grounded, fail-closed cold read-through for the active interlocutor.\n- [x] Narrow contextual continuation can transiently recover one grounded cold episode without embedding the remembered value in the query or promoting the episode into resident memory.\n- [x] Multi-memory pressure testing demonstrated that unlimited resident autobiography can degrade bounded top-K cognition through retrieval interference.\n- [ ] Derive the production hot-memory admission/eviction policy from actual memory-consumer evidence contracts rather than a convenient fixed item count.\n\nTasks:\n""",
        "master M6 evidence",
    )


if __name__ == "__main__":
    main()
