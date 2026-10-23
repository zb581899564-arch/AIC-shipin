"""Diagnostic only: group-constrained human F1 ceiling, never predictions or quality."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
from pathlib import Path
import sys
import numpy as np
from common import ROOT as ADMISSION,WORK,read,ref,save

ROOT=ADMISSION/'resolution_oracle56'
SPORT=WORK/'highlight_source_admission_20261021_v1/matched_hl_pilot16'


def ceiling(labels,size):
    groups=np.arange(len(labels))//size
    known=np.bincount(groups,weights=(labels>=0))
    positive=np.bincount(groups,weights=(labels==1))
    ratios=np.divide(positive,known,out=np.zeros_like(positive),where=known>0)
    order=np.argsort(-ratios,kind='stable');tp=np.cumsum(positive[order]);selected=np.cumsum(known[order])
    denominator=selected+positive.sum()
    f1=np.divide(2*tp,denominator,out=np.zeros_like(tp),where=denominator>0)
    index=int(np.argmax(f1));return dict(maximum_known_frame_F1=float(f1[index]),
        selected_known_frames=int(selected[index]),groups=len(known),oracle_only=True,
        UNKNOWN_excluded_from_metric_not_replaced_by_background=True)


def main():
    ROOT.mkdir()
    save(ROOT/'protocol.json',dict(purpose='Decide if native64 constant decisions impose a meaningful precision ceiling before any shorter-profile work',
        fixed_sizes=[64,16],oracle_labels_only=True,no_model_quality_claim=True,no_train_decode_or_GPU=True,
        not_a_deployment_selector=True,all_test_data_access=False))
    sys.path.insert(0,str(SPORT/'code'));from pilot15_common import original_targets
    rows=[]
    for source in read(SPORT/'registration.json')['sources']:
        labels=original_targets(source);values={str(size):ceiling(labels,size) for size in [64,16]}
        rows.append(dict(source=source['source'],role=source['role'],values=values,
            oracle_F1_resolution_gain=values['16']['maximum_known_frame_F1']-values['64']['maximum_known_frame_F1']))
    save(ROOT/'completion.json',dict(state='DIAGNOSTIC_RESOLUTION_CEILING_ONLY',sources=rows,
        no_model_forward=True,no_input_admission_or_production_permission=True,
        baseline_unchanged=True,new_ZIP=0))


if __name__=='__main__':main()
