"""Frozen author PANN with original Torchlibrosa forwards, no global installs.

Only frontend constructor dependencies are supplied locally: periodic Hann and
the checkpoint's own published Mel matrix. All original forward methods and
learned tensors remain unchanged and loading is strict.
"""
import ast
import types
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from common import ROOT, read, checked


def definitions(path, names, namespace):
    tree = ast.parse(path.read_text())
    nodes = [node for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef))
        and node.name in names]
    if {node.name for node in nodes} != set(names):
        raise ValueError('Exact required author definitions missing')
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), namespace)


def frontend(state):
    def window(name, size, fftbins=True):
        if name != 'hann' or not fftbins:
            raise ValueError('Only the checkpoint Hann profile is admitted')
        return torch.hann_window(size, periodic=True, dtype=torch.float64).numpy()

    def mel(**kwargs):
        if (kwargs['sr'], kwargs['n_fft'], kwargs['n_mels'], kwargs['fmin'], kwargs['fmax']) != (32000, 1024, 64, 50, 14000):
            raise ValueError('Author 32k Mel profile changed')
        return state['logmel_extractor.melW'].numpy().T.copy()

    def pad_center(value, size):
        if len(value) != size:
            raise ValueError('Only full FFT window supported')
        return value

    namespace = dict(torch=torch, nn=nn, F=F, np=np,
        librosa=types.SimpleNamespace(filters=types.SimpleNamespace(get_window=window, mel=mel),
            util=types.SimpleNamespace(pad_center=pad_center)))
    definitions(ROOT/'author/torchlibrosa__stft.py',
        ['DFTBase', 'STFT', 'Spectrogram', 'LogmelFilterBank'], namespace)
    return namespace


def load():
    lock = read(ROOT/'acquisition05_completion.json')
    state = torch.load(checked(lock['weight']), map_location='cpu', weights_only=True)['model']
    namespace = frontend(state)
    namespace['SpecAugmentation'] = lambda **kwargs: nn.Identity()
    code = read(ROOT/'author_source_acceptance.json')['files']
    definitions(checked(code['pytorch/pytorch_utils.py']),
        ['do_mixup', 'interpolate', 'pad_framewise_output'], namespace)
    definitions(checked(code['pytorch/models.py']),
        ['init_layer', 'init_bn', 'ConvBlock', 'AttBlock', 'Cnn14_DecisionLevelAtt'], namespace)
    model = namespace['Cnn14_DecisionLevelAtt'](sample_rate=32000, window_size=1024,
        hop_size=320, mel_bins=64, fmin=50, fmax=14000, classes_num=527)
    model.load_state_dict(state, strict=True)
    loaded = model.state_dict()
    if set(loaded) != set(state) or not all(torch.equal(loaded[key], value) for key, value in state.items()):
        raise ValueError('Strict author checkpoint tensor identity failed')
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    return model.eval(), len(state)


def frontend_check(model):
    t = torch.arange(8192, dtype=torch.float32)/32000
    wave = (torch.sin(2*torch.pi*440*t)+.1*torch.cos(2*torch.pi*1730*t))[None]
    actual = model.spectrogram_extractor(wave)
    expected = torch.stft(wave, n_fft=1024, hop_length=320,
        window=torch.hann_window(1024), center=True, pad_mode='reflect',
        return_complex=True).abs().square().transpose(1, 2)[:, None]
    if not torch.allclose(actual, expected, rtol=2e-4, atol=.03):
        raise ValueError('Stored DFT frontend does not match independent FFT')
    mel = torch.matmul(actual, model.logmel_extractor.melW)
    expected_log = 10*torch.log10(torch.clamp(mel, min=1e-10))
    if not torch.equal(model.logmel_extractor(actual), expected_log):
        raise ValueError('Original log-Mel forward differs from independent formula')
    return dict(DFT_vs_independent_FFT=True, logmel_vs_independent_formula=True,
        max_spectrogram_abs_error=float((actual-expected).abs().max()))
