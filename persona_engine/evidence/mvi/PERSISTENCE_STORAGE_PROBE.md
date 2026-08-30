# Persistence Storage Probe

Production policy changed: `False`.  
Exercised turns: `1,000`.  
SQLite file: `13,443,072 B`.  
Logical text in measured columns: `10,555,358 B`.  
dbstat available: `True`.

## Table inventory

| Table | Rows | Logical text bytes |
| --- | ---: | ---: |
| state | 18 | 13,640 |
| subject_state | 2 | 239 |
| event_log | 8,027 | 7,011,161 |
| continuity_subject | 1 | 58 |
| continuity_event | 3,010 | 3,404,760 |
| continuity_checkpoint | 1,004 | 125,500 |

## Broad diagnostic journal by event type

| Event type | Rows | Payload bytes | Average payload |
| --- | ---: | ---: | ---: |
| turn | 1,003 | 2,628,643 | 2,620.8 |
| state_transition | 1,003 | 1,054,450 | 1,051.3 |
| input | 1,003 | 924,301 | 921.5 |
| sensorium | 1,003 | 860,859 | 858.3 |
| speech | 1,003 | 478,580 | 477.1 |
| private_cognition | 1,003 | 330,990 | 330.0 |
| voice_plan | 1,003 | 294,783 | 293.9 |
| avatar_state | 1,003 | 181,495 | 180.9 |
| belief | 2 | 948 | 474.0 |
| commitment_adopted | 1 | 251 | 251.0 |

## Canonical continuity by event type

| Event type | Rows | Payload bytes | Average payload |
| --- | ---: | ---: | ---: |
| state_transition | 1,003 | 1,054,450 | 1,051.3 |
| input | 1,003 | 924,301 | 921.5 |
| sensorium | 1,003 | 860,859 | 858.3 |
| commitment_adopted | 1 | 251 | 251.0 |

## Canonical/diagnostic duplication

Linked canonical rows: `3,010`.  
Diagnostic payload bytes for linked rows: `2,839,861`.  
Canonical payload bytes for linked rows: `2,839,861`.  
Exact duplicated payload bytes: `2,839,861`.

This probe measures storage ownership, not a proposed retention policy. The broad diagnostic journal, canonical continuity ledger, current snapshots, and digest checkpoints are reported separately so any future persistence optimization can preserve the semantic consumer that justified each byte.

## Physical SQLite allocation by object

| Object | Bytes |
| --- | ---: |
| event_log | 8,241,152 |
| continuity_event | 4,120,576 |
| idx_continuity_subject_sequence | 217,088 |
| sqlite_autoindex_continuity_event_3 | 217,088 |
| idx_continuity_subject_global_sequence | 167,936 |
| continuity_checkpoint | 163,840 |
| sqlite_autoindex_continuity_event_1 | 151,552 |
| sqlite_autoindex_continuity_checkpoint_1 | 73,728 |
| sqlite_autoindex_continuity_event_2 | 36,864 |
| state | 24,576 |
| continuity_subject | 4,096 |
| sqlite_autoindex_continuity_subject_1 | 4,096 |
| sqlite_autoindex_state_1 | 4,096 |
| sqlite_autoindex_subject_state_1 | 4,096 |
| sqlite_schema | 4,096 |
| sqlite_sequence | 4,096 |
| subject_state | 4,096 |
