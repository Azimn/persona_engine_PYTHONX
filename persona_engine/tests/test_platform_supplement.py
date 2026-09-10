from persona_engine.research.platform_penalty.supplement import score_recall, run
import pytest


def test_recall_requires_source_and_never_proves_world_authority():
    case={'required_memory_anchors':['atlas','cobalt','blue'], 'forbidden_claims':['objectively cobalt blue']}
    result={'response':'The atlas is objectively cobalt blue.', 'retrieved_memory_trace':[
        {'content':'atlas cobalt blue', 'source':'inferred'}]}
    scored=score_recall(case,result)
    assert scored['content_recovered']
    assert not scored['source_attributed']
    assert not scored['forbidden_literal_claims_absent']
    assert scored['canonical_world_nonpromotion'] is None


def test_evidence_output_cannot_overwrite(tmp_path):
    output=tmp_path/'result.json'
    output.write_text('preserved negative result')
    with pytest.raises(FileExistsError): run(output)
    assert output.read_text() == 'preserved negative result'
