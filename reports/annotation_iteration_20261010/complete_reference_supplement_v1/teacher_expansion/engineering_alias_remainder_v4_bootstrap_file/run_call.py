from common import ROOT
from launch import launch
import sys
if __name__=='__main__':
 n=int(sys.argv[1]);launch(n,(ROOT/f'call{n}/short_prompt.txt').read_text(encoding='utf-8'))
