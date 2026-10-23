"""Original fixed VERIFY/review functions on explicit remaining55 metadata root."""
import importlib
import sys

from t_io import ROOT


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ['verify', 'review']:
        raise ValueError('Only explicit remaining VERIFY or first full review')
    module = importlib.import_module('development_verify48' if sys.argv[1] == 'verify' else 'development_review48')
    module.OUT = ROOT / 'development_remaining55'
    module.main()
