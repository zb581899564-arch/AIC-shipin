"""Uniform nested crop risk arms. No model calls, frame selection or GT access."""
import argparse
import json
from fractions import Fraction
from pathlib import Path

ARMS={'R16_099':({(16,9)},99,100),'R9_099':({(9,16)},99,100),
      'RBOTH_098':({(16,9),(9,16)},98,100)}

def crop(box,ratio,arm):
    allowed,n,d=ARMS[arm]
    if tuple(ratio) not in allowed:return list(box)
    x,y,w=box;tw,th=ratio;neww=(w*n+d-1)//d;delta=w-neww
    return [x+delta//2,y+(delta*th)//(2*tw),neww]

def transform(rows,arm):
    return [{**row,'predictions':[{'frame':p['frame'],'bboxes':crop(p['bboxes'],row['targetRatioWH'],arm)}
                                  for p in row['predictions']]} for row in rows]

def write(path,rows):
    with Path(path).open('x',encoding='utf-8') as f:
        for row in rows:f.write(json.dumps(row,ensure_ascii=False,sort_keys=True,allow_nan=False)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--arm',choices=ARMS,required=True);p.add_argument('--output',required=True);args=p.parse_args()
    values=[json.loads(x) for x in Path(args.input).read_text().splitlines() if x.strip()]
    write(args.output,transform(values,args.arm))
