"""Reject incomplete RGB before importing runtime/processor or creating outputs."""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
import prepare_processor_remote as prepare


if __name__ == '__main__':
    with tempfile.TemporaryDirectory(prefix='aic_processor_gate_') as directory:
        root = Path(directory)
        rgb = root/'rgb'
        rgb.mkdir()
        (rgb/'completion.json').write_text(json.dumps(dict(status='FAILED')))
        output = root/'uncreated_processor'
        with patch.object(prepare, 'RGB', rgb), patch.object(prepare, 'OUT', output), \
                patch.object(prepare.socket, 'gethostname', return_value='inspur-NP5570M5'), \
                patch.object(prepare, 'load_cpu_runtime', side_effect=AssertionError('Processor must not load')) as loader:
            try:
                prepare.main(root/'registration.json',root/'EVALUATION_POLICY.md',root/'NATIVE_MAPPING_CONTRACT_V2.md')
            except ValueError as error:
                assert str(error) == 'All registered original RGB windows must pass before processor preparation'
            else:
                raise AssertionError('Incomplete real RGB stage was admitted')
            assert not output.exists() and loader.call_count == 0
    print('PASS incomplete RGB rejected before processor/runtime loading or output mutation; no actual processor run')
