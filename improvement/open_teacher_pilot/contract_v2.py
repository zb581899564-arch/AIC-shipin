"""Prospective flat schema: generation and validation share one total span limit.

This repairs the v1 nested-schema gap. No v1 answer is converted or accepted here.
No model launcher is attached to this prepared contract.
"""
import json

STATES=('KEEP','ORDINARY','UNCERTAIN')
SCHEMA={
    'type':'object','additionalProperties':False,'required':['spans'],
    'properties':{'spans':{'type':'array','minItems':1,'maxItems':3,
        'items':{'type':'object','additionalProperties':False,
                 'required':['state','start','end','evidence','fact'],
                 'properties':{
                     'state':{'type':'string','enum':list(STATES)},
                     'start':{'type':'integer','minimum':0,'maximum':63},
                     'end':{'type':'integer','minimum':0,'maximum':63},
                     'evidence':{'type':'array','minItems':1,'maxItems':3,
                                 'items':{'type':'integer','minimum':0,'maximum':63}},
                     'fact':{'type':'string','minLength':1,'maxLength':96}}}}}}


def validate(value):
    if type(value)!=dict or set(value)!={'spans'} or type(value['spans'])!=list:
        raise ValueError('exact flat spans object required')
    spans=value['spans']
    if not 1<=len(spans)<=3:raise ValueError('one shared total span limit')
    previous=-1
    for span in spans:
        if type(span)!=dict or set(span)!={'state','start','end','evidence','fact'}:
            raise ValueError('exact span fields required')
        a,b=span['start'],span['end']
        if span['state'] not in STATES or type(a)!=int or type(b)!=int or not 0<=a<=b<64:
            raise ValueError('state or observation ID invalid')
        if a<=previous:raise ValueError('spans must be sorted and strictly non-overlapping')
        previous=b
        e=span['evidence']
        if type(e)!=list or not 1<=len(e)<=3 or any(type(v)!=int or not a<=v<=b for v in e) or len(set(e))!=len(e):
            raise ValueError('distinct evidence must be inside span')
        if type(span['fact'])!=str or not 1<=len(span['fact'])<=96:raise ValueError('fact length')
    return value


def parse(raw):
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result:raise ValueError('duplicate JSON key')
            result[key]=value
        return result
    return validate(json.loads(raw,object_pairs_hook=unique))
