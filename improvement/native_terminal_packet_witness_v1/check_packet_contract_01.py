"""One new exact packet synthetic check; no media, PyAV, Torch or GPU."""
from packet_contract import PacketUnavailable, packet_row, resolve


def rejected(fn):
    try:
        fn()
    except PacketUnavailable:
        return
    raise AssertionError('Invalid packet witness was accepted')


def main():
    row = packet_row(104, 2, '1/25', 47, 0, 'a'*64)
    value = resolve([row], '104/25', '104/25', '1/5', '106/25')
    assert value['physical_end_exact'] == '101/25'
    rejected(lambda: resolve([], '104/25', '104/25', '1/5'))
    rejected(lambda: resolve([row, row], '104/25', '104/25', '1/5'))
    rejected(lambda: resolve([packet_row(104, 0, '1/25', 47, 0)], '104/25', '104/25', '1/5'))
    rejected(lambda: resolve([row], '105/25', '104/25', '1/5'))
    rejected(lambda: resolve([row], '104/25', '104/25', '1/5', '107/25'))
    return dict(status='PASS_NEW_EXACT_PACKET_POSITIVE_NONE_AMBIGUOUS_ZERO_MAX_OLD_END_CHECK',
                checks=6, media_reads=0, packet_demuxes=0, frame_decodes=0,
                processor_calls=0, model_calls=0, Torch_imports=0)


if __name__ == '__main__':
    import json
    print(json.dumps(main(), sort_keys=True))
