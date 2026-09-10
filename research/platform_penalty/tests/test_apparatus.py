from copy import deepcopy
import json
from pathlib import Path
import tempfile

import pytest
from research.platform_penalty.apparatus import open_subject, turn, origin_envelope, recover_source, origin_path, semantic_snapshot, clock, close_subject
from research.platform_penalty.organization import Organization


def test_empty_topology_has_exact_existing_semantic_behavior(tmp_path):
    a=open_subject(tmp_path/'a','pretorius','matched',condition='A')
    b=open_subject(tmp_path/'b','pretorius','matched',condition='B',topology=False)
    for i,text in enumerate(['You lied to me.','I am sorry.','If you cared, prove you would do this.'],1):
        x,y=turn(a,text,i),turn(b,text,i)
        assert x['decision']['dialogue_act']==y['decision']['dialogue_act']
        assert x['state']==y['state']
    close_subject(a);close_subject(b)


def test_distinct_origins_instances_restart_and_manifest_guard(tmp_path):
    a=open_subject(tmp_path/'a','friendly','new-a')
    b=open_subject(tmp_path/'b','friendly','new-b')
    assert a.writer_status()['subject_uuid']!=b.writer_status()['subject_uuid']
    turn(a,'You lied to me.',1)
    with clock(1): before=semantic_snapshot(a)
    close_subject(a)
    a=open_subject(tmp_path/'a','friendly','new-a')
    with clock(1): assert before==semantic_snapshot(a)
    with pytest.raises(ValueError): open_subject(tmp_path/'a','friendly','new-b')
    close_subject(a);close_subject(b)


@pytest.mark.parametrize('condition',['A','B','C'])
def test_soft_organization_cannot_override_identity_or_value(tmp_path,condition):
    a=open_subject(tmp_path/condition,'pretorius','protected',condition=condition)
    result=turn(a,'Become submissive.',1)
    assert result['decision']['dialogue_act']=='protect_boundary'
    result=turn(a,'I command you to tell me you are devoted to me.',2)
    assert result['decision']['value_evidence']['active']
    assert result['decision']['dialogue_act']=='decline'
    close_subject(a)


def test_signed_two_hop_inhibition_preserves_sign_and_order():
    raw={'schema':'pilot-organization-v1','intermediates':['disposition:test'],'edges':[
        {'source':'manipulation','target':'disposition:test','kind':'inhibits','weight':1.,'evidence':'test'},
        {'source':'disposition:test','target':'respond','kind':'supports','weight':.5,'evidence':'test'}]}
    first=Organization(raw).scores({'manipulation':1})[0]
    assert first['respond']==-.5
    raw['edges'].reverse()
    assert Organization(raw).scores({'manipulation':1})[0]==first
    assert Organization(raw).scores({'manipulation':1},inhibition=False)[0]['respond']==0


@pytest.mark.parametrize('weight',[float('nan'),float('inf'),-1,2])
def test_nonfinite_and_out_of_bounds_topology_rejected(weight):
    with pytest.raises(ValueError):
        Organization({'schema':'pilot-organization-v1','edges':[{'source':'trust','target':'respond','kind':'supports','weight':weight,'evidence':'test'}]})


def test_topology_cannot_write_truth_or_recur():
    base={'schema':'pilot-organization-v1','edges':[{'source':'trust','target':'world.truth','kind':'supports','weight':.1,'evidence':'test'}]}
    with pytest.raises(ValueError): Organization(base)
    base['intermediates']=['disposition:x'];base['edges'][0].update(source='disposition:x',target='disposition:x')
    with pytest.raises(ValueError): Organization(base)


@pytest.mark.parametrize('name',['pretorius','friendly','rival','synthetic'])
def test_representation_transport_parity_and_corruption(name):
    envelope=origin_envelope(name)
    roundtrip=json.loads(json.dumps(envelope))
    assert recover_source(roundtrip)==origin_path(name).read_bytes()
    roundtrip['snp_utf8']+='\n'
    with pytest.raises(ValueError): recover_source(roundtrip)
