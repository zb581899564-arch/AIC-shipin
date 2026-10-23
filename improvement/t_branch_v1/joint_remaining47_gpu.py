"""Use original locked training implementation with only proven hook recovery."""
from joint_rollout47 import rollout
from t_io import ROOT
import joint_train44 as original

original.OUT = ROOT / 'joint_remaining47'
original.rollout = rollout

if __name__ == '__main__':
    original.main()
