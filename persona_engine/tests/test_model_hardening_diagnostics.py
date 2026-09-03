from persona_engine.evaluation.model_hardening import repetition_report, normalize, DEVELOPMENT, CONFIRMATION


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
