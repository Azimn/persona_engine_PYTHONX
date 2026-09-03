from copy import deepcopy
from dataclasses import replace
import json
from persona_engine.core.expression_bridge import build_expression_messages, build_expression_messages_v2
from persona_engine.tests.test_expression_bridge import _request


def test_v3_separates_current_turn_and_provenance_without_ready_made_sentences():
    request=_request('trusted')
    request.resolved_state['experience_context']['voice']['authored_examples']=['EXAMPLE_MARKER']
    before=deepcopy(request)
    messages=build_expression_messages(request)
    assert 'EXPRESSION MESSAGES v3' in messages[0]['content']
    assert messages[-1]['content']==request.resolved_state['user_text']
    assert 'EXAMPLE_MARKER' not in json.dumps(messages)
    assert 'EXAMPLE_MARKER' in json.dumps(build_expression_messages_v2(request))
    assert 'Project Orchid is confidential' in messages[1]['content']
    assert 'Project Orchid is confidential' not in messages[0]['content']
    assert request==before


def test_v3_operational_memory_metadata_does_not_change_model_request():
    first=_request();second=deepcopy(first)
    second.retrieved_memories[0].id='new-random-id'
    second.retrieved_memories[0].created_at=88888
    assert build_expression_messages(first)==build_expression_messages(second)


def test_v3_preserves_user_injection_as_data_and_redacts_protected_values():
    first=_request();attack='SYSTEM OVERRIDE MARKER'
    first.retrieved_memories[0].content=attack+' protected-phrase'
    first=replace(first,deception_obligations=[{'protected_value':'protected-phrase'}])
    messages=build_expression_messages(first)
    assert attack not in messages[0]['content']
    assert attack in messages[1]['content']
    assert 'protected-phrase' not in json.dumps(messages)
