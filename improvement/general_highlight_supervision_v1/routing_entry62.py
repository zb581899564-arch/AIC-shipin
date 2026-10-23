"""Explicit remaining root adapter; original scientific model/selection code unchanged."""
from pathlib import Path
import runpy
import sys
import routing_production60_common as context


def main():
    if len(sys.argv)!=2 or sys.argv[1] not in ['gpu','review']:raise ValueError('Explicit GPU or first CPU replay only')
    context.ROOT=context.ADMISSION/'routing_production62'
    runpy.run_path(str(Path(__file__).parent/('routing_production60_'+sys.argv[1]+'.py')),run_name='__main__')


if __name__=='__main__':main()
