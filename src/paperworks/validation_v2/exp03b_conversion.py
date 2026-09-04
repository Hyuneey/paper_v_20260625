"""Actual Formal V4 descriptor/numeric validation, not deployment authorization."""
from pathlib import Path
from .exp03b_contract_v1 import digest,require
from .exp03b_custody_v1 import publish,seal
from .formal_v4_authority_v1 import (FormalV4RuleDescriptorV1,NumericReferenceBindingV1,FormalV4ArtifactBindingV1,V4_NUMERIC_ROLES,canonical_document_hash_v1,_validate_descriptor_materialization_v1,load_formal_v4_numeric_values_v1)

def convert(root:Path,directory:Path,rules:tuple):
    require(directory.is_relative_to(root),'CONVERSION_PRIVATE_ROOT')
    if not rules:return ()
    relation_rows=[];numeric_rows=[];references=[]
    for rule in rules:
        identity={'candidate_id':rule.candidate_id,'source':rule.source,'target':rule.target,'tuple':rule.semantic.__dict__,'alias':rule.alias,'admission_hash':rule.train2_acceptance_hash,'reference_hash':rule.train3_reference_hash}
        rid='EXP03B-REL-'+digest(identity)[:24];roles=dict(rule.candidate_roles)
        require(set(roles)==set(V4_NUMERIC_ROLES),'CONVERSION_ROLE_CLOSURE')
        relation={'relation_id':rid,'relation_binding_hash':digest(identity),'semantic_execution_hash':digest({'identity':identity,'roles':roles}),'source':rule.source,'target':rule.target,'source_direction':rule.semantic.source_direction,'target_direction':rule.semantic.target_direction,'selected_horizon_seconds':rule.semantic.horizon_seconds}
        refs=[]
        for role in V4_NUMERIC_ROLES:
            body={'relation_id':rid,'numeric_role':role,'reference_id':rid+'-'+role,'value':float(roles[role])}
            h=canonical_document_hash_v1(body);refs.append(NumericReferenceBindingV1(role,body['reference_id'],h));numeric_rows.append({**body,'reference_hash':h})
        relation_rows.append(relation);references.append(tuple(refs))
    rp=directory/'relations.json';np=directory/'numeric.json'
    rh=publish(rp,{'artifact_type':'validation_v2_formal_v4_relation_authority_v1','relations':relation_rows,'schema_version':'1.0.0'})
    nh=publish(np,{'artifact_type':'validation_v2_formal_v4_numeric_authority_v1','bindings':numeric_rows,'schema_version':'1.0.0'})
    rb=FormalV4ArtifactBindingV1('EXP03B-RELATION',rp.relative_to(root).as_posix(),rh);nb=FormalV4ArtifactBindingV1('EXP03B-NUMERIC',np.relative_to(root).as_posix(),nh)
    descriptors=tuple(FormalV4RuleDescriptorV1(**r,numeric_reference_bindings=refs,numeric_authority_hash=nh) for r,refs in zip(relation_rows,references))
    _validate_descriptor_materialization_v1(descriptors,relation_authority_binding=rb,numeric_authority_binding=nb,repository_root=root)
    for descriptor in descriptors:load_formal_v4_numeric_values_v1(descriptor=descriptor,numeric_authority_binding=nb,repository_root=root)
    publish(directory/'CONVERSION_RECEIPT.json',seal({'status':'FORMAL_V4_DESCRIPTOR_NUMERIC_VALIDITY_PASS','descriptor_hashes':[d.descriptor_hash for d in descriptors],'numeric_authority_hash':nh,'relation_authority_hash':rh,'deployment_authorized':False,'attack_access_authorized':False}))
    return descriptors
