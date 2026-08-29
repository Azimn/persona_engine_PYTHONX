# Contextual Cold-Biography Probe

Passed: `True`.  
Production policy changed: `False`.

Positive query: `Is the lighthouse lens color still the same?`  
Positive topical anchors: `color, lens, lighthouse`  
Cold target recovered: `True`  
Existing live retrieval recovered target: `False`.

Never-happened negative admitted a candidate: `False`.  
Anchorless broad query admitted a candidate: `False`.  
Read-through remained transient: `True`.  
Existing unresolved-history conduct remained intact: `True`.

A grounded topical continuation can recover a cold canonical episode without embedding the remembered value in the query. Queries without enough topical anchors and never-happened compound topics fail closed. This probe does not yet integrate contextual read-through into the main turn pipeline.
