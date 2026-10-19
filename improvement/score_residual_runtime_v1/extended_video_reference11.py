"""CONDITIONAL VideoXum28 metadata registration / first new-purpose CPU images.

No launcher, downloader, teacher, model load or GPU operation. Nothing executes
on import. This file alone is NOT data/GPU admission; the registered prior
direction must actually STOP and explicit CPU preparation authority is required.

Protocol interface (ROOT/protocol.json, explicit AIC_RESIDUAL_ROOT):
  schema: EXTENDED_VIDEO_REFERENCE11_CONDITIONAL
  root: exact ROOT string
  prior_direction_result: {path, sha256}  # real STOP, production_allowed=false
  new_purpose_CPU_preparation_authorized: bool
  model_config: {path, sha256}  # existing b_score_aligned_package_v4/config.json
  cohorts: [
    {name: accepted20, cpu_completion:{path,sha256},
     b0_completion:{path,sha256}, b0_export:{path,sha256},
     replay_completion:{path,sha256}},
    {name: new8, ...same references...}]
  CPU_tensor_estimates_by_source: {V00: int_bytes, ..., V27: int_bytes}
  reserved_future_output_bytes: nonnegative int

register() verifies ALL declared and derived existing files, including media,
old input/done/request/raw, exact clock/mapping and original10 references, then
creates ROOT/reference_manifest11.json. It never substitutes a missing source.
prepare() re-verifies the closure, requires explicit CPU authority and creates
ROOT/inputs/Vxx/{native.npz,clock.json,chunk_*.pt,acceptance.json}, separate
ROOT/labels/Vxx.npy (native frames x10 bool), and CPU/label receipts. Labels are
never copied into native.npz, image tensors, prompts, or CPU feature manifests.
Missing/deleted historical RGB caches are not used or claimed to still exist.
"""
import bisect
import math
import sys
from fractions import Fraction as F
from common_runtime import *

SCHEMA = 'EXTENDED_VIDEO_REFERENCE11_CONDITIONAL'
SOURCE_NAMES = (
    'v_fVg3StD8LL0','v_SEebwJMNMQs','v_OzjjQ4SZ8PY','v_eWP99kNayuU',
    'v_b_iUgvzb1-0','v_LHewj6shKGw','v_tgPjcWP7Vig','v_fdd5ixvEXOE',
    'v_InA8Xbg-hvo','v_D9A_9FH7e-A','v_QCj7IGUGs2Y','v_YL3MvJVk6u0',
    'v_qH3HnhEaeok','v_pYbOylWZx-s','v_jzDXtd0__DM','v_2Sev8z4P7pE',
    'v_mb1LoOTM_NI','v_Jz9ZxenBLa8','v_m4EcgRjCpi8','v_WBkqGBFsdgI',
    'v_V_Nj_BhesEY','v_dSww-S8qyCM','v_Jh07fhoPWEI','v_4Xvn1xXvYdU',
    'v_PDjtB578yRk','v_WhYyvKiwLc8','v_xBtydVn3MVI','v_htfrXrKUIzg')
COHORTS = (
    ('accepted20',20,92,'203841bb779938771beec76461b53e5c972859914ba5d296d859c7476b7d2669',
     'PASS_EFFECTIVE20_NATIVE64_CPU_INPUTS_NOT_YET_GPU_LOCK_ADMISSION'),
    ('new8',8,39,'3c0c6cf6d3cc120b983f3d74aa91788a7aefe0502beea3a2a9a6955928699352',
     'PASS_FRESH_CONFIRM8_NATIVE64_CPU_INPUTS_PENDING_INDEPENDENT_ADMISSION'))
REFERENCE_SCOPE = 'Original10 human summary preference intervals; unselected is not ORDINARY; no official joint GT'


def file_ref(path, expected=None, size=None):
    path = Path(path)
    require(path.is_absolute() and path.is_file(), 'Missing existing absolute file: '+str(path))
    if size is not None: require(path.stat().st_size == size, 'Existing file size changed: '+str(path))
    digest = sha(path)
    if expected is not None: require(digest == expected, 'Existing file SHA changed: '+str(path))
    return dict(path=str(path),sha256=digest,bytes=path.stat().st_size)


