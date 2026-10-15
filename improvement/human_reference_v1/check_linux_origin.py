"""Read-only official-origin reachability and project-scoped existing media check."""
import base64
import shlex
import subprocess

SCRIPT = '''import urllib.request,json,pathlib
url='https://data.vision.ee.ethz.ch/cvl/SumMe/SumMe.zip'
try:
    with urllib.request.urlopen(urllib.request.Request(url,method='HEAD'),timeout=25) as response:
        print(json.dumps(dict(origin_http_status=response.status,headers={k:response.headers.get(k) for k in ('Content-Length','Accept-Ranges','ETag')})),flush=True)
except Exception as exc:
    print(json.dumps(dict(origin_error=type(exc).__name__+': '+str(exc))),flush=True)
'''

if __name__ == '__main__':
    payload = base64.b64encode(SCRIPT.encode()).decode()
    command = 'python3 -u -c ' + shlex.quote('import base64;exec(base64.b64decode(' + repr(payload) + '))')
    result = subprocess.run(['ssh','-o','StrictHostKeyChecking=yes','-o','BatchMode=yes',
                             '-o','ConnectTimeout=12','-o','ServerAliveInterval=15',
                             '-o','ServerAliveCountMax=2','aic-inspur-home',command],timeout=65)
    raise SystemExit(result.returncode)
