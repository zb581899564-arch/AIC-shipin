"""Explicit two-policy production paths; only accepted native inputs and frozen models."""
from pathlib import Path
import sys
from common import ROOT as ADMISSION,WORK,read,ref,save
from time_control50_common import RUN,PY,WRAPPER,checked

ROOT=ADMISSION/'routing_production60'
ENGINEERING=WORK/'i3d_umt_cross_domain_20261021_v1'
SPORT=WORK/'highlight_source_admission_20261021_v1/matched_hl_pilot16'
FAMILY=WORK/'twenty_hour_five_20261014_v1/temporal_family_native_package_v3'
JOB='semantic_sport_expert_route426_20261022_v60'
FULL_PARAMETERS=8816809946
CLASSES=['long jump','pole vault','gymnastics tumbling','springboard diving']


def activate_i3d():
    sys.path.insert(0,str(ENGINEERING))
    sys.path.insert(0,str(ENGINEERING/'crossdata12/code'))
    sys.path.insert(0,str(SPORT/'code'))
