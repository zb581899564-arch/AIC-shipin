import copy
import unittest
from phase_gate import validate_finished_phase
from sft_contract import BASE_PARAMS,LORA_PARAMS,TOTAL_PARAMS

class Gate(unittest.TestCase):
    def valid(self):
        freeze=dict(sha256='a'*64,parameters=BASE_PARAMS,method='all bytes')
        updates=[dict(optimizer_step=i,mean_loss=1.,gradient_norm=.2,changed_lora_tensors=144,
            lora_gradient_evidence={f:dict(tensors=144,connected=144,finite=144,nonzero=144)
                for f in ('lora_A','lora_B')}) for i in range(1,4)]
        return dict(status='PASS_MAC_8B_64_PROBE',base_frozen=True,vision_frozen=True,
            adapter_reload_succeeded=True,loss_finite=True,effective_batches=48,optimizer_steps=3,
            parameter_inventory=dict(base=BASE_PARAMS,lora=LORA_PARAMS,total=TOTAL_PARAMS),
            freeze_evidence={key:copy.deepcopy(freeze) for key in
                ('before_training','after_training','after_reload','adapter_off')},updates=updates,
            wall_seconds=600.,peak_memory_allocated_mib=20000.,mps_recommended_max_memory_bytes=55000000000)
    def test_complete_probe_accepts(self):self.assertIsNotNone(validate_finished_phase(self.valid(),'probe'))
    def test_incomplete_or_failed_probe_cannot_continue(self):
        for key,value in [('status','STOP_FULL_INTERVAL_SFT'),('effective_batches',47),('adapter_reload_succeeded',False)]:
            report=self.valid();report[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):validate_finished_phase(report,'probe')
    def test_frozen_bytes_and_gradients_are_required(self):
        for mutation in ('freeze','gradient','finite','capacity'):
            report=self.valid()
            if mutation=='freeze':report['freeze_evidence']['adapter_off']['sha256']='b'*64
            elif mutation=='gradient':report['updates'][-1]['lora_gradient_evidence']['lora_B']['connected']=143
            elif mutation=='finite':report['updates'][-1]['mean_loss']=float('nan')
            else:report['mps_recommended_max_memory_bytes']=1024
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):validate_finished_phase(report,'probe')

if __name__=='__main__':unittest.main(verbosity=2)
