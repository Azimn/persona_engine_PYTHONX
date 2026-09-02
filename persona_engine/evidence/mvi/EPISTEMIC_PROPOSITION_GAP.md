# Epistemic Proposition Gap

Date: 2026-09-02
Baseline production runtime: `wayfarer` at `569db261ecf4edda50403ce09d2f2a9e5d512b69`
Experimental branch: `wayfarer-adjacent-research-phase`

## Question

Can the current Wayfarer runtime distinguish all of these as separate state concepts?

1. `Alice told me X.`
2. `X is objectively established by the world/host.`
3. `I currently believe X.`
4. `I currently doubt X.`
5. `I used to believe X, but later evidence changed my position.`

## Baseline architecture inspection

The production runtime has intentionally separate authorities around this problem.

### Experience memory

`MemoryUnit` records first-person experience and includes `KnowledgeSource.USER_TOLD`. The normal turn path records user speech as:

`I heard you say: <user text>`

This correctly preserves the event that testimony occurred without making renderer speech objective truth.

### Objective world facts

`WorldAuthority` is explicitly the only generic owner of objective world facts derived from host/simulator/sensor/action-resolution inputs. It does not decide character belief.

Normal user text is not semantically parsed into a world fact such as `bridge.closed = true`.

### Turn-local interpretation

`InterpretiveBelief` is explicitly noncanonical and turn-local. It provides bounded subjective readings of visible sources and does not own durable arbitrary semantic propositions.

### Slow developmental belief ledger

`BeliefLedger` explicitly states that it handles slow, cartridge-defined belief drift and is **not** an arbitrary LLM-generated claim store.

## Gap

The baseline therefore has a clean missing middle rather than an authority conflict:

- testimony can be remembered;
- objective facts can be represented;
- turn-local subjective interpretation can be represented;
- slow authored developmental variables can be represented;
- but there is no durable typed current state for an arbitrary proposition such as `I currently believe the bridge is closed`, with explicit evidence provenance and later correction.

This means Wayfarer can preserve two contradictory user statements as lived experiences but does not yet have a general typed semantic contract for the subject's current epistemic position toward the underlying claim.

## Why not extend an existing subsystem directly?

Using `WorldAuthority` would incorrectly promote subjective belief into objective truth.

Using `BeliefLedger` would mix arbitrary acquired semantic knowledge with slow cartridge-defined developmental beliefs.

Using `InterpretiveBelief` would turn a deliberately noncanonical turn-local hypothesis into long-term semantic authority.

Using only `MemoryUnit` would retain evidence but force downstream consumers to repeatedly reconstruct current belief from prose history, making results renderer/model dependent and difficult to replay or inspect.

## Experimental candidate

`core/epistemic.py` is being tested as an isolated candidate representation. It deliberately does not enter the production turn loop yet.

The candidate separates:

- immutable evidence records;
- current proposition stance;
- an explicit revision certificate;
- deterministic first-person projection of the current stance.

Recording evidence never automatically changes the current stance. A separate typed revision is required.

## What this baseline does not prove

This architecture inspection proves a representation/ownership gap. It does **not** prove that the candidate ledger improves user-visible character quality.

It also does not yet answer:

- how testimony should be normalized into atomic propositions;
- how relationship trust should affect evidence weighting;
- whether confidence should remain numerical or become categorical;
- how contradictory evidence should be resolved;
- when World Authority should force or merely strongly support revision;
- how model-generated inference should be verified;
- how proposition revisions become canonical replay roots;
- how evidence should be cold-reconstructed under a low-resource runtime;
- whether proposition state materially improves cross-model continuity.

Those are separate experiments. The prototype must not smuggle answers to them into the storage contract.