def bound(ref):
    return file_ref(ref['path'],ref['sha256'],ref.get('bytes'))


def exact(value):
    require(not isinstance(value,(bool,float)), 'Exact source seconds must be string/int rational, never float')
    return F(value)


def protocol():
    require(os.environ.get('AIC_RESIDUAL_ROOT') and Path(os.environ['AIC_RESIDUAL_ROOT']).resolve() == ROOT.resolve(), 'Explicit independent AIC_RESIDUAL_ROOT required')
    p = read(ROOT/'protocol.json')
    require(p['schema'] == SCHEMA and Path(p['root']).resolve() == ROOT.resolve(), 'Independent protocol/root schema')
    require(type(p['new_purpose_CPU_preparation_authorized']) is bool, 'Explicit preparation authority field required')
    previous = read(bound(p['prior_direction_result'])['path'])
    require(previous['new_production_allowed'] is False and str(previous['status']).startswith('STOP_'), 'Prior direction must actually STOP; no speculative replacement')
    require([c['name'] for c in p['cohorts']] == ['accepted20','new8'], 'Exact two immutable source cohorts in original order')
    estimates = p['CPU_tensor_estimates_by_source']
    require(set(estimates) == {'V%02d'%i for i in range(28)} and all(type(x) is int and x > 0 for x in estimates.values()), 'Actual prospective per-source CPU byte estimates required')
    require(type(p['reserved_future_output_bytes']) is int and p['reserved_future_output_bytes'] >= 0, 'Future output reservation required')
    return p


def normalize_clock(clock):
    pts = [exact(x) for x in clock['original_exact_pts']]
    end = exact(clock['physical_end_exact']); duration = exact(clock['last_frame_duration_exact'])
    require(clock['original_zero_origin_verified'] is True and clock['timeline_shift_applied'] is False and
            exact(clock['first_original_pts_exact']) == 0 and pts and pts[0] == 0, 'Original zero-origin clock required; no shift/stretch fallback')
    require(len(pts) == clock['native_frames'] and all(b > a for a,b in zip(pts,pts[1:])) and
            duration > 0 and end == pts[-1]+duration, 'Exact complete native PTS and final positive duration')
    result = dict(clock)
    result.update(normalized_exact_pts=clock['original_exact_pts'].copy(),n_frames=len(pts),
                  normalization='IDENTITY_ORIGINAL_ZERO_ORIGIN_NO_SHIFT_NO_STRETCH')
    return result


def reference_row(value, name, end):
    require(isinstance(value,list) and len(value) == 1 and value[0]['video_id'] == name, 'Exactly one original reference source')
    row = value[0]; raters = row['annotator_intervals_exact_seconds']
    require(isinstance(raters,list) and len(raters) == 10, 'Exactly original10 annotators required')
    for intervals in raters:
        require(isinstance(intervals,list), 'Annotator intervals list required')
        for pair in intervals:
            require(len(pair) == 2 and 0 <= exact(pair[0]) < exact(pair[1]) <= end, 'Original reference outside native seconds; no clipping/stretching')
    return row


def native_ranges(pts, lo, hi, segments):
    ranges = []; exact_segments = []; previous = F(0)
    for pair in segments:
        require(len(pair) == 2 and all(type(x) in (int,float) and math.isfinite(x) for x in pair), 'Original parsed B0 segment schema')
        # This is the exact decimal spelling of the ACCEPTED old answer, not a
        # new boundary or a float-rounded source window endpoint.
        a,b = (F(str(x)) for x in pair)
        require(previous <= a < b <= hi-lo, 'Original B0 local segments escaped exact original window')
        left,right = bisect.bisect_left(pts,lo+a),bisect.bisect_left(pts,lo+b)
        require(0 <= left < right <= len(pts), 'Original B0 segment has no actual native frames')
        ranges.append([left,right]); exact_segments.append([str(a),str(b)]); previous = b
    return ranges,exact_segments


