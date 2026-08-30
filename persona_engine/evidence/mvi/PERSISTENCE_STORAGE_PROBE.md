# Persistence Storage Probe

Production policy changed: `False`.  
Exercised turns: `1,000`.  
SQLite file: `6,782,976 B`.  
Logical text in measured columns: `4,379,652 B`.  
dbstat available: `True`.

## Table inventory

| Table | Rows | Logical text bytes |
| --- | ---: | ---: |
| state | 18 | 13,628 |
| subject_state | 2 | 237 |
| event_log | 603 | 527,396 |
| consolidation_evidence | 8,027 | 308,073 |
| continuity_subject | 1 | 58 |
| continuity_event | 3,010 | 3,404,760 |
| continuity_checkpoint | 1,004 | 125,500 |

## Broad diagnostic journal by event type

| Event type | Rows | Payload bytes | Average payload |
| --- | ---: | ---: | ---: |
| turn | 76 | 199,322 | 2,622.7 |
| state_transition | 75 | 78,832 | 1,051.1 |
| input | 75 | 69,158 | 922.1 |
| sensorium | 75 | 64,350 | 858.0 |
| speech | 75 | 35,714 | 476.2 |
| private_cognition | 75 | 24,750 | 330.0 |
| voice_plan | 76 | 22,297 | 293.4 |
| avatar_state | 76 | 13,756 | 181.0 |

## Canonical continuity by event type

| Event type | Rows | Payload bytes | Average payload |
| --- | ---: | ---: | ---: |
| state_transition | 1,003 | 1,054,450 | 1,051.3 |
| input | 1,003 | 924,301 | 921.5 |
| sensorium | 1,003 | 860,859 | 858.3 |
| commitment_adopted | 1 | 251 | 251.0 |

## Canonical/diagnostic duplication

Linked canonical rows: `225`.  
Diagnostic payload bytes for linked rows: `212,340`.  
Canonical payload bytes for linked rows: `212,340`.  
Exact duplicated payload bytes: `212,340`.

This probe measures storage ownership, not a proposed retention policy. The broad diagnostic journal, canonical continuity ledger, current snapshots, and digest checkpoints are reported separately so any future persistence optimization can preserve the semantic consumer that justified each byte.

## Physical SQLite allocation by object

| Object | Bytes |
| --- | ---: |
| continuity_event | 4,120,576 |
| event_log | 626,688 |
| consolidation_evidence | 495,616 |
| idx_consolidation_evidence_stream_time | 364,544 |
| idx_continuity_subject_sequence | 217,088 |
| sqlite_autoindex_continuity_event_3 | 217,088 |
| idx_continuity_subject_global_sequence | 167,936 |
| continuity_checkpoint | 163,840 |
| sqlite_autoindex_continuity_event_1 | 151,552 |
| sqlite_autoindex_consolidation_evidence_1 | 94,208 |
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
