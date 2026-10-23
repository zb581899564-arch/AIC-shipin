"""Exact ordinal-score JSON contract; all-zero output is a valid semantic abstention."""
import json


class ScorePattern:
    def __init__(self,known):
        self.known=tuple(known)
        if not known or any(type(x) is not bool for x in known):raise ValueError('Explicit observed-word mask required')
        self.pattern='{"scores":['+','.join('?' if x else '0' for x in known)+']}'

    def prefix(self,text):
        return len(text)<=len(self.pattern) and all(
            expected==actual or expected=='?' and actual in '0123'
            for expected,actual in zip(self.pattern,text))

    def complete(self,text):return len(text)==len(self.pattern) and self.prefix(text)

    def parse(self,text):
        if not self.complete(text):raise ValueError('Incomplete or invalid native score vector; no repair')
        values=json.loads(text)['scores']
        if len(values)!=len(self.known) or any(type(x) is not int or not 0<=x<=3 for x in values):
            raise ValueError('Ordinal score schema differs')
        return values


def candidates(tokenizer):
    chars=frozenset('{}[]":,scores0123')
    result=[]
    for token in sorted(set(tokenizer.get_vocab().values())):
        text=tokenizer.decode([token],skip_special_tokens=False,clean_up_tokenization_spaces=False)
        if text and text.isascii() and set(text)<=chars:result.append(token)
    return tuple(result)


class Constraint:
    def __init__(self,tokenizer,prompt_length,known,token_ids,eos):
        self.tokenizer=tokenizer;self.length=prompt_length;self.grammar=ScorePattern(known)
        self.tokens=token_ids;self.eos=eos;self.cache={}

    def decode(self,ids):
        return self.tokenizer.decode(list(ids),skip_special_tokens=False,clean_up_tokenization_spaces=False)

    def __call__(self,batch,ids):
        tail=tuple(ids.tolist()[self.length:])
        if tail in self.cache:return self.cache[tail]
        text=self.decode(tail)
        if self.grammar.complete(text):allowed=[self.eos]
        elif self.grammar.prefix(text):
            allowed=[]
            for token in self.tokens:
                continued=self.decode(tail+(token,))
                if len(continued)>len(text) and continued.startswith(text) and self.grammar.prefix(continued):allowed.append(token)
        else:allowed=[]
        if not allowed:raise RuntimeError('Score grammar dead end; no fallback')
        self.cache[tail]=allowed;return allowed


def contracts():
    grammar=ScorePattern([True,False,True])
    if grammar.parse('{"scores":[0,0,0]}')!=[0,0,0]:raise ValueError('Successful abstention rejected')
    if grammar.parse('{"scores":[3,0,2]}')!=[3,0,2]:raise ValueError('Known mask differs')
    if grammar.prefix('{"scores":[3,1') or grammar.prefix('{"scores":[4'):raise ValueError('Unknown or ordinal value admitted')
    if grammar.complete('{"scores":[3,0]}'):raise ValueError('Short vector accepted')
    return dict(state='PASS',checks=4,explicit_unknown_mask=True,successful_all_zero_distinct_from_failure=True)
