"""One frozen video/text contrast, using accepted external inputs only."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent
PREVIOUS = WORK / 'independent_text_grounding_20261021_v1'
BASE_PARAMETERS = 8782557449
COMMIT = '1744b2159c3d11694f94dab4fcde8660c685e79a'
WEIGHT_BYTES = 786503179
WEIGHT_URL = 'https://github.com/nbl97/X-CLIP_Model_Zoo/releases/download/v1.0/k400_32_8.pth'


def adopted_module(name):
    spec = importlib.util.spec_from_file_location('adopted_' + name, PREVIOUS / 'code' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Reuse the existing small, reviewed file and AP utilities without running a stage.
utilities = adopted_module('common')
read, ref, checked, write, digest, grouped_ap = (
    utilities.read, utilities.ref, utilities.checked, utilities.write,
    utilities.digest, utilities.grouped_ap,
)
