"""Read-only donor inventory plus disposable hostile probes; original is untouched."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import sys
import tempfile


def audit(source):
    source=Path(source).resolve();sys.path.insert(0,str(source))
    from persona_connectome.store import PersonaStore
    from persona_connectome.models import Node,Edge
    from persona_connectome.activation import ActivationEngine
    from persona_connectome.engine import PersonaConnectomeEngine
    from persona_connectome.renderers import DryRunRenderer
    graph=json.loads((source/'persona_connectome/personas/pretorius.json').read_text())
    with tempfile.TemporaryDirectory() as td:
        s=PersonaStore(Path(td)/'sign.db')
        for id,baseline in [('x',0),('y',1),('z',0)]: s.upsert_node(Node(id,'concept',id,'',baseline=baseline,keywords=(id,)))
        s.upsert_edge(Edge('xy','x','y','inhibits',-1.))
        s.upsert_edge(Edge('yz','y','z','supports',1.))
        result=ActivationEngine(s,hops=2,damping=.62,inertia=0).run(1,'x','neutral')
        signed={'activation':result.activations,'issue':'downstream z receives positive signal after inhibition of y because frontier uses abs(new-old)'}
        s.upsert_node(Node('zero','relationship','zero','',baseline=.5,plasticity=0.))
        zero=s.update_node_baseline('zero',.1)
        s.close()
        engine=PersonaConnectomeEngine({'db_path':str(Path(td)/'actor.db'),'persona_path':str(source/'persona_connectome/personas/pretorius.json')},DryRunRenderer())
        before=engine.store.get_node('rel.trust.user').baseline
        engine.step('I trust you. This is between us, a secret.',actor='Morgan')
        after=engine.store.get_node('rel.trust.user').baseline
        original=json.loads((source/'persona_connectome/personas/pretorius.json').read_text())
        engine.close()
    owners={'identity':'genesis.identity_anchor','self_model':'genesis.self_model_claim','value':'genesis.value',
        'belief':'genesis.authored_belief_prior','motive':'genesis.regulatory_disposition','goal':'genesis.initial_goal_proposal',
        'emotion':'genesis.appraisal_disposition','relationship':'genesis.relationship_template_prior',
        'memory':'genesis.authored_biography_pending_provenance_review','style':'genesis.expression',
        'behavior':'genesis.procedure_proposal','concept':'genesis.associative_concept'}
    mapping=[]
    for n in graph['nodes']:
        mapping.append({'old_id':n['id'],'old_type':n['type'],'proposed_owner':owners.get(n['type'],'unresolved'),
            'semantic_ref':n['id'],'expression_ref':'expression:'+n['id'],
            'authored_baseline':n['baseline'],'runtime_activation_import':False,
            'protected':n['protected'],'plasticity_requires_review':bool(n['plasticity']),
            'source_provenance':'uploaded authored prototype; assertions are not verified lived events',
            'review_required':n['type'] in {'memory','belief','relationship','emotion','motive','goal','self_model'}})
    return {'source_files':{str(p.relative_to(source)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(source.rglob('*')) if p.is_file() and '__pycache__' not in str(p)},
        'node_count':len(graph['nodes']),'edge_count':len(graph['edges']),
        'node_types':dict(collections.Counter(n['type'] for n in graph['nodes'])),'edge_kinds':dict(collections.Counter(e['kind'] for e in graph['edges'])),
        'probes':{'inhibition_sign':signed,'zero_plasticity_baseline_after_update':zero,'actor_Morgan_changed_user_trust':{'before':before,'after':after}},
        'node_migration_map':mapping,
        'edge_migration_map':[{'old_id':e['id'],'old_kind':e['kind'],'source_ref':e['source'],'target_ref':e['target'],'authored_weight':e['weight'],'learned_delta':0.,'status':'quarantine_until_kind_semantics_reviewed','evidence_refs':[],'original':e} for e in graph['edges']]}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    out=Path(a.output)
    with out.open('x') as f: json.dump(audit(a.source),f,indent=2);f.write('\n')
