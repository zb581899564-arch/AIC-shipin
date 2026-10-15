"""Catalogue scene coverage selection; contains no reference labels or predictions."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/reliable_reference_20261012_v1'
selection=json.loads((OUT/'supplement_catalog_selection.json').read_text())
notes={
 'S01':'Air travel, queues and speech; audio/context dependent',
 'S02':'Conversation by motorcycle; no clearly independent result in catalogue',
 'S03':'Bottle/drink and bag handling, possible bounded demonstration',
 'S04':'Speech at podium, audio dependent', 'S05':'Car speech, audio dependent',
 'S06':'Mirror speech, audio dependent', 'S07':'Parked motorcycle views, useful repetitive demonstration control',
 'S08':'Cat and petting interaction, inspect whether meaningful event or ordinary',
 'S09':'Hair product demonstration, inspect action and result',
 'S10':'Finished food presentation and pointing, inspect meaningful static result',
 'S11':'Split-screen conversation, audio dependent', 'S12':'Couple speaking, audio dependent',
 'S13':'Restaurant ingredient counter, possible waiting/control evidence',
 'S14':'Cafe conversation, audio dependent', 'S15':'Toothbrush preparation and child interaction, inspect action evidence',
 'S16':'Two people physical hand interaction, inspect bounded action and result',
 'S17':'Festival landscape and spectators, performance audio dependent',
 'S18':'Street selfie speech, audio dependent', 'S19':'Speech, audio dependent',
 'S20':'Cello performance, musical saliency needs audio', 'S21':'Speech, audio dependent',
 'S22':'Tourism pans and architecture, possible transition controls', 'S23':'Two people speaking, audio dependent',
 'S24':'Repetitive footwear display and pans, possible controls', 'S25':'Outdoor music performance, audio dependent',
 'S26':'Talking and map, audio dependent', 'S27':'Night driving, no bounded unusual event in catalogue',
 'S28':'Beach pan and speech, subjective/audio dependent',
 'S29':'Makeup process, inspect state transition evidence',
 'S30':'Table tennis rallies and resets, inspect start/result and ordinary waits',
 'S31':'Car speech, audio dependent', 'S32':'Ingredients enter pan and cooking, inspect state transitions',
 'S33':'Food tasting and reactions, inspect visible evidence without guessing speech',
 'S34':'Food table conversation, audio dependent', 'S35':'News speech and text, audio/context dependent',
 'S36':'Gym leg movement, inspect repetition and outcome',
 'S37':'Parent/child toy demonstration, inspect bounded action or ordinary',
 'S38':'Packing clothes, inspect demonstration result or repetitive ordinary',
 'S39':'Balcony view and greeting, subjective scenic value',
 'S40':'Continuous motorcycle riding, possible repetitive control', 'S41':'Selfie speech, audio dependent',
 'S42':'News emotional context, no independent highlight judgement from catalogue',
 'S43':'News speech/graphic, semantic context required',
 'S44':'Blindfold removal and embrace, inspect bounded interaction',
 'S45':'Watercraft preparations and movement, inspect bounded event and clipping',
}
chosen={'S03','S07','S08','S09','S10','S13','S15','S16','S22','S24','S29','S30','S32','S33','S36','S37','S38','S40','S44','S45'}
rows=[]
for r in selection['rows']:
 if r['case_id'] in chosen:
  rows.append(dict(r,role='screen' if len(rows)<12 else 'confirm'))
result=dict(status='SCENE_COVERAGE_SELECTION_NOT_REFERENCE_LABELS',rows=rows,sources=len(rows),catalog_pages_actually_viewed=48,
            source_notes=notes,prediction_blind=True,old_failed_reference_preserved=True,
            selection_bias='Purposive visible-process and control coverage, not representative random validation',new_model_calls=0)
assert len(rows)==20
with (OUT/'supplement_review_selection.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(sources=len(rows),screen=12,confirm=8)))
