# Personal Journal Artifact

The personal journal is a character-owned notebook, not a replacement for
memory and not an objective authority.

```text
Memory: what survives experience
Journal: what the character deliberately chose to write
WorldEvent: the entry physically exists in the notebook
```

Entries are bounded, append-only records in session persistence and can be
materialized as a plain UTF-8 `.journal.txt` file beside the session database.
The structured record preserves ordering and provenance for replay and C99
porting; the text file remains readable as an ordinary notebook.

Reading the journal creates a new `journal_reading` world event and subjective
experience. The words may support or contradict recollection, but prove only
that the words were written. Writing and reading are available through the
approved `write_journal` and `read_journal` World Authority action channel.

Genesis episodes may contain deliberate journal entries. They are not created
for every event, and their wording may be defensive, incomplete, mistaken, or
self-serving.
