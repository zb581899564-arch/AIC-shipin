"""Adopt the accepted wheel and extract its actual license, then first weight GET."""
import zipfile
from common import ROOT, read, write, reference
from acquire04 import receive


def main():
    write(ROOT/'acquisition_failure04.json', dict(stage='WHEEL_LICENSE_MEMBER_LOOKUP',
        error='Expected LICENSE, wheel actually contains LICENSE.md',
        wheel_already_accepted=True, stft_and_augmentation_already_extracted=True,
        weight_requests=0))
    acceptance = read(ROOT/'author/torchlibrosa-0.1.0-py3-none-any.whl.acceptance.json')
    wheel = ROOT/'author/torchlibrosa-0.1.0-py3-none-any.whl'
    if acceptance['file'] != reference(wheel):
        raise ValueError('Accepted frontend archive changed')
    with zipfile.ZipFile(wheel) as archive:
        raw = archive.read('torchlibrosa-0.1.0.dist-info/LICENSE.md')
    with (ROOT/'author/torchlibrosa_LICENSE.md').open('xb') as stream:
        stream.write(raw)
    weight = next(x for x in read(ROOT/'author/zenodo_record04.json')['files']
        if x['key']=='Cnn14_DecisionLevelAtt_mAP=0.425.pth')
    write(ROOT/'acquisition_remaining05_registration.json', dict(
        adopted_wheel=acceptance['file'], license=reference(ROOT/'author/torchlibrosa_LICENSE.md'),
        actual_weight_first_GET=True, no_prior_weight_request=True, expected=weight))
    receive(weight['links']['self'], ROOT/'PANN_Cnn14_DecisionLevelAtt.pth',
        weight['size'], weight['checksum'].split(':')[1], 'md5', 900)
    write(ROOT/'acquisition05_completion.json', dict(status='PASS_ONE_DIRECT_PANN_AND_FRONTEND_SOURCE',
        weight=reference(ROOT/'PANN_Cnn14_DecisionLevelAtt.pth'), no_global_install=True))


if __name__ == '__main__':
    main()
