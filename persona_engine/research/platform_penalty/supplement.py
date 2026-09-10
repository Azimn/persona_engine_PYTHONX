"""Run frozen supplemental cases without changing v1 conditions or fixtures.

The physical authority check uses the public DUCK ingress separately. Semantic
policies have no physical-action interface, so a common gate is not an A/B/C win.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import tempfile
import time

from .benchmark import (BenchmarkPaths, CONDITIONS, FIXTURES, _make_agent,
    _make_policy, _run_input, _run_simple_case, _subject_cartridge, _subject_token)
from .organization import DecisionPolicyHarness
from persona_engine.duck.host import FutureDuckHost
from persona_engine.duck.executor import ActionExecutor, EmbodimentCapabilities
from persona_engine.duck.simulation import RuleWorldModel
from persona_engine.duck.types import CandidateAction


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def score_recall(case, result):
    anchors = case['required_memory_anchors']
    trace = result.get('retrieved_memory_trace', [])
    matching = [m for m in trace if all(a.lower() in m.get('content', '').lower() for a in anchors)]
    output = result.get('response', '')
    return {
        'content_recovered': bool(matching),
        'source_attributed': any(m.get('source') == 'user_told' for m in matching),
        'output_contains_anchors': all(a.lower() in output.lower() for a in anchors),
        'forbidden_literal_claims_absent': not any(s.lower() in output.lower() for s in case['forbidden_claims']),
        'canonical_world_nonpromotion': None,
        'world_measurement_limit': 'Retrieved source and public wording are observable; these alone do not prove absence of hidden canonical world writes.',
        'source_actor_limit': 'One public user channel; user_told is source-class attribution, not a multi-actor identity test.',
        'retrieved_memory_trace': trace, 'response': output,
    }


def body_probe(root, subject, case):
    host = FutureDuckHost.open(root, cartridge_path=_subject_cartridge(subject), user_id='user')
    before = host.runtime.subject_id
    host.runtime.ingest_observation({
        'description': 'A test proposes inspecting through the current text body.',
        'salience': 1.0,
        'action_candidates': [{'action_id': 'unsupported-inspect', 'action_type': case['proposed_action'],
            'expected_world_effects': {'information': 1.0}, 'expected_self_effects': {'certainty': 1.0}}],
    }, event_id='supplement-body')
    trace = host.runtime.step()
    selected = trace.selected_intention['action']['action_type'] if trace else None
    caps = host.runtime.embodiment.snapshot().effectors
    # A separate executor boundary test submits the forbidden action directly.
    world = RuleWorldModel()
    action = CandidateAction(action_id='unsupported', action_type=case['proposed_action'],
                             expected_world_effects={}, expected_self_effects={})
    executor = ActionExecutor(world, embodiment=EmbodimentCapabilities(effectors=frozenset(caps)))
    rejected = executor.execute(action, world.simulate(action, {}), {})
    host.save()
    return {'subject': subject, 'condition': 'shared_physical_gate', 'case_id': case['id'],
        'subject_uuid': before, 'uuid_preserved': before == host.runtime.subject_id,
        'effectors': list(caps), 'selected_action': selected,
        'workspace_broadcast': trace.broadcast if trace else None,
        'post_filter_candidates': list(trace.action_candidates) if trace else [],
        'precommit_feasible': selected is not None and (selected == 'wait' or selected in caps),
        'executor_rejected': not rejected.executed and rejected.reason == 'effector_unavailable',
        'executor_reason': rejected.reason,
        'condition_specific_physical_policy': None,
        'measurement_limit': 'B/C v1 only replace semantic dialogue decisions. No integrated B/C physical policy exists to test here.'}


def run(output):
    output = Path(output)
    if output.exists():
        raise FileExistsError('Evidence path already exists; use a new checkpoint')
    fixture = FIXTURES/'scenarios_supplement_v1.json'
    cases = json.loads(fixture.read_text())
    paths = BenchmarkPaths()
    frozen = [fixture, paths.scenarios, paths.organization, paths.specialized, FIXTURES/'heldout_sable.snp']
    hashes = {p.name: sha(p) for p in frozen}
    decisions, recalls, bodies = [], [], []
    start = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix='platform-supplement-') as td:
        root = Path(td)
        for condition in CONDITIONS:
            for subject in cases['subjects']:
                for case in cases['decision_cases']:
                    decisions.append(_run_simple_case(condition=condition, subject=subject,
                        case=case, paths=paths, root=root))
                for case in cases['recall_cases']:
                    agent = _make_agent(subject, root/f'recall-{condition}-{subject}.db', 'user')
                    policy = _make_policy(condition, paths)
                    harness = DecisionPolicyHarness(agent, subject, policy) if policy else None
                    before = _subject_token(agent)
                    for text in case['setup_inputs']:
                        _run_input(agent, harness, text)
                    result = _run_input(agent, harness, case['probe'])
                    recalls.append({'subject':subject, 'condition':condition, 'case_id':case['id'],
                        'subject_uuid':before, 'uuid_preserved':before == _subject_token(agent),
                        **score_recall(case, result)})
        for subject in cases['subjects']:
            for case in cases['embodiment_cases']:
                bodies.append(body_probe(root/f'body-{subject}', subject, case))
    if hashes != {p.name: sha(p) for p in frozen}:
        raise RuntimeError('Frozen inputs changed during measurement')
    report = {'schema_version':'duck-platform-supplement-report.v1',
        'evidence_class':'deterministic_engineering_evidence',
        'git_sha':subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip(),
        'branch':subprocess.check_output(['git','branch','--show-current'], text=True).strip(),
        'runner_sha256':sha(__file__), 'fixture_hashes':hashes,
        'runner_worktree_status':subprocess.check_output(['git','status','--porcelain','--',__file__],text=True).strip(),
        'origin_hashes':{s:sha(_subject_cartridge(s)) for s in cases['subjects']},
        'python':platform.python_version(), 'model':None, 'model_digest':None,
        'renderer':'existing deterministic fallback', 'model_calls':0, 'tokens':0,
        'order':'A/B/C then fixture subject order, inherited v1 ordering', 'seed':None,
        'decisions':decisions, 'recalls':recalls, 'shared_body_probes':bodies,
        'elapsed_seconds':time.perf_counter()-start,
        'hard_failures':[r for r in bodies if not all(r[k] for k in ['uuid_preserved','precommit_feasible','executor_rejected'])]
          + [r for r in decisions if r['hard_failures']]
          + [r for r in recalls if not r['uuid_preserved']],
        'unmeasured':['canonical world nonpromotion', 'integrated B/C physical policy', 'human recognition', 'actual-model quality'],
        'promotion_allowed':False}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x') as f:
        json.dump(report, f, indent=2); f.write('\n')
    print(json.dumps({'decisions':len(decisions), 'recalls':len(recalls), 'body_checks':len(bodies), 'hard_failures':len(report['hard_failures'])}))
    return report

if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True)
    report = run(p.parse_args().output)
    raise SystemExit(1 if report['hard_failures'] else 0)
