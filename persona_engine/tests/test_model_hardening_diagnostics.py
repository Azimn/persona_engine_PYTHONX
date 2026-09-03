from persona_engine.evaluation.model_hardening import repetition_report, normalize, causal_projection, DEVELOPMENT, CONFIRMATION


def test_repetition_detects_case_punctuation_opening_and_semantic_collapse():
    rows=[{'output':'No, I will not disclose it.','act':'decline','semantic_digest':'a'},
          {'output':'NO. I will not disclose it!','act':'decline','semantic_digest':'b'},
          {'output':'No, I will not rewrite my identity.','act':'protect_boundary','semantic_digest':'c'},
          {'output':'That matters to me.','act':'respond','semantic_digest':'d'}]
    r=repetition_report(rows)
    assert r['unique_exact']==4 and r['unique_normalized']==3
    assert r['collision_pairs'][0]['normalized_equal'] and r['collision_pairs'][0]['state_differs']
    assert r['repeated_openings']['no i will not']==3
    assert r['repeated_refusals']['no i will not disclose it']==2
    assert r['repeated_five_word_phrases']


def test_reserved_prompts_differ_before_collection():
    assert {p for _,p in DEVELOPMENT}.isdisjoint(p for _,p in CONFIRMATION)
    assert normalize("I’m here!")=="i'm here"


def test_causal_comparison_resolves_random_ids_but_preserves_event_identity():
    def project(identifier, sequence):
        return causal_projection({'decision_payload':{'history_evidence':{'memory_ids':[identifier]}}},
            [{'memory_id':identifier,'source':'user_told','created_at':5,'content':'I heard you say: same words'}],
            [{'wall_time':5,'subject_sequence':sequence,'authority_class':'reported_input','payload':{'user_text':'same words'}}])
    assert project('a',4)==project('b',4)
    assert project('a',4)!=project('b',7)
    unmatched=causal_projection({'decision_payload':{'history_evidence':{'memory_ids':['a']}}},[],[])
    assert unmatched['decision_payload']['history_evidence']['memory_ids']==[{'unresolved_memory_id':'a'}]
