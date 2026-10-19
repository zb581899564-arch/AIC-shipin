"""Same exact cache bytes; decompress once before the seekable torch ZIP reader."""
import gzip
import io
from sr_common import W,module,sys

def cache_load(path):
    import torch
    # Passing a GzipFile to torch.load makes ZIP seeks decompress the stream
    # repeatedly. BytesIO preserves the same serialized payload and bit checks.
    with open(path,'rb')as f:data=gzip.decompress(f.read())
    payload=torch.load(io.BytesIO(data),map_location='cpu',weights_only=True)
    lib=W/'twenty_hour_five_20261014_v1/production_stream_cache_v2/code'
    sys.path.insert(0,str(lib));packing=module('sr_pixel_dictionary',lib/'pixel_dictionary.py')
    return packing.unpack(payload)
