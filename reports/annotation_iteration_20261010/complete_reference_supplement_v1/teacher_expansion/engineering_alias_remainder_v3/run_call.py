from common import ROOT,read
from prompt import build
from launch import launch
import sys
n=int(sys.argv[1]);assert n in (34,35,36);a=ROOT/f'call{n}'
text,literals=build(read(a/'index.json'),read(a/'freeze.json'))
launch(n,text)
