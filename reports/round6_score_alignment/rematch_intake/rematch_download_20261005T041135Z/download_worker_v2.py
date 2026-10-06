import os,json,time,subprocess,hashlib,zipfile,shutil,signal,traceback
from pathlib import Path,PurePosixPath
from datetime import datetime,timezone
os.umask(0o077)
run=Path(__file__).resolve().parent
spec=json.loads((run/'job_spec_v2.json').read_text())
archive=run/'archive'/spec['filename']
logpath=run/'download_v2.log'
state={'run_id':spec['run_id'],'state':'STARTING','wrapper_pid':os.getpid(),'started_utc':spec['started_utc'],'expected_bytes':spec['expected_bytes'],'archive_path':str(archive)}
def save():
    state['updated_utc']=datetime.now(timezone.utc).isoformat()
    temp=run/'status.json.tmp'
    temp.write_text(json.dumps(state,ensure_ascii=False,indent=2))
    os.replace(temp,run/'status.json')
def tail_progress():
    if not logpath.exists(): return
    with logpath.open('rb') as f:
        f.seek(max(0,logpath.stat().st_size-16000))
        t=f.read().decode('utf-8','replace')
    lines=[x.strip() for x in t.replace(chr(13),chr(10)).splitlines() if '↓' in x]
    if lines:
        line=lines[-1]
        state['progress_line']=line[-700:]
        amount=line.split('↓',1)[1].split('/',1)[0].strip()
        for unit,mult in [('KB',1024),('MB',1024**2),('GB',1024**3),('B',1)]:
            if amount.endswith(unit):
                try:
                    received=int(float(amount[:-len(unit)])*mult)
                    state['received_bytes_approx']=received
                    state['progress_percent_approx']=round(100*received/spec['expected_bytes'],4)
                except ValueError: pass
                break
p=None
try:
    if shutil.disk_usage(run).free < spec['expected_bytes']: raise RuntimeError('insufficient capacity for expected archive')
    args=[spec['cli'],'download','--saveto',str(run/'archive'),'--retry',str(spec['retry']),'-p',str(spec['parallel']),'-l','1',spec['cloud_path']]
    with logpath.open('wb') as log:
        p=subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,cwd=run,start_new_session=True)
        state.update(state='DOWNLOADING',download_pid=p.pid)
        save()
        t0=time.monotonic()
        while p.poll() is None:
            time.sleep(10)
            tail_progress()
            elapsed=time.monotonic()-t0
            allocated=archive.stat().st_blocks*512 if archive.exists() else 0
            needed=max(0,spec['expected_bytes']-allocated)
            stop_reason=None
            if shutil.disk_usage(run).free < needed: stop_reason='external disk growth leaves insufficient remaining capacity'
            if elapsed > spec['max_seconds']: stop_reason='24-hour download deadline reached'
            state['elapsed_seconds']=round(elapsed,2)
            state['file_size_bytes']=archive.stat().st_size if archive.exists() else 0
            state['allocated_bytes']=allocated
            if stop_reason:
                os.killpg(p.pid,signal.SIGTERM)
                try: p.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    os.killpg(p.pid,signal.SIGKILL)
                    p.wait(timeout=10)
                raise RuntimeError(stop_reason)
            save()
        state['download_exit_code']=p.returncode
    tail_progress()
    if p.returncode != 0: raise RuntimeError('download process exited '+str(p.returncode))
    if not archive.is_file() or archive.stat().st_size != spec['expected_bytes']: raise RuntimeError('downloaded byte count does not match cloud metadata')
    state['state']='VERIFYING'
    save()
    sha=hashlib.sha256(); md=hashlib.md5()
    with archive.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):
            sha.update(b); md.update(b)
    inventory=[]; paths=[]
    with zipfile.ZipFile(archive) as z:
        for i in z.infolist():
            name=i.filename.replace(chr(92),'/')
            parts=PurePosixPath(name).parts
            unsafe=name.startswith('/') or '..' in parts or (bool(parts) and ':' in parts[0])
            is_link=((i.external_attr>>16)&0o170000)==0o120000
            if unsafe or is_link: paths.append({'name':i.filename,'unsafe':unsafe,'symlink':is_link})
            inventory.append({'name':i.filename,'bytes':i.file_size,'compressed_bytes':i.compress_size,'is_dir':i.is_dir(),'crc32':format(i.CRC,'08x')})
        bad=z.testzip()
    (run/'archive_inventory.json').write_text(json.dumps({'members':inventory,'member_count':len(inventory),'uncompressed_bytes':sum(i['bytes'] for i in inventory),'unsafe_entries':paths},ensure_ascii=False,indent=2))
    state.update(sha256=sha.hexdigest(),md5=md.hexdigest(),cloud_md5_matches=md.hexdigest()==spec['cloud_md5_untrusted'],zip_crc_ok=bad is None,zip_bad_member=bad,member_count=len(inventory),uncompressed_bytes=sum(i['bytes'] for i in inventory),unsafe_entry_count=len(paths))
    if bad is not None: raise RuntimeError('ZIP CRC failure')
    if paths: raise RuntimeError('unsafe ZIP member paths or links detected; archive remains unextracted')
    state.update(state='COMPLETE_VERIFIED',completed_utc=datetime.now(timezone.utc).isoformat())
    save()
except Exception as e:
    state.update(state='FAILED',error=str(e),completed_utc=datetime.now(timezone.utc).isoformat())
    save()
    (run/'failure_traceback.txt').write_text(traceback.format_exc())
    raise
