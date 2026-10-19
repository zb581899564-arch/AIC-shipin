import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
REPORT=ROOT/'reports/trajectory_risk_20261017_v1'
REPORT.mkdir(exist_ok=True)
OPTIONS=['-o','BatchMode=yes','-o','ConnectTimeout=12','-o','ProxyCommand="C:/Program Files/Tailscale/tailscale.exe" nc %h %p']
def ssh(code,timeout=60):
    p=subprocess.run(['ssh']+OPTIONS+['aic-inspur-tailscale','python3 -'],input=code,text=True,capture_output=True,timeout=timeout)
    if p.returncode: raise RuntimeError(p.stderr+'\n'+p.stdout)
    return p.stdout
if __name__=='__main__':
    code=Path(sys.argv[1]).read_text(encoding='utf-8')
    result=ssh(code,int(sys.argv[3]) if len(sys.argv)>3 else 60)
    (REPORT/sys.argv[2]).write_text(result,encoding='utf-8')
    print(result)