def occupied_sampling(clock):
    """Exact half-second occupied cells, midpoint-nearest native observation."""
    import numpy as np
    pts = [exact(x) for x in clock['normalized_exact_pts']]; end = exact(clock['physical_end_exact'])
    cells = np.asarray([int(t*2) for t in pts],dtype=np.int64); occupied = np.unique(cells)
    groups = np.searchsorted(occupied,cells).astype(np.int64); ordinals = []
    for cell in occupied.tolist():
        a = F(cell,2); b = min(a+F(1,2),end)
        lo,hi = bisect.bisect_left(pts,a),bisect.bisect_left(pts,b)
        require(lo < hi, 'Occupied cell has no actual native observation')
        mid = (a+b)/2; pos = bisect.bisect_left(pts,mid,lo,hi)
        ordinals.append(min([j for j in (pos-1,pos) if lo <= j < hi],key=lambda j:(abs(pts[j]-mid),j)))
    return groups,np.asarray(ordinals,dtype=np.int64)


def native_reference_labels(clock, row):
    import numpy as np
    pts = [exact(x) for x in clock['normalized_exact_pts']]
    labels = np.zeros((len(pts),10),dtype=np.bool_)
    for rater,intervals in enumerate(row['annotator_intervals_exact_seconds']):
        for a,b in intervals:
            labels[bisect.bisect_left(pts,exact(a)):bisect.bisect_left(pts,exact(b)),rater] = True
    return labels


