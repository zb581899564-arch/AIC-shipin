from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil
H=Path(__file__).resolve().parent
E=H.parents[1]/'rematch_execution/rematch_exec_20261005T1215Z/post_sg8_reference_g0_slot5_v1'
def bind(p):return dict(file=p.name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
ledger=json.loads((H/'ledger.json').read_bytes())
acks=[]
for seat in ['sol','tibo','grok','gemini']:
    p=H/(seat+'-final-ack.md');s=p.read_text(encoding='utf-8')
    assert 'NO_426' in s or 'NO426' in s
    assert 'END_REPLAN_FINAL' in s or seat=='gemini'
    acks.append(dict(seat=seat,**bind(p),complete_final_response=True,packet_text_read='SELF_REPORTED_COMPLETE',raw_packet_byte_hash_verification=('EXPLICIT_NOT_INDEPENDENTLY_VERIFIED_TEXT_EXTRACTION_SIZE_DIFFERS' if seat=='tibo' else 'SELF_REPORTED_NOT_HOST_REEXECUTION')))
parts=[H/('context-final-part0'+str(i)+'.md') for i in range(1,7)]
assert b''.join(p.read_bytes() for p in parts)==(H/'context-final.md').read_bytes()
receipt=dict(status='COMPLETE_TWO_ORDINARY_ROUNDS_PRO_SLOT5_AND_FINAL_RELAY_WITH_ACTUAL_G0_NO_426',utc=datetime.now(timezone.utc).isoformat(),packet=bind(H/'context-final.md'),previous_packet_exact_prefix=(H/'context-final.md').read_bytes().startswith((H/'context-p01.md').read_bytes()),pro=bind(H/'pro-p01.md'),pro_slot=5,pro_remaining=3,final_receipts=acks,work_completion=bind(E/'closure.json'),runtime=bind(H/'final-runtime-readonly.json'),scientific_quality='UNKNOWN',new_426_ZIP=False,new_model_calls=0,new_optimizer_updates=0,publication='PRIVATE_NO_NEW_GITHUB_PUBLICATION_THIS_TURN',no_automation_recreated=True)
with (H/'final-delivery-receipt.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
ledger['final_delivery']=receipt
ledger['status']='COMPLETE_DISCUSSION_AND_BOUNDED_WORK_NO_426'
(H/'ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
shutil.copyfile(H/'final-runtime-readonly.json',E/'final-runtime-readonly.json')
shutil.copyfile(H/'final-delivery-receipt.json',E/'discussion-delivery-receipt.json')
print(json.dumps(dict(status=receipt['status'],final_receipts=len(acks),pro_remaining=3,new_model_calls=0,new_426_ZIP=False),ensure_ascii=False))
