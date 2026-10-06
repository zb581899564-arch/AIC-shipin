"""Ephemeral Tailscale-only, Mac-peer-only, capability-authenticated asset sender."""
import argparse
import datetime as dt
import hmac
import hashlib
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import shutil
import threading

HERE=Path(__file__).resolve().parent
manifest_bytes=(HERE/'assets_manifest.json').read_bytes()
assert hashlib.sha256(manifest_bytes).hexdigest()=='88d159b085d4842e7f9660738b9d4a632c9d579544bc43ded335d17ca0acc488'
manifest=json.loads(manifest_bytes);entries=manifest['files']
assert len(entries)==719 and sum(entry['bytes'] for entry in entries)==25599530028
for entry in entries:
    assert any(root in Path(entry['source']).resolve().parents for root in
               (Path('/home/inspur/aic_video_work'),Path('/home/inspur/aic_video_data/videos')))
    assert not Path(entry['source']).is_symlink()
project=Path(manifest['mac_project'])
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def allowed(self):
        return self.client_address[0]=='100.73.195.39' and hmac.compare_digest(self.headers.get('Authorization',''),
                                                                            'Bearer '+self.server.token)
    def do_GET(self):
        if not self.allowed():self.send_error(403);return
        try:
            prefix='/asset/';assert self.path.startswith(prefix)
            index=int(self.path[len(prefix):]);assert 0<=index<len(entries)
            entry=entries[index];source=Path(entry['source']);assert not source.is_symlink()
            assert source.is_file() and source.stat().st_size==entry['bytes']
        except Exception:self.send_error(404);return
        self.send_response(200);self.send_header('Content-Length',str(entry['bytes']));self.end_headers()
        with source.open('rb') as stream:shutil.copyfileobj(stream,self.wfile,length=1<<20)
    def do_POST(self):
        if not self.allowed() or self.path!='/done':self.send_error(403);return
        self.send_response(200);self.end_headers();self.wfile.write(b'closed')
        threading.Thread(target=self.server.shutdown,daemon=True).start()

if __name__=='__main__':
    server=ThreadingHTTPServer(('100.127.244.47',0),Handler);server.token=secrets.token_urlsafe(32)
    deadline=threading.Timer(12*3600,server.shutdown);deadline.daemon=True;deadline.start()
    configuration=dict(url='http://100.127.244.47:'+str(server.server_port),token=server.token)
    path=HERE/'http_transport_config.json'
    with path.open('x') as stream:stream.write(json.dumps(configuration)+'\n')
    path.chmod(0o600)
    (HERE/'http_sender_launch.json').write_text(json.dumps(dict(status='TASK_OWNED_TAILSCALE_MAC_ONLY_SENDER',
        pid=__import__('os').getpid(),port=server.server_port,allowed_peer='100.73.195.39',capability_required=True,
        started_utc=dt.datetime.now(dt.timezone.utc).isoformat()),indent=2)+'\n')
    server.serve_forever();server.server_close();deadline.cancel()
    (HERE/'http_sender_completion.json').write_text(json.dumps(dict(status='CLOSED_AFTER_AUTHENTICATED_MAC_DONE',
        checked_utc=dt.datetime.now(dt.timezone.utc).isoformat()),indent=2)+'\n')
