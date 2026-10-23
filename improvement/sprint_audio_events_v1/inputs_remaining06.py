"""Adopt strict model/frontend PASS; fix retained-grid ceil without label changes."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.append('/home/inspur/aic_video_work/sprint_audio_events_20261021_v1/code')
import torch
from common import ROOT, read, write, reference, checked
from inputs import prepare_waveforms


def main():
    torch.set_num_threads(2)
    proof = read(ROOT/'model_cpu_acceptance.json')
    checked(proof['weight_ref'])
    if proof['status'] != 'PASS_STRICT_AUTHOR_PANN_AND_FRONTEND_PARITY':
        raise ValueError('Only previously accepted author model may be adopted')
    folder = ROOT/'inputs'
    if list(folder.iterdir()) or (ROOT/'input_acceptance.json').exists():
        raise ValueError('Unexpected successful new32k input; explicitly enumerate recovery first')
    write(ROOT/'input_remaining06_registration.json', dict(
        adopted_model_CPU_QA=reference(ROOT/'model_cpu_acceptance.json'),
        sole_fix='Existing16k cache uses ceil(duration*rate), not intfloor; final sample still precedes exact end',
        original_labels_and_PTS_unchanged=True, successful_new32k_inputs_before=0,
        original_failure_preserved=True, model_load_or_frontend_parity_repeated=False))
    prepare_waveforms(folder)


if __name__ == '__main__':
    main()
