# Semantic Substrate

`SemanticSubstrate` is a small read-only commonsense layer beneath situated
synthesis. It answers only four bounded questions:

- What generic concept was observed?
- Which features usually apply to that kind of thing?
- Which nearby concepts become relevant through one relation hop?
- Which affordances may be worth considering?

It does not decide what is objectively present, what the character believes,
or what action should be taken.

## Authority Boundary

```text
structured observed concept IDs
    -> read-only semantic graph
    -> bounded SemanticActivationFrame
    -> at most three semantic synthesis candidates
    -> existing situated synthesis and action selection
```

Only World Authority may establish instance facts. A generic assertion such as
`locked -> restricted_access = usually` does not establish ownership,
permission, danger, contents, or motive for a particular object. Affordances
are candidates and still pass through normal action selection and World
Authority validation.

The substrate never writes beliefs, memories, relationships, intentions,
pressures, habits, or world facts. It performs no prose extraction and accepts
only structured concept IDs or exact concept names from an approved host path.

## Representation

The base data lives in `persona_engine/semantic_data/core_semantics.json`.
Concepts, features, and relations have stable integer IDs for later flat-array
C99 fixtures. Assertions carry a five-valued state:

- `unknown`
- `false`
- `true`
- `usually`
- `sometimes`

Unknown is never treated as false. Direct assertions override the nearest
inherited assertion. Runtime activation is deterministic, one-hop, and capped
at 12 concepts, 16 features, and 8 affordances. Sparse explicit feature
profiles provide cheap overlap without embeddings or model calls.

## Current Pilot

The pilot contains a deliberately tiny set of physical-object, container,
access, tool, material, and inheritance examples. It is an interface and
behavioral proof, not a production ontology. Expansion should follow observed
scenario failures and remain reviewed, source-traced, and bounded.

## Prototype Measurements

Measured on the local development machine with the 17-concept pilot:

- semantic data file: 3,876 bytes;
- representative activation frame: 3,453 bytes of compact JSON;
- activation of two concepts: about 40.8 microseconds;
- three semantic candidates added about 1.18 microseconds to synthesis;
- deterministic performance planning: about 0.97 microseconds and 272 bytes;
- added idle-tick cost: none;
- new independently mutable persistence fields: none.

These are implementation measurements, not cross-platform performance claims.
