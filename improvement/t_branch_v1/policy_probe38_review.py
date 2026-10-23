"""First independent scalar replay in explicit remaining probe root38."""
from t_io import ROOT
import policy_replay36 as original

if __name__ == '__main__':
    original.OUT = ROOT / 'policy_probe38'
    original.main()