def collect_manifest(p):
    """Read/check actual old metadata and media only; no decode or processor."""
    closure = {}; sources = []; names = []; all_cases = set()
    def keep(path, expected=None, size=None):
        ref = file_ref(path,expected,size)
        require(ref['path'] not in closure or closure[ref['path']] == ref, 'Conflicting file bindings')
        closure[ref['path']] = ref
        return ref
    def declared(ref): return keep(ref['path'],ref['sha256'],ref.get('bytes'))
    declared(p['prior_direction_result']); config_ref = declared(p['model_config'])
    require(Path(config_ref['path']).resolve() == (RUN/'b_score_aligned_package_v4/config.json').resolve(), 'Existing original-B config only')
    model_directory = Path(read(config_ref['path'])['model_dir'])
    processor_assets = [keep(path) for path in sorted(model_directory.iterdir()) if path.is_file() and path.suffix in ('.json','.txt','.jinja')]
    require(processor_assets, 'Existing frozen processor assets missing')
    for spec,expected in zip(p['cohorts'],COHORTS):
        cohort_name,count,window_count,accepted_sha,status = expected
        cpu_ref = declared(spec['cpu_completion']); require(cpu_ref['sha256'] == accepted_sha, 'Original accepted cohort bytes required; no reselection')
        cpu = read(cpu_ref['path']); require(cpu['status'] == status and cpu['sources'] == count and cpu['windows'] == window_count and len(cpu['accepted']) == count, 'Original accepted source/window denominator')
        gpu_ref = declared(spec['b0_completion']); gpu = read(gpu_ref['path'])
        export_ref = declared(spec['b0_export']); exported = read(export_ref['path'])
        replay_ref = declared(spec['replay_completion']); replay = read(replay_ref['path'])
        require(gpu['status'] == 'PASS_COMPLETE_ORIGINAL_B_EXTERNAL_NATIVE64_CALLS_NOT_QUALITY' and gpu['successful_windows'] == gpu['actual_model_calls'] == window_count and gpu['registered_sources'] == count and gpu['model_parameters'] == 8782459120, 'Actual old B0 successful terminal')
        require(exported['status'] == 'PASS_NEW_B_NATIVE_INFERENCE_AND_INDEPENDENT_CPU_REPLAY' and exported['successful_windows'] == exported['started_windows'] == window_count and exported['registered_sources'] == count and exported['model_parameters'] == 8782459120, 'Actual old B0 export')
        require(gpu['reference_labels_read'] is False and exported['reference_labels_read'] is False and
                gpu['new_optimizer_updates'] == exported['new_optimizer_updates'] == 0 and
                gpu['source_lock_sha256'] == exported['source_lock_sha256'] == replay['source_lock_sha256'], 'Original no-reference/no-update B0 frozen source-lock identity')
        require(replay['status'] == 'PASS_ALL_HUMAN_EXTERNAL_B_INDEPENDENT_CPU_REPLAYS' and replay['windows'] == window_count and replay['registered_sources'] == count and replay['gpu_completion_sha256'] == gpu_ref['sha256'] and exported['independent_replay_completion_sha256'] == replay_ref['sha256'], 'Actual old independent replay binding')
        entries = {e['case_id']:e for e in gpu['entries']}; rows = {r['source_name']:r for r in exported['rows']}
        require(len(entries) == len(gpu['entries']) == window_count and len(rows) == len(exported['rows']) == count, 'Old indexes contain duplicate/omitted source or case')
        used = set()
        for accepted in cpu['accepted']:
            name = accepted['video_id']; names.append(name); sid = 'V%02d'%len(sources)
            require(name == SOURCE_NAMES[len(sources)] and name in rows, 'Fixed accepted28 source order; never replace or reorder')
            reference = keep(accepted['reference_path'],accepted['reference_sha256'])
            keep(accepted['media_completion_path'],accepted['media_completion_sha256'])
            keep(accepted['cpu_completion_path'],accepted['cpu_completion_sha256'])
            # These legacy files may have extra fields. Their complete raw bytes
            # are bound, but no unknown media/cpu-completion schema is invented.
            proofs = accepted['proofs']; require(proofs, 'Original B0 windows required')
            old_windows = []; original_clock = normalized = media_ref = clock_ref = mapping_ref = None
            export_windows = {(w['start_exact'],w['end_exact']):w for w in rows[name]['windows']}
            require(len(export_windows) == len(rows[name]['windows']) == len(proofs), 'Original per-source window denominator')
            for proof_index,proof_entry in enumerate(proofs):
                case = proof_entry['case_id']; require(case not in used and case not in all_cases and case in entries, 'Original B0 case missing/duplicated')
                used.add(case); all_cases.add(case)
                input_ref = keep(proof_entry['input_path'],proof_entry['input_sha256']); meta = read(input_ref['path'])
                proof_ref = keep(proof_entry['proof_path'],proof_entry['proof_sha256']); proof = read(proof_ref['path'])
                require(meta['case_id'] == proof['case_id'] == case and meta['source_name'] == proof['source_name'] == name and proof['status'] == 'PASS_CPU_ORIGINAL_B_NATIVE64_PROCESSOR_INPUT' and proof['input_sha256'] == input_ref['sha256'] and proof['input_path'] == input_ref['path'], 'Actual original CPU window/input binding')
                require(meta['reference_available_to_inference'] is False and meta['audio_observed'] is False, 'Original B0 visual-only input excludes human reference')
                source_directory = Path(input_ref['path']).parent.parent
                current_mapping = keep(source_directory/'mapping.json',meta['bindings']['mapping_sha256']); mapping = read(current_mapping['path'])
                current_clock = keep(source_directory/'clock.json',mapping['clock_sha256']); clock = read(current_clock['path'])
                require(mapping['status'] == 'PASS_UNMODIFIED_REFERENCE_SECONDS_IN_NATIVE_DOMAIN' and mapping['video_id'] == name and mapping['author_1fps_grid_used_as_native_GT'] is False and mapping['reference_text_available_to_model'] is False, 'Original unmodified native mapping only')
                if original_clock is None:
                    original_clock = clock; normalized = normalize_clock(clock); clock_ref = current_clock; mapping_ref = current_mapping
                    media_ref = keep(meta['source_path'],meta['source_sha256'],meta['source_bytes'])
                    require(media_ref['sha256'] == clock['source_sha256'] and media_ref['bytes'] == clock['source_bytes'] and rows[name]['native_clock'] == clock, 'Original media/export/clock source identity')
                    reference_row(read(reference['path']),name,exact(clock['physical_end_exact']))
                require(current_clock == clock_ref and current_mapping == mapping_ref and meta['source_path'] == media_ref['path'] and meta['source_sha256'] == media_ref['sha256'] and meta['source_bytes'] == media_ref['bytes'] and meta['all_source_exact_pts'] == clock['original_exact_pts'] and meta['source_total_frames'] == clock['native_frames'] and exact(meta['original_clock_origin_exact']) == 0, 'Every old B0 window must reference exactly the same original native source')
                lo,hi = exact(meta['window_start']),exact(meta['window_end'])
                require(len(mapping['windows']) == len(proofs) and mapping['windows'][proof_index]['start_exact'] == str(lo) and mapping['windows'][proof_index]['end_exact'] == str(hi), 'Exact original window mapping/order')
                require((str(lo),str(hi)) in export_windows, 'Original export window endpoints missing')
                item = entries[case]; done_ref = keep(item['done_path'],item['done_sha256']); done = read(done_ref['path'])
                require(item['source_name'] == name and done['case_id'] == case and done['source_name'] == name and done['parse_errors'] == [] and done['new_optimizer_updates'] == 0 and done['input_evidence'] == proof['input_evidence'] and done['input_evidence']['source_sha256'] == media_ref['sha256'], 'Original successful B0 answer/evidence only')
                require(exact(done['source_start_exact']) == lo and exact(done['source_end_exact']) == hi, 'Original B0 exact source endpoints')
                require(done['status'] == ('MODEL_OK' if done['segments'] else 'LEGAL_EMPTY'), 'Engineering failure must never become baseline empty')
                raw_ref = keep(done['raw_path'],done['raw_sha256'])
                require(read(raw_ref['path'])['actual_model_call'] is True, 'Actual saved original model answer, never synthetic B0')
                request_ref = keep(Path(done_ref['path']).with_name('request.json'),done['request_sha256']); request = read(request_ref['path'])
                require(request['input_sha256'] == input_ref['sha256'] and request['CPU_proof_sha256'] == proof_ref['sha256'] and request['reference_labels_read'] is False and exact(request['source_start_exact']) == lo and exact(request['source_end_exact']) == hi, 'Old B0 request/CPU/reference exclusion')
                exported_window = export_windows[(str(lo),str(hi))]
                require(exported_window['segments'] == done['segments'] and exported_window['original_status'] == done['status'] and exported_window['original_raw_sha256'] == raw_ref['sha256'], 'Old B0 export differs from saved done answer')
                ranges,segments = native_ranges([exact(x) for x in clock['original_exact_pts']],lo,hi,done['segments'])
                require(ranges == done['native_ranges'], 'Independent exact original B0 native range replay')
                old_windows.append(dict(case_id=case,start_exact=str(lo),end_exact=str(hi),segments_exact=segments,native_ranges=ranges,old_done=done_ref,old_input=input_ref,old_CPU_proof=proof_ref,old_request=request_ref,old_raw=raw_ref))
            require(old_windows[0]['start_exact'] == '0' and exact(old_windows[-1]['end_exact']) == exact(normalized['physical_end_exact']) and all(a['end_exact'] == b['start_exact'] for a,b in zip(old_windows,old_windows[1:])), 'Original B0 windows must cover whole source without omitted windows')
            sources.append(dict(id=sid,name=name,cohort=cohort_name,historical_labels_exposed=True,
                                media=media_ref,reference=reference,clock=clock_ref,mapping=mapping_ref,
                                original_CPU_completion=keep(accepted['cpu_completion_path'],accepted['cpu_completion_sha256']),
                                normalized_clock=normalized,old_B0_windows=old_windows,
                                original_B0_export=export_ref,original_B0_completion=gpu_ref,reference_scope=REFERENCE_SCOPE))
        require(used == set(entries), 'Every old B0 successful index entry must be adopted exactly once')
    require(tuple(names) == SOURCE_NAMES and len(sources) == 28 and len(all_cases) == 131, 'Exact immutable28/131 source/window denominator')
    return dict(schema=SCHEMA,status='REGISTERED_EXISTING28_METADATA_ONLY_NOT_CPU_OR_GPU_ADMISSION',
                protocol_sha256=sha(ROOT/'protocol.json'),sources=sources,files=list(closure.values()),
                original_successful_B0_windows=131,processor_assets=processor_assets,reference_scope=REFERENCE_SCOPE,
                new_model_calls=0,new_decodes=0,new_image_processors=0)


