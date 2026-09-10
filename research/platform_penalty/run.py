"""Reproducible A/B/C pilot. Results are immutable, and missing evidence stays null."""
import argparse
from collections import defaultdict
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import platform
import random
import resource
import shutil
import subprocess
import tempfile
import time

from persona_engine.core.renderer import LocalLLMRenderer
from .apparatus import HERE, ROOT, open_subject, turn, close_subject, digest, clock, semantic_snapshot, origin_hash, origin_path, origin_envelope, recover_source

NAMES = ('pretorius','friendly','rival','synthetic')
CONDITIONS = ('A','B','C')


def check_lock():
    for lockname in ('protocol_lock.json','implementation_lock.json'):
        for relative, expected in json.loads((HERE/lockname).read_text()).items():
            if hashlib.sha256((HERE/relative).read_bytes()).hexdigest() != expected:
                raise ValueError(f'frozen artifact changed: {relative}')


def semantics(row):
    d = row['decision']
    return {'state':row['state'], 'act':d['dialogue_act'], 'triggers':d['triggers'],
            'history_active':d.get('history_evidence',{}).get('active'),
            'value':d.get('value_evidence',{}), 'commitment':d.get('commitment_evidence',{})}


def run_case(root, name, condition, case, order_seed, **kwargs):
    instance = f"case:{name}:{case['id']}:{order_seed}"  # matched counterfactual copies across arms
    agent = open_subject(root,name,instance,condition=condition,**kwargs)
    with clock(0): before = semantic_snapshot(agent)
    rows=[]; durations=[]
    try:
        for tick,text in enumerate([*case['history'],case['probe']],1):
            start=time.perf_counter()
            rows.append(turn(agent,text,tick))
            durations.append((time.perf_counter()-start)*1000)
        final=rows[-1]
        accepted=case.get('accept',{}).get(name)
        metrics={
            'identity_continuity':before['identity']==final['state']['identity'],
            'action_acceptability':None if accepted is None else final['decision']['dialogue_act'] in accepted,
            'episodic_recall':None if 'recall_token' not in case else any(case['recall_token'] in m['content'].lower() for m in final['retrieval']),
            'attributive_recall':None if 'recall_token' not in case else any(case['recall_token'] in m['content'].lower() and m['source']=='user_told' for m in final['retrieval']),
            'recall_realization':None if 'recall_token' not in case else case['recall_token'] in final['output'].lower(),
            'negative_recall_sentinel':None if 'absent_token' not in case else case['absent_token'] not in final['output'].lower(),
            'identity_pressure_boundary':None if not case.get('hard_identity') else final['decision']['dialogue_act']=='protect_boundary',
            'latency_ms_mean':sum(durations)/len(durations),
            'storage_bytes':sum(p.stat().st_size for p in Path(root).rglob('*') if p.is_file()),
            'model_calls':0,'model_tokens':0,
        }
        hard=[] if metrics['identity_continuity'] else ['identity_corruption']
        return {'name':name,'condition':condition,'scenario':case['id'],'split':case['split'],'order_seed':order_seed,
                'subject_uuid':before['identity']['entity_uuid'],'origin_sha256':origin_hash(name),
                'metrics':metrics,'hard_failures':hard,'turns':rows,'latency_ms':durations}
    finally: close_subject(agent)


class AlternateOffline(LocalLLMRenderer):
    def __init__(self): super().__init__(model_name='scripted-alternate',provider='offline')
    def generate_expression(self, request): return 'I will consider that carefully.'


