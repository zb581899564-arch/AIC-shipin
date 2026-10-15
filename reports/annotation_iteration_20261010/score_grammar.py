"""Finite scores grammar; exact length, integers 20..100, no output repair."""
import json

class ScoresGrammar:
    opening='{"scores_x20":['
    values=tuple(str(i) for i in range(20,101))
    def __init__(self,n):
        if type(n) is not int or not 1<=n<=16:raise ValueError('bad count')
        self.n=n
    def scan(self,text):
        if len(text)<=len(self.opening):return self.opening.startswith(text),False
        if not text.startswith(self.opening):return False,False
        count=0;number='';state='number'
        for ch in text[len(self.opening):]:
            if state=='number':
                if ch.isascii() and ch.isdigit():
                    number+=ch
                    if not any(v.startswith(number) for v in self.values):return False,False
                elif ch in ',]' and number in self.values:
                    count+=1;number=''
                    if ch==',' and count<self.n:continue
                    if ch==']' and count==self.n:state='close';continue
                    return False,False
                else:return False,False
            elif state=='close':
                if ch!='}':return False,False
                state='done'
            else:return False,False
        return True,state=='done'
    def valid_prefix(self,t):return self.scan(t)[0]
    def complete(self,t):return self.scan(t)[1]

def candidates(tokenizer):
    chars=set('{}[]":,scores_x2013456789')
    out=[]
    for i in sorted(set(tokenizer.get_vocab().values())):
        t=tokenizer.decode([i],skip_special_tokens=False,clean_up_tokenization_spaces=False)
        if t and t.isascii() and set(t)<=chars:out.append(i)
    return tuple(out)

class Constraint:
    def __init__(self,tok,prompt,n,ids):
        self.tok=tok;self.prompt=prompt;self.g=ScoresGrammar(n);self.ids=ids;self.cache={}
        eos=tok.eos_token_id;self.eos=[eos] if type(eos) is int else list(eos)
    def __call__(self,batch,seq):
        ids=tuple(seq.tolist()[self.prompt:])
        if ids in self.cache:return self.cache[ids]
        text=self.tok.decode(ids,skip_special_tokens=False,clean_up_tokenization_spaces=False)
        if self.g.complete(text):out=self.eos
        elif self.g.valid_prefix(text):
            out=[]
            for i in self.ids:
                t=self.tok.decode((*ids,i),skip_special_tokens=False,clean_up_tokenization_spaces=False)
                if t.startswith(text) and len(t)>len(text) and self.g.valid_prefix(t):out.append(i)
        else:out=[]
        if not out:raise ValueError('constrained dead end; no fallback')
        self.cache[ids]=out;return out
    def finish(self,ids):
        ids=list(ids)
        if ids and ids[-1] in self.eos:ids.pop()
        if any(i in self.eos for i in ids):raise ValueError('early EOS')
        text=self.tok.decode(ids,skip_special_tokens=False,clean_up_tokenization_spaces=False)
        if not self.g.complete(text):raise ValueError('incomplete output')
        return text,json.loads(text)

def selftest():
    for n in range(1,17):
        g=ScoresGrammar(n)
        for value in (20,21,99,100):
            s=json.dumps({'scores_x20':[value]*n},separators=(',',':'))
            assert g.complete(s) and all(g.valid_prefix(s[:i]) for i in range(len(s)+1))
        for bad in (19,101,True,20.0):
            assert not g.complete(json.dumps({'scores_x20':[bad]*n},separators=(',',':')))
        for count in (0,n+1):assert not g.complete(json.dumps({'scores_x20':[20]*count},separators=(',',':')))
    print('PASS exact count/range/all canonical prefixes')
if __name__=='__main__':selftest()
