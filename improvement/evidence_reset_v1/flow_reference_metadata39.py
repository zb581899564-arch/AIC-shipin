"""Bounded original-publisher ZIP directory/README acquisition; no image/flow."""
import gzip,hashlib,io,json,os,socket,subprocess,time,traceback,urllib.request,zipfile
from pathlib import Path
N=Path(__file__).resolve().parent
URL='https://files.is.tue.mpg.de/sintel/MPI-Sintel-complete.zip'
def ref(p):
 p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def save(p,v):
 with Path(p).open('x')as f:json.dump(v,f,indent=2,allow_nan=False)
def main():
 started=time.monotonic();reg=json.loads((N/'registration39.json').read_text());assert reg['code_ref']==ref(__file__)and socket.gethostname()=='inspur-NP5570M5'
 headers={'User-Agent':'AIC-student-research-metadata/1.0','Accept-Encoding':'identity'}
 with urllib.request.urlopen(urllib.request.Request(URL,method='HEAD',headers=headers),timeout=20)as response:
  assert response.geturl()==URL and response.status==200
  total=int(response.headers['Content-Length']);etag=response.headers.get('ETag');modified=response.headers.get('Last-Modified')
  save(N/'author_archive_head39.json',dict(url=URL,total_bytes=total,etag=etag,last_modified=modified,metadata_only=True))
 assert total>0 and(etag or modified)
 class Reader(io.RawIOBase):
  def __init__(self):self.pos=0;self.used=0;self.requests=0;self.cache={}
  def readable(self):return True
  def seekable(self):return True
  def tell(self):return self.pos
  def seek(self,offset,whence=0):
   self.pos=offset if whence==0 else self.pos+offset if whence==1 else total+offset
   assert 0<=self.pos<=total;return self.pos
  def read(self,size=-1):
   size=total-self.pos if size<0 else min(size,total-self.pos)
   if not size:return b''
   key=self.pos,size
   if key in self.cache:self.pos+=size;return self.cache[key]
   assert time.monotonic()-started<300 and self.requests<32 and self.used+size<=4000000,'Boundedmetadata budget; never wholearchive fallback'
   a=self.pos;b=a+size-1;hh=dict(headers,Range=f'bytes={a}-{b}')
   if etag and not etag.startswith('W/'):hh['If-Range']=etag
   elif modified:hh['If-Range']=modified
   with urllib.request.urlopen(urllib.request.Request(URL,headers=hh),timeout=20)as response:
    assert response.geturl()==URL and response.status==206 and response.headers.get('Content-Range')==f'bytes {a}-{b}/{total}','Strictsource206range only'
    assert(etag is None or response.headers.get('ETag')==etag)and(modified is None or response.headers.get('Last-Modified')==modified)
    payload=response.read(size+1);assert len(payload)==size
   self.used+=size;self.requests+=1;self.pos+=size;self.cache[key]=payload
   path=N/(f'range_{self.requests:02d}_{a}_{size}.bin')
   with path.open('xb')as f:f.write(payload)
   with(N/'ranges39.jsonl').open('a')as f:f.write(json.dumps(dict(start=a,length=size,ref=ref(path)))+'\n')
   return payload
 source=Reader();docs=[]
 with zipfile.ZipFile(source)as archive:
  infos=archive.infolist();assert 0<len(infos)<100000
  index=[dict(name=z.filename,bytes=z.file_size,compressed=z.compress_size,CRC=z.CRC,method=z.compress_type,flags=z.flag_bits,offset=z.header_offset)for z in infos]
  data=gzip.compress(json.dumps(index,separators=(',',':')).encode(),mtime=0)
  with(N/'author_archive_directory39.json.gz').open('xb')as f:f.write(data)
  for z in infos:
   name=Path(z.filename).name.lower()
   if z.is_dir()or not(name.startswith('readme')or name.startswith('license')or name.startswith('copying')):continue
   assert z.file_size<=65536 and len(docs)<16,'Textonlyexplicit budget'
   raw=archive.read(z);text=raw.decode('utf-8')
   path=N/(f'publisher_text_{len(docs):02d}.txt')
   with path.open('xb')as f:f.write(raw)
   docs.append(dict(member=z.filename,CRC=z.CRC,ref=ref(path),text=text))
 save(N/'completion39.json',dict(status='COMPLETE_ORIGINAL_PUBLISHER_DIRECTORY_AND_TEXT_ONLY',url=URL,archive_bytes=total,
  directory_ref=ref(N/'author_archive_directory39.json.gz'),members=len(index),texts=docs,
  actual_HTTP_payload_bytes=source.used,unique_range_requests=source.requests,seconds=time.monotonic()-started,
  new_images=0,new_flow_labels=0,new_models=0,new_updates=0,source_use_admitted=False,production_admitted=False,new_ZIP=0,official_submissions=0,
  scope='PublisherREADME/license evidence pending actualhuman-readable evaluation; archive availability/code license does not itself admitmedia. Opticalflow GT is transport, notcompositionGT.'))
 print(json.dumps(dict(completion_ref=ref(N/'completion39.json'),status='METADATA_COMPLETE_NO_MEDIA_OR_MODEL',actual_payload=source.used)))
if __name__=='__main__':
 try:main()
 except BaseException:
  save(N/'failure39.json',dict(status='ACTUAL_METADATA_FAILURE_NO_AUTOMATIC_RETRY',traceback=traceback.format_exc()));raise