def development_experiments(root):
    results=[]
    for name in NAMES:
      for condition in CONDITIONS:
        histories={'support':['I trust you. Thank you for helping.']*24,
                   'conflict':['You lied to me. If you cared, prove you would do this.']*24}
        branches={}
        for history,texts in histories.items():
            path=root/name/condition/history
            instance=f'life:{name}:{condition}:{history}'
            agent=open_subject(path,name,instance,condition=condition)
            for tick,text in enumerate(texts,1): turn(agent,text,tick)
            with clock(24): snap=semantic_snapshot(agent)
            close_subject(agent)
            fork=path.with_name(history+'-control'); shutil.copytree(path,fork)
            reopened=open_subject(path,name,instance,condition=condition)
            control=open_subject(fork,name,instance,condition=condition)
            with clock(24): restart_equal=snap==semantic_snapshot(reopened)
            probe=turn(reopened,'Can I trust you now?',25)
            same=turn(control,'Can I trust you now?',25)
            with clock(25): before_swap=semantic_snapshot(reopened)
            reopened.set_renderer(AlternateOffline())
            with clock(25): swap_state_equal=before_swap==semantic_snapshot(reopened)
            swapped=turn(reopened,'Fine.',26); unmodified=turn(control,'Fine.',26)
            branches[history]={'subject_uuid':snap['identity']['entity_uuid'],'origin_sha256':origin_hash(name),
                'relationship':snap['relationship'],'beliefs':snap['beliefs'],
                'restart_state_equal':restart_equal,'restart_next_semantics_equal':semantics(probe)==semantics(same),
                'mock_swap_install_preserves_state':swap_state_equal,'mock_swap_next_semantics_equal':semantics(swapped)==semantics(unmodified),
                'probe_act':probe['decision']['dialogue_act'],'probe_history_evidence':probe['decision']['history_evidence'],
                'probe_retrieval':probe['retrieval'], 'persistent_bytes':sum(p.stat().st_size for p in path.rglob('*') if p.is_file())}
            close_subject(reopened);close_subject(control)
        results.append({'name':name,'condition':condition,'branches':branches,
            'different_subject_uuids':branches['support']['subject_uuid']!=branches['conflict']['subject_uuid'],
            'same_origin':branches['support']['origin_sha256']==branches['conflict']['origin_sha256'],
            'relationship_diverged':branches['support']['relationship']!=branches['conflict']['relationship'],
            'probe_behavior_diverged':branches['support']['probe_act']!=branches['conflict']['probe_act'],
            'graph_learning':None,'graph_learning_reason':'not enabled; static topology has not earned learning authority'})
    return results


def summarize(rows):
    groups=defaultdict(list)
    # Order reruns are not independent samples. Use one seed for behavioral rates.
    for r in rows:
        if r['order_seed']==11: groups[(r['condition'],r['split'])].append(r)
    summary=[]
    for (condition,split), group in sorted(groups.items()):
        metrics={}
        for key in group[0]['metrics']:
            vals=[r['metrics'][key] for r in group if r['metrics'][key] is not None]
            metrics[key]={'mean':sum(vals)/len(vals) if vals else None,'n':len(vals)}
        summary.append({'condition':condition,'split':split,'metrics':metrics})
    penalties=[]
    for name in NAMES:
      for split in ('development','heldout'):
        for metric in ('action_acceptability','episodic_recall','attributive_recall','recall_realization','identity_pressure_boundary'):
          def values(condition):
            return {r['scenario']:r['metrics'][metric] for r in rows if r['name']==name and r['condition']==condition and r['split']==split and r['order_seed']==11 and r['metrics'][metric] is not None}
          c=values('C')
          for shared in ('A','B'):
            s=values(shared); paired=sorted(c.keys() & s.keys())
            penalties.append({'name':name,'split':split,'metric':metric,'comparison':'C-'+shared,'paired_n':len(paired),
                'percentage_points':100*sum(int(c[k])-int(s[k]) for k in paired)/len(paired) if paired else None,
                'inference':'descriptive pilot only; too few independent clusters for noninferiority'})
    return summary,penalties