def register():
    p = protocol(); manifest = collect_manifest(p)
    write(ROOT/'reference_manifest11.json',manifest)


def prepare():
    p = protocol()
    require(p['new_purpose_CPU_preparation_authorized'] is True and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'Explicit new-purpose CPU admission and child-only GPU masking required')
    manifest = read(ROOT/'reference_manifest11.json')
    require(manifest['protocol_sha256'] == sha(ROOT/'protocol.json') and manifest['status'] == 'REGISTERED_EXISTING28_METADATA_ONLY_NOT_CPU_OR_GPU_ADMISSION', 'Frozen existing28 manifest')
    # Rehash all files, including media. No old source is assumed to remain on
    # disk simply because a successful historic receipt exists.
    for ref in manifest['files']: bound(ref)
    require([s['name'] for s in manifest['sources']] == list(SOURCE_NAMES) and [s['id'] for s in manifest['sources']] == ['V%02d'%i for i in range(28)], 'Frozen source identities/order')
    import av
    import numpy as np
    import torch
    import shutil
    from transformers import AutoProcessor
    require(not torch.cuda.is_initialized(), 'No CUDA in new-purpose CPU preparation')
    torch.set_num_threads(2)
    processor = AutoProcessor.from_pretrained(read(p['model_config']['path'])['model_dir'],local_files_only=True)
    (ROOT/'labels').mkdir(exist_ok=False); accepted = []; label_receipts = []
    for source_index,source in enumerate(manifest['sources']):
        sid = source['id']; clock = source['normalized_clock']; pts = [exact(x) for x in clock['normalized_exact_pts']]
        needed = sum(p['CPU_tensor_estimates_by_source'][s['id']] for s in manifest['sources'][source_index:])+p['reserved_future_output_bytes']
        require(shutil.disk_usage(ROOT).free >= needed, 'Live disk cannot hold remaining declared CPU/future outputs; no automatic cleanup or source replacement')
        directory = ROOT/'inputs'/sid; directory.mkdir(parents=True,exist_ok=False)
        groups,ordinals = occupied_sampling(clock)
        baseline = np.zeros(len(pts),dtype=np.bool_)
        for window in source['old_B0_windows']:
            lo = exact(window['start_exact'])
            for a,b in window['segments_exact']:
                baseline[bisect.bisect_left(pts,lo+exact(a)):bisect.bisect_left(pts,lo+exact(b))] = True
        with (directory/'native.npz').open('xb') as handle:
            np.savez(handle,groups=groups,baseline=baseline,sample_ordinals=ordinals)
        write(directory/'clock.json',clock)
        reference = reference_row(read(source['reference']['path']),source['name'],exact(clock['physical_end_exact']))
        labels = native_reference_labels(clock,reference); label_path = ROOT/'labels'/(sid+'.npy')
        with label_path.open('xb') as handle: np.save(handle,labels)
        label_receipts.append(dict(id=sid,path=str(label_path),sha256=sha(label_path),shape=list(labels.shape),dtype='bool',
                                   reference_sha256=source['reference']['sha256'],clock_sha256=sha(directory/'clock.json'),
                                   mapping='Actual native PTS in original exact half-open human intervals; no 1fps label interpolation',scope=REFERENCE_SCOPE))
        desired = set(ordinals.tolist()); batch = []; batch_ids = []; chunks = []; observed = 0
        def flush():
            if not batch: return
            enc = processor.image_processor(images=batch,return_tensors='pt',size={'shortest_edge':65536,'longest_edge':65536})
            pixels = enc['pixel_values'].contiguous(); grid = enc['image_grid_thw'].contiguous()
            require(pixels.device.type == 'cpu' and bool(torch.isfinite(pixels).all()) and grid.shape == (len(batch),3) and bool((grid[:,0] == 1).all()), 'Actual first CPU image processor contract')
            path = directory/('chunk_%04d.pt'%len(chunks))
            with path.open('xb') as handle: torch.save(dict(pixel_values=pixels,image_grid_thw=grid,sample_ordinals=batch_ids.copy()),handle)
            chunks.append(dict(path=str(path),bytes=path.stat().st_size,sha256=sha(path),samples=batch_ids.copy(),pixel_shape=list(pixels.shape),grid=grid.tolist(),pixel_sha256=hashlib.sha256(pixels.numpy().tobytes()).hexdigest()))
            batch.clear(); batch_ids.clear()
        with av.open(source['media']['path']) as container:
            stream = container.streams.video[0]; stream.thread_count = 2
            require(stream.index == clock['video_stream_index'] and F(stream.time_base) == exact(clock['stream_time_base_exact']), 'Actual existing native stream identity')
            last_duration = None
            for i,frame in enumerate(container.decode(stream)):
                require(i < len(pts) and frame.pts is not None and frame.time_base is not None and
                        F(frame.pts)*F(frame.time_base) == pts[i], 'Full native decode differs from original zero-origin clock; never shift/stretch')
                require(frame.width == clock['width'] and frame.height == clock['height'], 'Original source geometry')
                duration = getattr(frame,'duration',None)
                last_duration = F(duration)*F(frame.time_base) if duration is not None else None
                observed += 1
                if i in desired:
                    batch.append(frame.to_image()); batch_ids.append(i)
                    if len(batch) == 8: flush()
            flush()
        require(observed == len(pts) and last_duration == exact(clock['last_frame_duration_exact']) and pts[-1]+last_duration == exact(clock['physical_end_exact']) and
                [i for c in chunks for i in c['samples']] == ordinals.tolist(), 'Actual complete native frames/final duration/ordered targets')
        receipt = dict(status='PASS_FIRST_NEW_IMAGE_CPU_INPUTS',id=sid,name=source['name'],role='external_historical_reference_conditional',
                       native_frames=observed,feature_cells=len(ordinals),native_sha256=sha(directory/'native.npz'),clock_sha256=sha(directory/'clock.json'),
                       chunks=chunks,new_generation_calls=0,new_feature_forwards=0,
                       old_B0_windows_adopted=len(source['old_B0_windows']),label_content_in_images_or_queries=False)
        write(directory/'acceptance.json',receipt); accepted.append(receipt)
        event('EXTENDED11_FIRST_NEW_PURPOSE_CPU_SOURCE_ACCEPTED',id=sid,name=source['name'],native_frames=observed,cells=len(ordinals))
    require(not torch.cuda.is_initialized() and len(accepted) == 28, 'Complete28 CPU-only preparation')
    write(ROOT/'label_acceptance11.json',dict(status='PASS_ORIGINAL10_REFERENCE_INTERVALS_NATIVE_PTS_MAPPING_ONLY',sources=label_receipts,scope=REFERENCE_SCOPE,
                                           labels_not_in_GPU_inputs=True,reference_manifest_sha256=sha(ROOT/'reference_manifest11.json')))
    write(ROOT/'cpu_acceptance.json',dict(status='PASS_ALL28_NEW_FEATURE_INPUTS',sources=accepted,protocol_sha256=sha(ROOT/'protocol.json'),
                                         reference_manifest_sha256=sha(ROOT/'reference_manifest11.json'),total_cells=sum(s['feature_cells'] for s in accepted),
                                         new_model_calls=0,new_optimizer_updates=0,source_selection_or_replacement=False,reference_labels_in_GPU_inputs=False))


if __name__ == '__main__':
    try: {'register':register,'prepare':prepare}[sys.argv[1]]()
    except BaseException as error:
        import traceback
        failure = ROOT/('extended11_%s_failure_%s.json'%(sys.argv[1] if len(sys.argv)>1 else 'arguments',os.getpid()))
        if not failure.exists(): write(failure,dict(error=repr(error),traceback=traceback.format_exc(),utc=utc(),new_model_calls=0))
        raise
