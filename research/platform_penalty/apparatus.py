"""Pilot adapters over real Wayfarer decisions, without a second decision loop."""
from contextlib import contextmanager
from dataclasses import asdict, replace
from pathlib import Path
from types import MethodType
from unittest.mock import patch
import hashlib
import json
import time
import uuid

from persona_engine.agent import CharacterAgent
from persona_engine.core.cartridge import load_cartridge
from persona_engine.core.renderer_control import RendererControlService, RendererConfig
from persona_engine.core.renderer import LocalLLMRenderer
from persona_engine.core.expression_bridge import build_expression_messages
from .organization import Organization, ACTIONS, FEATURES
from .specialists import POLICIES

class CapturingRenderer(LocalLLMRenderer):
    def __init__(self):
        super().__init__(model_name='offline-template', provider='offline')
        self.requests = []

    def generate_expression(self, request):
        self.requests.append(build_expression_messages(request))
        return super().generate_expression(request)


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), default=str).encode()).hexdigest()


def origin_path(name):
    return HERE/'fixtures/synthetic.snp' if name == 'synthetic' else ROOT/'persona_engine/cartridges'/f'{name}.snp'


def origin_hash(name):
    return hashlib.sha256(origin_path(name).read_bytes()).hexdigest()


@contextmanager
def clock(tick):
    # Only the single-thread deterministic pilot uses this clock. No hosted/model calls.
    with patch('time.time', return_value=1800000000. + tick * 86.4):
        yield


def open_subject(root, name, instance, *, condition='A', topology=True, inhibition=True):
    """Explicit fresh instantiation in the test harness, not a production migration.

    Override the parsed identity only before initial store binding. Never change
    an existing subject UUID. Source and its original UUID remain in provenance.
    A re-open must supply the identical manifest and fails if it differs.
    """
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    sid = str(uuid.uuid5(uuid.NAMESPACE_URL, 'duck-platform-pilot:' + instance))
    manifest = {'instance':instance,'subject_uuid':sid,'origin_sha256':origin_hash(name),'condition':condition}
    mp = root/'instance.json'
    if mp.exists() and json.loads(mp.read_text()) != manifest:
        raise ValueError('instance manifest mismatch')
    if not mp.exists():
        mp.write_text(json.dumps(manifest, indent=2)+'\n')
    original_loader = load_cartridge
    def instantiate(path):
        identity, ledger, raw = original_loader(path)
        identity = replace(identity, entity_uuid=sid)
        return identity, replace(ledger, immutable=identity), raw
    with clock(0), patch('persona_engine.core.engine.load_cartridge', side_effect=instantiate):
        agent = CharacterAgent(cartridge_path=str(origin_path(name)), db_path=str(root/'subject.sqlite3'), user_id='interlocutor')
        agent.set_renderer(CapturingRenderer())
    if condition == 'B' and topology:
        organization = Organization(json.loads((HERE/'fixtures/organizations.json').read_text())[name])
        chooser = lambda base, f: organization.propose(base, f, inhibition=inhibition)
    elif condition == 'C':
        chooser = lambda base, f: (POLICIES[name](base, f), {'specialist':name})
    else:
        chooser = None
    if chooser:
        engine = agent.engine
        original = engine._resolve_decision_payload
        def resolve(self, *args, **kwargs):
            self._pilot_influence = None
            base = original(*args, **kwargs)
            # Protected decisions remain in the original authority. No soft proposal
            # can erase identity, commitment, value or disclosure constraints.
            if (base['dialogue_act'] == 'protect_boundary' or
                base.get('commitment_evidence', {}).get('active') or
                base.get('value_evidence', {}).get('active')):
                return base
            r = self.relationship
            f = {k:float(k in base.get('triggers', [])) for k in FEATURES}
            f.update(trust=r.trust, guardedness=r.guardedness, conflict=r.unresolved_conflict, suspicion=base.get('suspicion',0))
            action, trace = chooser(base['dialogue_act'], f)
            if action not in ACTIONS:
                raise ValueError('specialist proposed unknown action')
            self._pilot_influence = trace
            return {**base, 'dialogue_act':action}
        engine._resolve_decision_payload = MethodType(resolve, engine)
    return agent


def semantic_snapshot(agent):
    e = agent.engine
    return {
        'identity':asdict(e.identity),
        'relationship':dict(vars(e.relationship)),
        'beliefs':e.belief_ledger.to_state(),
        'commitments':[dict(vars(c)) for c in e.intentions.active_commitments(time.time())],
    }


def turn(agent, text, tick):
    with clock(tick):
        result = agent.say(text)
        snapshot = semantic_snapshot(agent)
    return {
        'text':text, 'output':result.get('response', result.get('text','')),
        'decision':result['decision_payload'], 'state':snapshot,
        'retrieval':result.get('retrieved_memory_trace', []),
        'influence':getattr(agent.engine, '_pilot_influence', None),
        'messages':getattr(agent.engine.renderer, 'requests', [[]])[-1],
        'validation_issues':result.get('validation_issues', []),
        'delivery':result.get('expression_delivery', {}),
    }


def close_subject(agent):
    # Persistence opens/closes each SQLite transaction; no background thread is started.
    agent.engine.stop_idle_loop() if getattr(agent.engine, '_idle_thread', None) else None


def origin_envelope(name):
    """Lossless transport-parity prototype only. No new package/loader authority."""
    text = origin_path(name).read_text()
    _, _, raw = load_cartridge(str(origin_path(name)))
    return {'schema':'origin-review-envelope-v1', 'snp_utf8':text, 'source_sha256':origin_hash(name), 'normalized':raw, 'topology_enabled':False}


def recover_source(envelope):
    if envelope.get('schema') != 'origin-review-envelope-v1' or envelope.get('topology_enabled') is not False:
        raise ValueError('unsupported parity envelope')
    source = envelope['snp_utf8'].encode()
    if hashlib.sha256(source).hexdigest() != envelope['source_sha256']:
        raise ValueError('source checksum mismatch')
    return source