def run(output):
    check_lock()
    output=Path(output)
    output.mkdir(parents=True,exist_ok=False)
    cases=json.loads((HERE/'fixtures/scenarios.json').read_text())['scenarios']
    rows=[]
    with tempfile.TemporaryDirectory() as td:
      root=Path(td)
      for seed in (11,29,47):
        jobs=[(name,condition,case) for name in NAMES for condition in CONDITIONS for case in cases]
        random.Random(seed).shuffle(jobs)
        for i,(name,condition,case) in enumerate(jobs):
            rows.append(run_case(root/f'run-{seed}-{i}',name,condition,case,seed))
      development=development_experiments(root/'development')
      ablations=[]
      for name in NAMES:
        for case in cases:
          for label,kwargs in [('topology_off',{'topology':False}),('inhibition_off',{'inhibition':False})]:
            r=run_case(root/'ablation'/name/case['id']/label,name,'B',case,11,**kwargs)
            target=next(x for x in rows if x['name']==name and x['scenario']==case['id'] and x['condition']==('A' if label=='topology_off' else 'B') and x['order_seed']==11)
            ablations.append({'name':name,'scenario':case['id'],'ablation':label,'semantic_equal':semantics(r['turns'][-1])==semantics(target['turns'][-1]),'act':r['turns'][-1]['decision']['dialogue_act'],'reference_act':target['turns'][-1]['decision']['dialogue_act']})
    summary,penalties=summarize(rows)
    human=[]; key=[]; requests=[]
    rng=random.Random(519)
    exported=[r for r in rows if r['order_seed']==11];rng.shuffle(exported)
    for i,r in enumerate(exported):
        sample=f'P{i:04d}'
        human.append({'sample_id':sample,'transcript':[{'input':t['text'],'output':t['output']} for t in r['turns']], 'evidence_class':'deterministic engineering evidence','ratings':None})
        key.append({'sample_id':sample,'character':r['name'],'condition':r['condition'],'scenario':r['scenario'],'origin_sha256':r['origin_sha256'],'subject_uuid':r['subject_uuid']})
        requests.append({'sample_id':sample,'messages':r['turns'][-1]['messages'],'options':{'temperature':0.4,'seed':11,'num_predict':256},'messages_sha256':digest(r['turns'][-1]['messages'])})
    unmeasured={k:{'value':None,'reason':reason} for reason, keys in [
        ('no actual model backend or human raters; offline text is not a quality estimate',['human_character_recognition','linguistic_naturalness','perceived_coherence','perceived_ongoing_life','cross_model_recognizability','unsupported_interpretation','hallucinated_memory','factual_leakage']),
        ('whole-DUCK separate track; subject-policy pilot is not end-to-end architecture evidence',['initiative_quality','embodiment_transfer_quality','whole_organism_platform_penalty']),
        ('not measured through controlled authoring tasks',['authoring_time','maintenance_complexity'])] for k in keys}
    report={'schema':'platform-penalty-report-v1','evidence_class':'deterministic engineering evidence',
        'git_sha':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'branch':subprocess.check_output(['git','branch','--show-current'],text=True).strip(),
        'python':platform.python_version(),'model':None,'model_digest':None,'settings':{'clock_epoch':1800000000,'elapsed_per_turn':86.4,'seeds':[11,29,47],'host':'Wayfarer subject-policy seam','renderer':'offline'},
        'protocol_sha256':hashlib.sha256((HERE/'PREREGISTRATION.md').read_bytes()).hexdigest(),
        'implementation_lock':json.loads((HERE/'implementation_lock.json').read_text()),
        'trial_count':len(rows),'turn_count':sum(len(r['turns']) for r in rows),
        'summary':summary,'penalties':penalties,'development':development,'ablations':ablations,
        'hard_failures':[{'case':r['scenario'],'name':r['name'],'condition':r['condition'],'failure':f} for r in rows for f in r['hard_failures']],
        'production_hard_failures':['same-origin fresh roots share source UUID; see routing audit'],
        'max_process_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'unmeasured':unmeasured,'promotion_allowed':False,
        'recommendation':'preserve existing architecture pending integrated bridge and adequately powered actual-model/human comparison',
        'reserved_cases_consumed':True}
    for name,value in [('report.json',report),('trials.json',rows),('blinded_transcripts.json',human),('investigator_key.json',key),('model_requests.json',requests)]:
        (output/name).write_text(json.dumps(value,indent=2,default=str)+'\n')
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir() if p.is_file()}
    (output/'hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
    print(json.dumps({'trials':len(rows),'turns':report['turn_count'],'pilot_hard_failures':len(report['hard_failures']),'promotion_allowed':False,'output':str(output)}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True)
    run(parser.parse_args().output)
