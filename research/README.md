# Wayfarer Research Workspace

This directory contains research-facing material that may support a future thesis, paper, poster, or formal evaluation of Project Wayfarer.

It is intentionally separate from the engineering implementation contract.

## Authority boundary

Files under `research/` are allowed to contain hypotheses, literature notes, candidate research questions, methodological plans, historical summaries, and interpretations of results. They do **not** define current runtime behavior.

For engineering truth, use:

- `persona_engine/docs/WAYFARER_PROGRESS.md` for live operational status;
- `persona_engine/docs/WAYFARER_MASTER_PLAN.md` for the roadmap;
- `persona_engine/docs/CURRENT_STATUS.md` for the current production contract;
- `AGENTS.md` for contributor constraints;
- `persona_engine/evidence/` and the test suite for executable/recorded evidence.

A research summary should link to those sources rather than silently replacing them.

## Directory structure

- `RESEARCH_QUESTIONS.md` — candidate thesis/research questions and subquestions. These are exploratory until formally selected.
- `METHODS_AND_EVALUATION.md` — proposed separation between development testing and thesis-grade evaluation, including held-out adversarial testing and human evaluation.
- `EVIDENCE_INDEX.md` — research-facing map from possible claims to authoritative Wayfarer evidence files.
- `evidence_summaries/` — dated, immutable snapshots of engineering results that may later be useful when reconstructing the research history.
- `literature/` — scholarly notes, related-work reviews, bibliographic leads, and comparison material.

## Research discipline

1. Do not promote a literature claim into an engineering claim without implementation evidence.
2. Do not treat builder-designed regression tests as independent validation.
3. Keep development fixtures distinct from held-out evaluation fixtures whenever possible.
4. Preserve negative results and pre-fix failures. They are part of the causal research record.
5. When recording a quantitative result, identify the evidence file, code commit or tested head, and test/run context when available.
6. Prefer dated snapshots over mutable prose for thesis-facing summaries.
7. Do not freeze a thesis claim merely because the current architecture makes it convenient. Let the final research question follow the strongest reproducible result.
8. Treat research capture as part of substantive Wayfarer completion: if a phase changes a potentially thesis-relevant claim, limitation, negative result, method, or quantitative result, update the evidence index or add a dated research summary in that same phase.

## Likely thesis pathway

A plausible progression is:

literature and problem definition → candidate research question → operational definitions → development experiments → frozen candidate system → held-out/adversarial evaluation → human-visible evaluation where appropriate → analysis and limitations.

This structure lets Wayfarer remain an engineering project now while preserving the provenance needed if it later becomes formal research.
