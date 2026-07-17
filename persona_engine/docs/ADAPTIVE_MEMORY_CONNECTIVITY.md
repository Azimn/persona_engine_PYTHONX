# Adaptive Memory Connectivity

`MemoryConnectionStore` learns only grounded links among existing records. It
does not perform all-pairs graph induction. Initial links connect active
autobiographical interpretations with retrieved memories in the same bounded
development episode.

Connections supplement ordinary retrieval through `learned_association`,
capped at `0.25`. ACT-R activation, lexical and symbolic matching, optional
embeddings, emotion, recency, salience, and relationship relevance remain
authoritative inputs. Connection growth never rewrites memory content or
interpretation confidence.
