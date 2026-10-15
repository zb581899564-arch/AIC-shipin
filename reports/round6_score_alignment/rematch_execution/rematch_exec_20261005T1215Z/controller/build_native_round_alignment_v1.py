"""One finite train-serving ordinal alignment hypothesis; immutable ancestors."""
from pathlib import Path
import re

RUN=Path(__file__).resolve().parent.parent
OUT=RUN/'native_round_alignment_v1'
MAPPING=(('aic_ND_', 'aic_NRA_'),('nested_density_v1','native_round_alignment_v1'),
 ('NESTED_NATIVE_DENSITY','NATIVE_ROUND_ALIGNMENT'),('NESTED_DENSITY','NATIVE_ROUND_ALIGNMENT'),
 ('decode_nested_window','decode_round_window'),('encode_nested','encode_round'),('dense_window','round_window'),
 ('nested_indices','round_indices'),('nested-density','native-nearest-alignment'),('nested density','native nearest alignment'),
 ('density','round_alignment'),('Density','Round alignment'),('DENSITY','ROUND_ALIGNMENT'),
 ("'D'","'Q'"),('all104_D_minus_B0','all104_Q_minus_B0'),('expanded72_D_minus_B0','expanded72_Q_minus_B0'),
 ('BASE_FLOOR64_PLUS_ALL_ADJACENT_NATIVE_ORDINAL_MIDPOINTS','NATIVE_NEAREST64_SAME_COUNT_ENDPOINTS'),
 ('SAME_TOTAL_VIDEO_PIXEL_BUDGET_ACTUAL_GRID_RECORDED_NOT_ASSUMED_EQUAL','SAME_FRAME_COUNT_PIXEL_GRID_AND_B0_PROMPT'),
 ('ORIGINAL_B0_PROMPT_WITH_NESTED_NATIVE_DENSITY','ORIGINAL_B0_PROMPT_WITH_NATIVE_NEAREST64_ALIGNMENT'))

def main():
    assert not OUT.exists(),'never rebuild an existing experiment'
    OUT.mkdir()
    for p in (RUN/'nested_density_v1').iterdir():
        if p.suffix!='.py':continue
        text=p.read_text(encoding='utf-8')
        text=re.sub(r'\bnd_', 'nr_', text)
        for a,b in MAPPING:text=text.replace(a,b)
        dest=OUT/p.name.replace('nd_','nr_');dest.write_text(text,encoding='utf-8',newline='\n')
    p=RUN/'controller/register_nested_density_v1.py'
    text=p.read_text(encoding='utf-8')
    text=re.sub(r'\bnd_', 'nr_', text)
    for a,b in MAPPING:text=text.replace(a,b)
    (RUN/'controller/register_native_round_alignment_v1.py').write_text(text,encoding='utf-8',newline='\n')
    print('PASS_UNFROZEN_INDEPENDENT_ROUND_ALIGNMENT_SCAFFOLD')

if __name__=='__main__':main()
