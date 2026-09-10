"""Read-only donor audit, with disposable-state failure probes."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile


def audit(source):
    source=Path(source).resolve();sys.path.insert(0,str(source))
    from persona_connectome.engine import PersonaConnectomeEngine
    from persona_connectome.models import Node, Edge
    from persona_connectome.renderers import DryRunRenderer
    from persona_connectome.store import PersonaStore
    seed=source/'persona_connectome/personas/pretorius.json'
    raw=json.loads(seed.read_text())
    with tempfile.TemporaryDirectory() as td:
        store=PersonaStore(str(Path(td)/'plastic.db'))
        store.upsert_node(Node('test','concept','test','test',baseline=.5,plasticity=0))
        zero=store.update_node_baseline('test',.1)
        store.upsert_edge(Edge('inhibition','test','test','inhibits',-.5,plasticity=1))
        store.update_edge_weight('inhibition',.1)
        inhibition=store.get_edges()[0].weight
        store.close()
        engine=PersonaConnectomeEngine({'db_path':str(Path(td)/'engine.db'), 'persona_path':str(seed),
            'semantic':{'enabled':False}}, DryRunRenderer())
        before=engine.store.get_node('rel.trust.user').baseline
        engine.step('I do not trust you yet, and you should not assume that I do.',actor='Morgan')
        after=engine.store.get_node('rel.trust.user').baseline
        engine.close()
    return {'source_file_hashes':{str(p.relative_to(source)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(source.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix in ['.py','.json','.md','.toml']},
        'node_count':len(raw['nodes']),'edge_count':len(raw['edges']),
        'evidence_class':'deterministic engineering evidence',
        'probes':{'zero_plasticity_baseline':{'before':.5,'after':zero},
                  'positive_learning_weakens_inhibition':{'before':-.5,'after':inhibition},
                  'Morgan_input_changes_user_relationship':{'before':before,'after':after}},
        'model':None,'scope':'targeted donor review, no transplantation or biological validation'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    result=audit(a.source)
    with Path(a.output).open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='source_file_hashes'}))
