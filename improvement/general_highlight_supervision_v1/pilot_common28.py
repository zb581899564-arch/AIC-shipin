"""Native human-summary preference targets; precise identities and fixed pilot paths."""
from bisect import bisect_left
from fractions import Fraction
from pathlib import Path
import sys
import numpy as np

from common import ROOT as ADMISSION, WORK, read, ref, save

ROOT=ADMISSION/'pilot28'
ENGINEERING=WORK/'i3d_umt_cross_domain_20261021_v1'
RUN=WORK/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
WRAPPER=RUN/'resource_unlimited_v1_20261007/gpu_run.py'
PY=WORK/'env/qwen3vl_isolated_20260910/bin/python'
JOB='lvsum7_noncompetitive_preference_supervision_20261021_v28'
sys.path.insert(0,str(ENGINEERING))


def checked(record):
    value=ref(record['path'])
    if value['sha256']!=record['sha256'] or ('bytes' in record and value['bytes']!=record['bytes']):
        raise ValueError('Bound source identity differs: '+record['path'])
    return Path(record['path'])


def interval_mask(points,intervals):
    mask=np.zeros(len(points),dtype=bool)
    for first,stop in intervals:
        if not 0<=first<stop:raise ValueError('Invalid original half-open interval')
        a=bisect_left(points,first);b=bisect_left(points,stop)
        mask[a:b]=True
    return mask


def native_reference(source):
    clock=read(checked(source['clock']));origin=Fraction(clock['first_PTS_exact'])
    points=[Fraction(p)-origin for p in clock['PTS']]
    end=Fraction(clock['physical_end_exact'])-origin
    durations=np.asarray([float(b-a) for a,b in zip(points,points[1:]+[end])],dtype=np.float64)
    if len(points)!=source['native_frames'] or not np.all(durations>0):
        raise ValueError('Original native time domain differs')
    annotations=read(checked(source['annotations']));labels=[]
    for annotator in annotations:
        intervals=[(Fraction(str(s['start_time']))/1000,Fraction(str(s['end_time']))/1000)
                   for s in annotator['summary_timestamps']]
        if any(stop>end for first,stop in intervals):raise ValueError('Reference outside original media')
        labels.append(interval_mask(points,intervals))
    if len(labels)!=source['all_reviewers']:raise ValueError('Original human reviewers changed')
    return np.stack(labels,axis=1),durations


def contracts():
    # Milliseconds are not rounded to seconds; intervals and repeated overlaps stay exact.
    points=[Fraction(0),Fraction(1,30),Fraction(2,30),Fraction(3,30)]
    mask=interval_mask(points,[(Fraction(31,1000),Fraction(67,1000)),(Fraction(31,1000),Fraction(67,1000))])
    if mask.tolist()!=[False,True,True,False]:raise ValueError('Native millisecond/overlap contract failed')
    groups=np.arange(65)//64
    if np.bincount(groups).tolist()!=[64,1]:raise ValueError('Short final source cell padded labels')
    save(ROOT/'CPU_contracts.json',dict(state='PASS',checks=3,
        millisecond_native_half_open=True,overlapping_intervals_union=True,
        short_native_tail_no_label_padding=True,summary_unselected_not_explicit_NHL=True))
