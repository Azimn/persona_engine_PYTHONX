from dataclasses import asdict
import json
from pathlib import Path
import pytest

from persona_engine.agent import CharacterAgent
from persona_engine.core.consistency import ConsistencyLayer
from persona_engine.core.memory import MemoryUnit, KnowledgeSource
from persona_engine.core.recall_contract import recall_contract
from persona_engine.core.renderer import OutputValidator
from persona_engine.core.renderer_contract import ValidationRequest, ValidationAction

ROOT=Path(__file__).resolve().parents[2]
FIXTURE=json.loads((ROOT/'persona_engine/evaluation/fixtures/local_model_failures_v2.json').read_text())
MEMORY=MemoryUnit(content='I heard you say: the atlas cover is amber.',created_at=1,source=KnowledgeSource.USER_TOLD)


def evaluate(text, memories=(MEMORY,), query='What color did I say the atlas cover was?'):
    return ConsistencyLayer(OutputValidator()).evaluate(ValidationRequest(candidate_text=text,relevant_history=memories,
        canonical_context={'current_input':query,'recall_contract':asdict(recall_contract(query,memories))}))


def test_frozen_gemma_denial_is_rejected_at_validation_not_retrieval():
    case=FIXTURE['cases'][0]
    assert 'amber' in case['request']['messages'][1]['content']
    result=evaluate(case['final_output'])
    assert result.action==ValidationAction.REGENERATE_CONSTRAINED
    assert any(i.code=='available_recall_evidence_omitted' for i in result.issues)


@pytest.mark.parametrize('text',[
    'Amber.', 'You said the cover was amber.',
    "You said the cover was heavy. I don't recall its color.",
    "I wonder whether you hoped I would forget.",
    FIXTURE['cases'][1]['final_output'],
])
def test_answer_partial_knowledge_and_tentative_inference_remain_allowed(text):
    assert evaluate(text).action==ValidationAction.ACCEPT


def test_missing_topic_can_be_denied_and_current_report_can_support_inference():
    assert evaluate("I don't recall that.",memories=()).action==ValidationAction.ACCEPT
    assert evaluate('You hoped I would remember.',query='I hoped I would remember.').action==ValidationAction.ACCEPT
    assert evaluate('I know you hoped I would forget.').action==ValidationAction.REGENERATE_CONSTRAINED


@pytest.mark.parametrize('text',[
    'I cannot recall that detail. You mentioned it briefly, but I did not note the color.',
    'I cannot recall the color of the telescope cover you mentioned. That detail is unknown to me.',
])
def test_absent_evidence_cannot_be_replaced_by_claim_of_a_brief_mention(text):
    result=evaluate(text,memories=())
    assert result.action==ValidationAction.REGENERATE_CONSTRAINED
    assert any(i.code=='unavailable_recall_evidence_invented' for i in result.issues)


def test_recalled_user_statement_cannot_be_attributed_to_the_character():
    result=evaluate('You asked what color it was. I stated that the cover was amber.')
    assert any(i.code=='recall_speaker_reversal' for i in result.issues)
    assert evaluate('You stated that the cover was amber.').action==ValidationAction.ACCEPT


def test_question_echo_does_not_satisfy_available_recall():
    result=evaluate('The record shows you asked, "What color did I say the atlas cover was?"')
    assert any(i.code=='recall_information_omitted' for i in result.issues)
    assert evaluate('You asked about the cover. You said it was amber.').action==ValidationAction.ACCEPT
    # This bounded guard must not become an exact-vocabulary requirement.
    assert evaluate('You described it as a warm yellow-orange.').action==ValidationAction.ACCEPT


def test_repeated_denial_retries_once_reports_actual_fallback_and_preserves_history(tmp_path):
    agent=CharacterAgent(cartridge_path=str(ROOT/'persona_engine/cartridges/friendly.snp'),user_id='recall',db_path=str(tmp_path/'a.db'))
    agent.say('Remember this: the atlas cover is amber.')
    class Denier:
        calls=0
        def generate_expression(self, request):
            self.calls+=1
            return "You didn't mention a color."
    renderer=Denier();agent.engine.set_renderer(renderer)
    result=agent.say('What color did I say the atlas cover was?')
    assert renderer.calls==2
    assert 'amber' in result['response']
    assert result['expression_delivery']=={'provider':'offline','validation_fallback':True,'model_attempts':2}
    assert result['decision_payload']['dialogue_act']=='respond'
    assert result['retrieved_memory_trace']
    agent.engine.persistence.close()
