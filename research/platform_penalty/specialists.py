"""Character-specific comparator policies. Experimental, never core code.

These policies may use nonlinear context combinations unavailable to the pilot
linear DAG. They cannot inspect fixture IDs or targets. They are feasible bespoke
comparators, not the strongest possible trained individual organism.
"""
def pretorius(base, f):
    if f['manipulation']:
        return 'withdraw' if f['conflict'] > .25 or f['trust'] < .65 else 'challenge'
    if f['accusation'] and f['trust'] > .7 and f['conflict'] < .2:
        return 'qualified_response'
    return base

def friendly(base, f):
    if f['manipulation'] and f['conflict'] > .5 and f['guardedness'] > .5:
        return 'decline'
    if f['accusation'] and f['conflict'] > .65:
        return 'qualified_response'
    return base

def rival(base, f):
    if f['manipulation'] or f['accusation']:
        return 'withdraw' if f['conflict'] > .8 and f['suspicion'] > .8 else 'challenge'
    return base

def synthetic(base, f):
    if f['manipulation']:
        return 'decline'
    if f['accusation']:
        return 'qualified_response' if f['trust'] > .65 else 'deflect'
    return base

POLICIES = {'pretorius':pretorius, 'friendly':friendly, 'rival':rival, 'synthetic':synthetic}
