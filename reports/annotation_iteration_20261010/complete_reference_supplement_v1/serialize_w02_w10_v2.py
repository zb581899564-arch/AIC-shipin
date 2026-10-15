"""Independent explicit literal repair; original failed script/reference preserved."""
from pathlib import Path
original=Path(__file__).with_name('serialize_w02_w10.py')
source=original.read_text(encoding='utf-8')
old="[['0','0.7273333333333333'],['4.531133333333333','7.250516666666667'],['19.2792','20.563816666666667'],['22.115366666666667','23.550133333333334'],['29.255833333333333','30']]"
new="[['0','0.7273333333333333'],['4.531133333333333','7.250516666666666'],['19.2792','20.563816666666664'],['22.115366666666663','23.55013333333333'],['29.25583333333333','30']]"
assert source.count(old)==1
exec(compile(source.replace(old,new),str(original), 'exec'))
