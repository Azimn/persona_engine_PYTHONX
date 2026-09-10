"""Read-only authored influence; it owns neither facts nor continuation state.

Only bounded action-preference proposals leave this module. Identity, memory,
relationships, commitments, and learning remain in existing Wayfarer authorities.
This is a seam-level experimental condition, not a production graph substrate.
"""
from dataclasses import dataclass
import math

ACTIONS = frozenset({'respond', 'qualified_response', 'withdraw', 'challenge', 'deflect', 'decline', 'redirect'})
FEATURES = frozenset({'trust', 'guardedness', 'conflict', 'suspicion', 'manipulation', 'accusation', 'contradiction', 'disrespect', 'intimacy_too_fast', 'boredom', 'emotional_overload'})

@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    kind: str
    weight: float
    evidence: str

class Organization:
    def __init__(self, raw):
        if raw.get('schema') != 'pilot-organization-v1':
            raise ValueError('unsupported organization schema')
        self.edges = tuple(Edge(**e) for e in raw.get('edges', []))
        if len(self.edges) > 64:
            raise ValueError('edge budget exceeded')
        self.nodes = frozenset(raw.get('intermediates', []))
        if len(self.nodes) > 32 or any(not n.startswith('disposition:') for n in self.nodes):
            raise ValueError('invalid intermediate node')
        pairs = set()
        for e in self.edges:
            if e.kind not in {'supports', 'inhibits'} or not e.evidence:
                raise ValueError('typed provenance required')
            if not math.isfinite(e.weight) or not 0 <= e.weight <= 1:
                raise ValueError('weight outside bounds')
            if e.source not in FEATURES | self.nodes or e.target not in ACTIONS | self.nodes:
                raise ValueError('unknown reference or authority target')
            if (e.source, e.target, e.kind) in pairs:
                raise ValueError('duplicate edge')
            pairs.add((e.source,e.target,e.kind))
        # A DAG is the simplest interpretable pilot; recurrent dynamics are not earned.
        pending = set(self.nodes)
        order = []
        while pending:
            ready = sorted(n for n in pending if not any(e.target == n and e.source in pending for e in self.edges))
            if not ready:
                raise ValueError('recurrent topology not supported in pilot')
            order.extend(ready)
            pending.difference_update(ready)
        self.order = tuple(order)

    def scores(self, features, *, inhibition=True):
        values = {k: max(0., min(1., float(features.get(k, 0)))) for k in FEATURES}
        trace = []
        for target in (*self.order, *sorted(ACTIONS)):
            terms = []
            for e in self.edges:
                if e.target != target or (e.kind == 'inhibits' and not inhibition):
                    continue
                delta = values.get(e.source, 0.) * e.weight * (-1 if e.kind == 'inhibits' else 1)
                terms.append(delta)
                trace.append({'source':e.source,'target':target,'delta':delta,'evidence':e.evidence})
            values[target] = max(-1., min(1., sum(terms)))
        return {a: values[a] for a in ACTIONS}, trace

    def propose(self, base, features, *, inhibition=True):
        scores, trace = self.scores(features, inhibition=inhibition)
        # Continuity of the existing policy has explicit inertia, not absolute authority.
        scores[base] = scores.get(base, 0.) + .35
        winner = min(scores, key=lambda a: (-scores[a], a))
        return winner, {'scores':scores, 'influences':trace}
