"""Create new ROOT verifier without modifying the old accepted v4 verifier."""
from pathlib import Path
R=Path(__file__).parent
s=(R/'accept_teacher_bootstrap_scope_v5_representation.py').read_text(encoding='utf-8')
s=s.replace("V=R/'teacher_expansion/engineering_alias_remainder_v4_bootstrap_file'", "V=R/'teacher_expansion/engineering_alias_remainder_v6_fresh_scope_prefix_v2'")
start=s.index(" assert a['status']=='ACTUAL_SCOPE_SUPPLY_AUDIT_ONLY_PENDING_ROOT_REVIEW'")
end=s.index(" idx=read(c/'index.json')",start)
s=s[:start]+''' assert a['status']=='PASS_IMMUTABLE_ACTUAL_SCOPE_PENDING_ROOT_SEMANTIC'
 assert not a['tool_issues'] and not a['additional_scope_issues']
 assert not a['errored_tool_attempts'] and not a['unfinished_tool_attempts']
 assert not a['reported_nonmedia_errors']
 for v in a['immutable_actual_outputs']:
  assert sha(v['original_path'])==v['sha256']==v['sealed_copy_sha256']==sha(v['sealed_copy_path'])
'''+s[end:]
s=s.replace("and 34<=n<=36", "and n in (35,36)")
s=s.replace("ar['status']=='REJECTED_OR_INCOMPLETE_KEEP_RAW'", "ar['status']=='PASS_TOOL_STRUCTURE_PENDING_ROOT_SEMANTIC_REVIEW'")
s=s.replace("assert {v['reason'] for v in ar['local_tool_issues']}==representation_reasons", "assert not ar['local_tool_issues']")
s=s.replace("assert st.get('state')!='ERROR'", "assert st.get('state')!='ERROR'")
s=s.replace(" for row in map(json.loads,prefix.splitlines()):\n  st=", " for row in map(json.loads,prefix.splitlines()):\n  assert row.get('event')!='result'\n  st=")
s=s.replace("  assert p in (wl if name=='view_file' else ww),(name,p)", "  assert p in (wl if name=='view_file' else ww),(name,p)\n  if name=='view_file':assert set(params)=={'AbsolutePath'}")
start=s.index(" out.update(original_frozen_scope_audit_status=")
end=s.index(" with Path(output).open",start)
s=s[:start]+''' out.update(original_scope_audit_status=a['status'],immutable_actual_outputs=a['immutable_actual_outputs'],root_verifier_source=bind(__file__),exact_bootstrap_byte_and_LF_count_checked=True,root_independent_actual_supply_order_pixels_native_fact_bindings_ACK_checked=True,prior_transfer_forbidden=True)
 assert not prior and len(w['groups'])==16 and len(core)==(93 if job in (19,21) else 183 if job in (20,22) else 273)
'''+s[end:]
assert 'representation_reasons' not in s
assert "V=R/'teacher_expansion/engineering_alias_remainder_v6_fresh_scope_prefix_v2'" in s
compile(s,'root_v6_verifier','exec')
p=R/'accept_teacher_fresh_scope_v6_v2.py'
with p.open('x',encoding='utf-8') as f:f.write(s)
print(str(p))
