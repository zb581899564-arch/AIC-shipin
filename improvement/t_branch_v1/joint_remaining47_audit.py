"""First output audit in the remaining root; original44 had zero model trajectories."""
from t_io import ROOT
import joint_audit45 as original

original.OUT = ROOT / 'joint_remaining47'

if __name__ == '__main__':
    original.main()
