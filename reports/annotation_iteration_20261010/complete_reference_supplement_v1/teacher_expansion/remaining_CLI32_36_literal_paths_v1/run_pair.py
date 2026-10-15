from launch import ROOT,read,launch
from prompt import build_prompt
import sys
n=int(sys.argv[1]);assert n in range(6,11)
a=ROOT/f'call{n:02d}';prompt,paths=build_prompt(a)
assert prompt==(a/'frozen_prompt.txt').read_text(encoding='utf-8')
launch(a,prompt)
