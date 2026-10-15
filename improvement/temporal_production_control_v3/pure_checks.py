"""This revision runs only runtime_v4's seven NEW checks, never old suites."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--runtime-code',required=True,type=Path)
    parser.add_argument('--bootstrap-code',required=True,type=Path);parser.add_argument('--result',required=True,type=Path)
    args=parser.parse_args();sys.path.insert(0,str(args.runtime_code))
    spec=importlib.util.spec_from_file_location('_new_revision_cases',args.runtime_code/'pure_checks.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    value=module.run(Path(__file__).resolve().parent,args.bootstrap_code)
    with args.result.open('x',encoding='utf-8') as stream:json.dump(value,stream,indent=2)
    print(json.dumps(value))
