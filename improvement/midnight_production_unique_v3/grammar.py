"""Prefix-valid exact JSON grammar, without forcing positive predictions."""
from functools import lru_cache
import itertools,json,re
import regex
from mf_common import FIELDS,require,validate

PIECES={}

def expression(n):
    prefixes=[]
    if n<=1:
        prefixes=[re.escape('{"ordinary":[],"redundant":[],')]
    else:
        for best in range(n):
            others=[i for i in range(n) if i!=best]
            for worst in others:
                text='{"ordinary":'+json.dumps(others,separators=(',',':'))+',"redundant":['+str(worst)+'],'
                prefixes.append(re.escape(text))
    ranges=['\\[\\]']
    for a in range(64):
        ranges.append('\\['+str(a)+',(?:'+'|'.join(map(str,range(a+1,65)))+')\\]')
    interval='(?:'+'|'.join(ranges)+')'
    return '(?:'+'|'.join(prefixes)+')'+','.join(re.escape('"'+f+'":')+interval for f in FIELDS[2:])+'\\}'

class Constraint:
    def __init__(self,tokenizer,input_length,n,eos):
        self.tokenizer=tokenizer;self.offset=input_length;self.n=n;self.eos=eos
        self.regex=regex.compile(expression(n));self.complete=False
        allowed=set('{}[],:"0123456789'+''.join(FIELDS))
        key=id(tokenizer)
        if key not in PIECES:
            pieces=[]
            for token in range(len(tokenizer)):
                text=tokenizer.decode([token],skip_special_tokens=False,clean_up_tokenization_spaces=False)
                if text and all(c in allowed for c in text):pieces.append((token,text))
            PIECES[key]=pieces
        self.pieces=PIECES[key]
    @lru_cache(maxsize=2048)
    def allowed(self,text):
        match=self.regex.fullmatch(text,partial=True)
        require(match is not None,'Generated prefix escaped exact grammar')
        if not match.partial:return self.eos
        values=[token for token,piece in self.pieces if self.regex.fullmatch(text+piece,partial=True) is not None]
        require(values,'No valid grammar token; stop rather than repair output')
        return values
    def __call__(self,batch,input_ids):
        text=self.tokenizer.decode(input_ids[self.offset:].tolist(),skip_special_tokens=True,clean_up_tokenization_spaces=False)
        return self.allowed(text)
    def finish(self,ids):
        text=self.tokenizer.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False)
        match=self.regex.fullmatch(text)
        require(match is not None,'Truncated/invalid output cannot become empty decisions')
        result=validate(json.loads(text),self.n)
        require(json.dumps(result,separators=(',',':'))==text,'Canonical actual output required')
        return result
