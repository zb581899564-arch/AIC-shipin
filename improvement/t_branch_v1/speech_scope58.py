"""Paths and original helper bindings for the CPU-only information study."""
from pathlib import Path
import sys

from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'speech_information58'
WAVE = Path('/dev/shm/aic_T_speech_information58')
GENERAL = WORK / 'general_highlight_supervision_20261021_v1'
NEW = ('L7ddd6bf6c93a', 'Lf27fb5bf66ad')
ADOPT = ('N865eb00aa784', 'N68272a683236')


def original_helpers():
    sys.path.insert(0, str(GENERAL / 'code'))
    import source_audio36
    helper, ref = source_audio36.old_helpers()
    return source_audio36, helper, ref


def selected_sources():
    protocol = read(ROOT / 'code/joint_policy_protocol44.json')
    wanted = set(protocol['training_sources'] + protocol['development_sources'])
    sources = {row['sid']: row for row in read(ROOT / 'source_registry09/registration.json')['sources']
               if row['sid'] in wanted}
    if set(sources) != set(NEW + ADOPT) or any(row['role'] == 'confirmation' for row in sources.values()):
        raise ValueError('Exact old fit/dev cohort differs; never inspect fresh confirmation')
    return sources
