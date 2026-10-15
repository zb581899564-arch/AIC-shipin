"""Independent row/parameter declaration check supplementing frozen geometry checks."""
import json
import math
import sys
from pathlib import Path

EXPECTED_PARAMS = 8782459120


def validate(path):
    rows = [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]
    assert len(rows) == 426
    assert {row['video_id'] for row in rows} == {str(i) for i in range(426)}
    for row in rows:
        assert set(row) == {'video_id', 'targetRatioWH', 'predictions', 'model_params_b'}
        value = row['model_params_b']
        assert type(value) in (int, float) and math.isfinite(value)
        assert 0 < value <= 9 and value == EXPECTED_PARAMS / 10**9
    return dict(status='PASS_426_CURRENT_ROW_KEYS_AND_ACTUAL_MODEL_PARAMETER_DECLARATION',
                rows=len(rows), actual_parameters=EXPECTED_PARAMS, model_params_b=EXPECTED_PARAMS / 10**9,
                source='Previously accepted actual original B model parameter count; no new model or adapter')


if __name__ == '__main__':
    result = validate(sys.argv[1])
    with Path(sys.argv[2]).open('x', encoding='utf-8') as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    print(json.dumps(result))
