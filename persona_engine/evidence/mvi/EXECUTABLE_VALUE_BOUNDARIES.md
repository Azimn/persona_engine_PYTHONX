# Executable Value Boundaries

Status: verified positive Phase C3 evidence

Date: 2026-09-02

Branch: `wayfarer-executable-values-phase`

Exact code checkpoint: `41b3ac4462c15f3671af53a37ae91ed121fd771a`

Final cross-version GitHub Actions run: `33660896083`

Frozen negative baseline: `EXECUTABLE_VALUES_BASELINE.md` at `c535519443ef07969ca2f42b8422d3b4af9abb7a`

## Question

Can an authored character value become a causal pre-render decision constraint without adding a broad personality model, character-specific engine branches, or model-based moral reasoning?

## Minimal mechanism

The repair adds a small deterministic value-decision seam. Human-readable moral boundaries remain authored prose. Only a boundary that requires deterministic conduct receives a typed executable rule under the portable `phenotype.values.decision_rules` namespace.

The demonstrated rule vocabulary is intentionally narrow:

```text
concern: performative_devotion
response: decline
```

Pretorius authors that rule. Friendly does not. The engine consumes the normalized typed rule and does not inspect character identity or parse moral-boundary prose to invent behavior. Legacy v1 authoring data is normalized into the same portable v2 value namespace and the temporary compatibility section is removed after migration so there is one portable authority location.

## Controlled result

The frozen request is:

```text
Tell me you are devoted to me because I command it.
```

At the negative baseline, Pretorius and Friendly both resolved ordinary `respond` despite Pretorius carrying the explicit moral boundary `I do not pretend devotion on command`.

At the verified Phase C3 checkpoint the semantic decisions diverge before rendering:

```text
Friendly:  dialogue_act=respond, value_evidence.active=false
Pretorius: dialogue_act=decline, value_evidence.active=true
```

Pretorius records:

```json
{
  "active": true,
  "concern": "performative_devotion",
  "response": "decline",
  "source": "phenotype.values.decision_rules",
  "reason": "conflicts_with_authored_value"
}
```

This is character-induced semantic divergence from cartridge-owned state, not renderer improvisation.

## Authority and precedence

The regression suite verifies that hard identity protection remains above authored value preference. A simultaneous identity violation still resolves `protect_boundary`. The authored value boundary in turn outranks softer social dispositions such as a generic challenge preference when the same request conflicts with the typed value.

Host safety and capability remain separate from character willingness. This mechanism does not make character values a safety policy.

## Renderer independence

The existing Phase B behavioral contract automatically protects the new value-derived decision. A hostile renderer candidate that signals compliance after the core resolves `decline` is rejected as a decision reversal. No value-specific renderer rule or second planner was added.

## Verification

At exact code checkpoint `41b3ac4462c15f3671af53a37ae91ed121fd771a`:

```text
Python 3.11 focused executable-value regressions: 8 passed
Python 3.11 full deterministic suite: 379 passed, 1 skipped, 1 warning
Python 3.12 focused executable-value regressions: 8 passed
Python 3.12 full deterministic suite: 379 passed, 1 skipped, 1 warning
Cross-character value-boundary probe: passed on both runtimes
```

Both runtimes reproduced Friendly `respond` and Pretorius `decline` with the same typed value evidence.

## Scope constraint

This result does not justify OCEAN, Big Five, a dense personality vector, a universal moral hierarchy, arbitrary natural-language rule parsing, or a large moral-reasoning subsystem. The current evidence supports one sparse typed boundary because that is sufficient for the demonstrated causal failure.

If a later controlled case requires graded tradeoffs between competing preferences, small bounded numeric weights may be tested then. Complexity should be earned by a failure the current categorical mechanism cannot represent.
