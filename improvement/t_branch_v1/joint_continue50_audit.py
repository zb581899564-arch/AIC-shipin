"""First complete independent audit; old timed-out47 never completed this audit."""
from t_io import ROOT
import joint_audit45 as original

original.OUT = ROOT / 'joint_continue50'

if __name__ == '__main__':
    original.main()
