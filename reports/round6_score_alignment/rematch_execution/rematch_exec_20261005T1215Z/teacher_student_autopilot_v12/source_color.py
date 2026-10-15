"""Explicit registered sample conversion for one SHA-pinned unsupported transfer tag."""
from autopilot_common import *

def settings():
    return read(HERE / "config.json")
import ast
from fractions import Fraction


def authorized_source(source_sha256):
    return source_sha256 in settings()['source_color_repair']['sources']


def convert_frame(frame, source_sha256, output):
    require(output in ('rgb24', 'bgr24'), 'only declared RGB/BGR source conversions allowed')
    config = settings()['source_color_repair']; profile = config['sources'].get(source_sha256)
    if profile is None:
        return frame.to_ndarray(format=output)
    require(frame.format.name == profile['format'] and frame.width == profile['width'] and
        frame.height == profile['height'] and all(getattr(frame, name) == profile[name] for name in
            ('color_trc', 'colorspace', 'color_primaries', 'color_range')),
        'SHA-pinned unsupported source color profile changed')
    original = frame.color_trc
    try:
        # Preserve decoded YUV sample planes, range, clock and geometry. This
        # is an explicit registered YUV->RGB recipe, not a recovered gamma curve.
        frame.color_trc = config['transfer_tag_for_conversion']
        result = frame.reformat(format=output, src_colorspace=config['matrix'],
            dst_colorspace=config['matrix']).to_ndarray()
    finally:
        frame.color_trc = original
    require(result.shape == (profile['height'], profile['width'], 3) and str(result.dtype) == 'uint8',
            'declared source conversion geometry/dtype changed')
    return result


def normalized_native_input(path):
    text = Path(path).read_text(encoding='utf-8-sig')
    new = 'from source_color import convert_frame\n            image = convert_frame(frame, w["source_sha256"], "rgb24")'
    require(text.count(new) == 1, 'unexpected native conversion changes')
    return ast.dump(ast.parse(text.replace(new, 'image = frame.to_ndarray(format="rgb24")')),
                    include_attributes=False)


def verify_default_decoder_ast(path, old_path):
    text = Path(path).read_text(encoding='utf-8-sig')
    substitutions = (
        ("from source_color import authorized_source, ColorNativeReader\n        self.color_special=authorized_source(item['source_sha256'])\n        if self.color_special:\n            self.reader=ColorNativeReader(item,clock)\n        elif self.native:", 'if self.native:'),
        ('        if self.color_special:return self.reader.get(index)\n', ''),
        ('if self.color_special:self.reader.close()\n        elif self.native:self.reader=None', 'if self.native:self.reader=None'))
    for new, original in substitutions:
        require(text.count(new) == 1, 'unexpected registered source decoder changes')
        text = text.replace(new, original)
    def node(source):
        tree = ast.parse(source)
        tree.body = [n for n in tree.body if getattr(n,'name',None) == 'OrdinalReader']
        require(len(tree.body) == 1, 'default source decoder missing')
        return ast.dump(tree, include_attributes=False)
    require(node(text) == node(Path(old_path).read_text(encoding='utf-8-sig')),
            'default source-field decoder changed beyond declared source branch')
    return True


def validate_original_decode_failure(item, clock, index, start, end, window):
    require(authorized_source(item['source_sha256']) and item['video_id'] ==
        settings()['source_color_repair']['sources'][item['source_sha256']]['video_id'],
        'unregistered failed source cannot be recovered under the color repair')
    errors = window.get('parse_errors') or []
    require(window.get('start_sec') == start and window.get('end_sec') == end and window.get('index') == index and
        window.get('clock_record_sha256') == clock['clock_record_sha256'] and window.get('clock_branch') == clock['branch'] and
        window.get('status') == 'INFERENCE_FAILURE' and window.get('output_valid') is False and
        window.get('parsed_segments') is None and window.get('raw_output') is None and
        window.get('video_identity') is None and window.get('failure_to_empty_conversions') == 0 and
        len(errors) == 1 and errors[0].startswith('OSError: [Errno 95] Operation not supported') and
        'fmt:yuv420p' in errors[0] and 'trc:log316' in errors[0] and 'fmt:rgb24' in errors[0],
        'original failure is not the declared pre-model unsupported transfer conversion')


class ColorNativeReader:
    """Source-field BGR with the exact same registered conversion as temporal RGB."""
    def __init__(self, item, clock):
        import av
        require(authorized_source(item['source_sha256']), 'unregistered special source reader')
        require(sha(item['source_path']) == item['source_sha256'], 'source color bytes changed')
        self.item = item; self.container = av.open(item['source_path'])
        require(len(self.container.streams.video) == 1, 'ambiguous special source stream')
        self.frames = iter(self.container.decode(self.container.streams.video[0]))
        arrays = clock['arrays']; tick = Fraction(arrays['raw_time_base'])
        self.points = [float(value*tick) for value in arrays['native_pts_ticks']]
        require(len(self.points) == item['n_frames'], 'special native frame denominator changed')
        self.next = 0; self.last = None

    def get(self, index):
        require(type(index) is int and 0 <= index < self.item['n_frames'], 'invalid special source ordinal')
        if index == self.next-1 and self.last is not None:
            return self.last
        require(index >= self.next, 'backwards/random special source seek prohibited')
        while self.next <= index:
            frame = next(self.frames)
            require(frame.pts is not None and frame.time_base is not None and
                float(frame.pts*frame.time_base) == self.points[self.next], 'special source actual PTS changed')
            self.next += 1
        image = convert_frame(frame, self.item['source_sha256'], 'bgr24')
        self.last = (image, hashlib.sha256(image.tobytes()).hexdigest())
        return self.last

    def close(self):
        self.container.close()
