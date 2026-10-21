"""One fixed center-position ablation of the immutable40.47 submission.

No selection, scale, ratio, parameter, model or source-frame changes. This is
an authorized unknown-effect complete-method control, not a quality guarantee.
"""
import argparse,copy,gzip,hashlib,io,json,math,os,shutil,sys,time,traceback,zipfile
from fractions import Fraction
from pathlib import Path

BASE_SHA='b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'
PARAMS=8782557449
POLICY='DETERMINISTIC_IMAGE_CENTER_RETAIN_EACH_ORIGINAL_WIDTH'


def sha(b):return hashlib.sha256(b).hexdigest()
def ref(p):
    p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=sha(b))
def save(p,v):
    with Path(p).open('x',encoding='utf-8')as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False)
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def lines(b):return [json.loads(x)for x in b.splitlines()if x.strip()]
def jsonl(rows):return b''.join((json.dumps(z,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n').encode()for z in rows)
def canonical(rows):
    """Legacy digest: retained solely for comparison with old recorded hashes."""
    values=[{k:r[k]for k in ['video_id','targetRatioWH','predictions']}for r in sorted(rows,key=lambda v:v['video_id'])]
    return sha(json.dumps(values,sort_keys=True,separators=(',',':'),allow_nan=False).encode())


def semantic_digest(rows):
    """Actual complete predictions, independent of order/ignored extra keys."""
    def number(value):
        assert type(value)in (int,float)and math.isfinite(value)
        value=float(value)
        return (0. if value==0 else value).hex()
    values={}
    for row in rows:
        sid=str(row['video_id']);assert sid not in values
        ratio=row['targetRatioWH'];assert len(ratio)==2
        reduced=Fraction(ratio[0])/Fraction(ratio[1]);assert reduced>0
        points={}
        for item in row['predictions']:
            k=item['frame'];assert type(k)is int and k>=0 and k not in points
            assert len(item['bboxes'])==3
            points[k]=[number(x)for x in item['bboxes']]
        values[sid]=dict(ratio=str(reduced),predictions=[[k,points[k]]for k in sorted(points)])
    assert set(values)=={str(i)for i in range(426)},'Semanticrecheckrequirescomplete426uniqueids'
    return sha(json.dumps(dict(schema='AIC_ACTUAL_PREDICTION_SEMANTICS_V1',sources=[[k,values[k]]for k in sorted(values,key=int)]),separators=(',',':')).encode())


def metadata_index(meta):
    result={}
    for value in meta['records']:
        row=dict(value);ratio=row['targetRatioWH']
        row['targetRatioWH']=[int(x)for x in (ratio if isinstance(ratio,list)else ratio.split())]
        assert len(row['targetRatioWH'])==2 and min(row['targetRatioWH'])>0
        sid=str(row['video_id']);assert sid not in result;result[sid]=row
    return result


def center_box(old,width,height,ratio):
    assert len(old)==3 and all(type(v)is int for v in old)
    cw=old[2];tw,th=ratio
    assert 0<cw<=width and cw*th<=height*tw
    room=Fraction(height)-Fraction(cw*th,tw)
    ymax=room.numerator//room.denominator
    return [round(Fraction(width-cw,2)),round(min(room/2,Fraction(ymax))),cw]


def independent_center(width,height,cw,tw,th):
    """Separate integer quotient/remainder formula, without generator Fraction."""
    def nearest_even(num,den):
        q,r=divmod(num,den)
        return q+int(2*r>den or(2*r==den and q%2==1))
    room_num=height*tw-cw*th
    assert room_num>=0 and 0<cw<=width
    ymax=room_num//tw
    return [nearest_even(width-cw,2),nearest_even(min(room_num,2*ymax*tw),2*tw),cw]


def context(root):
    n=Path(root).resolve(strict=True);w=n.parent.parent;r=load(n/'registration46.json')
    assert r['code_ref']==ref(__file__)
    def bound(rr):
        p=Path(rr['path']).resolve(strict=True);assert p.is_relative_to(w)
        actual=ref(p);assert actual['sha256']==rr['sha256']
        if 'bytes'in rr:assert actual['bytes']==rr['bytes']
        return p
    for rr in r['bindings']:bound(rr)
    baseline=bound(r['baseline_ref']);assert baseline.stat().st_size==384630 and ref(baseline)['sha256']==BASE_SHA
    assert load(bound(r['official_rule_check_ref']))['automatic_center_ablation_admitted']is True
    return n,w,r,bound


def historical_registry(w,initial_ref,bound):
    prior=load(bound(initial_ref));hist=dict(legacy={q['canonical_SHA256']for q in prior},semantic=set())
    references=[];skipped=[]
    # Only submission-named archives. Never scan/download old media archives.
    for p in sorted(w.rglob('candidate_*.zip')):
        if 'center_ablation46'in str(p):continue
        try:
            with zipfile.ZipFile(p)as z:
                if z.namelist()!=['predictions.jsonl']:continue
                rows=lines(z.read('predictions.jsonl'))
            digest=canonical(rows);hist['legacy'].add(digest)
            try:actual=semantic_digest(rows)
            except(AssertionError,KeyError,TypeError,ValueError):actual=None
            if actual is not None:hist['semantic'].add(actual)
            references.append(dict(path=str(p),zip_bytes=p.stat().st_size,legacy_canonical_sha256=digest,semantic_v1_sha256=actual))
        except(zipfile.BadZipFile,KeyError,ValueError,TypeError)as error:
            skipped.append(dict(path=str(p),reason=type(error).__name__))
    return hist,dict(initial_history_ref=initial_ref,valid_archive_refs=references,nonconforming_archives=skipped,
                     legacy_canonical_count=len(hist['legacy']),semantic_v1_count=len(hist['semantic']),
                     legacy_hash_only_records_adopted_not_semantically_reverified=True,media_archives_read=False)


def package(root):
    n,w,r,bound=context(root);started=time.monotonic()
    assert os.environ.get('CUDA_VISIBLE_DEVICES')==''and not(n/'package_started46.json').exists()
    save(n/'package_started46.json',dict(policy=POLICY,single_use=True,new_models=0,new_training=0))
    with zipfile.ZipFile(bound(r['baseline_ref']))as z:
        assert z.namelist()==['predictions.jsonl'];base=lines(z.read('predictions.jsonl'))
    inputs=load(bound(r['package_inputs_ref']));meta=load(bound(inputs['metadata']))
    manifest=load(bound(inputs['source_manifest']));clocks=load(bound(inputs['source_clocks']))
    index=metadata_index(meta);sources={str(z['video_id']):z for z in manifest['records']}
    assert len(base)==len(index)==len(sources)==len(clocks)==426
    rows=copy.deepcopy(base);selected=[];provenance=[];changed_frames=0;changed_sources=set()
    for row,oldrow in zip(rows,base):
        sid=str(row['video_id']);m=index[sid];source=sources[sid];clock=clocks[sid]
        assert row['targetRatioWH']==m['targetRatioWH']and m['source_sha256']==source['source_sha256']==clock['source_sha256']
        assert m['n_frames']==clock['n_frames']and clock['measured_geometry']==[m['width'],m['height']]
        assert round(row['model_params_b']*1e9)==PARAMS
        assert row['predictions'],'Protected40.47 contains complete nonempty selection'
        for item,original in zip(row['predictions'],oldrow['predictions']):
            frame=item['frame'];assert type(frame)is int and 0<=frame<clock['n_frames']
            original_pts=Fraction(clock['original_exact_pts'][frame]);normalized=Fraction(clock['normalized_exact_pts'][frame])
            assert original_pts-Fraction(clock['first_original_pts_exact'])==normalized
            assert Fraction(clock['native_duration_by_ordinal'][str(frame)])>0
            assert normalized+Fraction(clock['native_duration_by_ordinal'][str(frame)])<=Fraction(clock['physical_end_exact'])
            new=center_box(original['bboxes'],m['width'],m['height'],row['targetRatioWH'])
            item['bboxes']=new
            if new!=original['bboxes']:changed_frames+=1;changed_sources.add(sid)
            selected.append(dict(video_id=sid,source_frame=frame))
            provenance.append(dict(video_id=sid,source_frame=frame,box_xyw=new,spatial_source=POLICY,legal=True,
                original_box_xyw=original['bboxes'],source_sha256=m['source_sha256'],original_pts_exact=str(original_pts),
                normalized_pts_exact=str(normalized),position_only=True))
    assert len(selected)==123506
    assert changed_frames>=1000 and len(changed_sources)>=10,'Insufficientinformation; no alternatecenter scan'
    history,registry=historical_registry(w,inputs['history'],bound)
    olddigest=canonical(base);history['legacy'].add(olddigest);newdigest=canonical(rows);actual_digest=semantic_digest(rows)
    assert newdigest not in history['legacy']and actual_digest not in history['semantic'],'Historicalduplicate; do not rename'
    pred=jsonl(rows);sel=gzip.compress(jsonl(selected),compresslevel=6,mtime=0);prov=gzip.compress(jsonl(provenance),compresslevel=6,mtime=0)
    archive=io.BytesIO()
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED)as z:z.writestr('predictions.jsonl',pred)
    payloads={'predictions.jsonl':pred,'selected46.jsonl.gz':sel,'provenance46.jsonl.gz':prov,'candidate_CENTER_POSITION_ABLATION_40_47.zip':archive.getvalue()}
    needed=sum(len(v)for v in payloads.values())
    already=sum(p.stat().st_size for p in n.rglob('*')if p.is_file())
    assert already+needed+350000<r['maximum_new_persistent_bytes']and shutil.disk_usage(n).free>needed+350000,'Actualnewbuffers andsmallvalidationreceipt cannot fit; preserveall'
    save(n/'historical_registry46.json',registry)
    save(n/'render46.json',dict(policy=POLICY,records=426,frames=len(selected),changed_frames=changed_frames,changed_sources=len(changed_sources),baseline_canonical_sha256=olddigest,canonical_sha256=newdigest,semantic_v1_sha256=actual_digest,all_temporal_and_widths_retained=True,parameters=PARAMS,original_baseline_ref=r['baseline_ref'],payload_bytes=needed,new_models=0,new_training=0,official_score='UNKNOWN',seconds=time.monotonic()-started))
    for name,data in payloads.items():
        with(n/name).open('xb')as f:f.write(data);f.flush();os.fsync(f.fileno())
    save(n/'package_payloads46.json',dict(payload_refs={name:ref(n/name)for name in payloads},render_ref=ref(n/'render46.json')))


def validate(root):
    n,w,r,bound=context(root);p=load(n/'package_payloads46.json')
    for rr in p['payload_refs'].values():bound(rr)
    sys.path.insert(0,str(bound(r['strict_loader_ref']).parent.parent))
    from aic6.scoring import load_predictions
    inputs=load(bound(r['package_inputs_ref']));meta=load(bound(inputs['metadata']));index=metadata_index(meta)
    clocks=load(bound(inputs['source_clocks']))
    with zipfile.ZipFile(bound(r['baseline_ref']))as z:base=lines(z.read('predictions.jsonl'))
    rows=lines((n/'predictions.jsonl').read_bytes());selected=lines(gzip.decompress((n/'selected46.jsonl.gz').read_bytes()));prov=lines(gzip.decompress((n/'provenance46.jsonl.gz').read_bytes()))
    expected={(str(row['video_id']),v['frame'])for row in base for v in row['predictions']}
    actual={(str(row['video_id']),v['frame'])for row in rows for v in row['predictions']}
    loaded=load_predictions(n/'predictions.jsonl',index)
    frozenkeys={(sid,k)for sid,frames in loaded.rows.items()for k in frames}
    bm={str(row['video_id']):row for row in base};pm={(str(v['video_id']),v['source_frame']):v for v in prov}
    geometry=True;identity=True;temporal=True;pts=True;changed=0;changed_sources=set()
    for row in rows:
        sid=str(row['video_id']);old=bm[sid];m=index[sid];clock=clocks[sid]
        temporal &= {k:v for k,v in row.items()if k!='predictions'}=={k:v for k,v in old.items()if k!='predictions'}
        temporal &= len(row['predictions'])==len(old['predictions'])
        for item,original in zip(row['predictions'],old['predictions']):
            key=(sid,item['frame']);proof=pm[key];cw=original['bboxes'][2];tw,th=row['targetRatioWH']
            temporal &= {k:v for k,v in item.items()if k!='bboxes'}=={k:v for k,v in original.items()if k!='bboxes'}
            temporal &= item['bboxes'][2]==cw
            geometry &= item['bboxes']==independent_center(m['width'],m['height'],cw,tw,th)
            identity &= proof['spatial_source']==POLICY and proof['box_xyw']==item['bboxes']and proof['original_box_xyw']==original['bboxes']and proof['position_only']is True and proof['legal']is True
            identity &= proof['source_sha256']==m['source_sha256']==clock['source_sha256']
            k=item['frame'];pts &= Fraction(proof['original_pts_exact'])==Fraction(clock['original_exact_pts'][k])and Fraction(proof['normalized_pts_exact'])==Fraction(clock['normalized_exact_pts'][k])
            if item['bboxes']!=original['bboxes']:changed+=1;changed_sources.add(sid)
    registry=load(n/'historical_registry46.json');hist={v['legacy_canonical_sha256']for v in registry['valid_archive_refs']}
    semantic_hist={v['semantic_v1_sha256']for v in registry['valid_archive_refs']if v['semantic_v1_sha256']is not None}
    hist.update(v['canonical_SHA256']for v in load(bound(inputs['history'])));hist.add(canonical(base))
    path=n/'candidate_CENTER_POSITION_ABLATION_40_47.zip'
    with zipfile.ZipFile(path)as z:names=z.namelist();crc=z.testzip();archived=z.read('predictions.jsonl')
    checks=dict(frozen_strict_loader_ok=loaded.ok and not loaded.validation['issues']and frozenkeys==expected,
        record_set_426_exact=len(rows)==426 and len({str(z['video_id'])for z in rows})==426 and set(bm)=={str(z['video_id'])for z in rows},
        all_temporal_fields_and_per_frame_widths_exact=bool(temporal),
        selected_sets_exact_no_empty_no_duplicate=actual==expected=={(str(v['video_id']),v['source_frame'])for v in selected}and len(selected)==len(expected)==123506 and all(v['predictions']for v in rows),
        independent_center_geometry_exact=bool(geometry),
        ratios_and_actual_total_parameters_exact=all(z['targetRatioWH']==index[str(z['video_id'])]['targetRatioWH']and round(z['model_params_b']*1e9)==PARAMS<=9000000000 for z in rows),
        bound_source_identity_and_original_native_PTS=bool(pts and identity),
        honest_center_provenance_complete=set(pm)==expected and len(prov)==len(pm),
        meaningful_and_historically_new_prediction=changed>=1000 and len(changed_sources)>=10 and canonical(rows)not in hist and semantic_digest(rows)not in semantic_hist,
        single_JSONL_and_CRC=names==['predictions.jsonl']and crc is None,
        ZIP_member_and_protected_baseline_bytes=sha(archived)==ref(n/'predictions.jsonl')['sha256']and ref(r['baseline_ref']['path'])==r['baseline_ref'])
    assert len(checks)==11
    report=dict(status='PASS_CENTER_SPECIFIC_INDEPENDENT_11_AND_UNCHANGED_FROZEN_LOADER'if all(checks.values())else'FAIL_CENTER_SPECIFIC_INDEPENDENT_11',checks=checks,strict_loader_ref=r['strict_loader_ref'],strict_loader_issues=loaded.validation['issues'],
        note='Old11validator permittedonlyQwenanchor/interpolation sourcekinds. Thisnewpolicy-specificvalidator honestlyallows deterministiccenter and independentlyrecalculatesit; oldvalidator/evidenceunchanged.',new_model_calls=0,new_training=0)
    save(n/'independent_validation46.json',report);assert all(checks.values()),checks
    save(n/'completion46.json',dict(status='PASS_ENGINEERING_CENTER_ABLATION_OFFICIAL_SCORE_UNKNOWN',zip_ref=ref(path),member_sha256=sha(archived),canonical_sha256=canonical(rows),semantic_v1_sha256=semantic_digest(rows),records=426,frames=len(expected),changed_frames=changed,changed_sources=len(changed_sources),temporal_selection_unchanged=True,per_frame_widths_unchanged=True,actual_pipeline_parameters=PARAMS,independent11_ref=ref(n/'independent_validation46.json'),baseline_ref=r['baseline_ref'],new_models=0,new_training=0,official_submissions=0,official_score='UNKNOWN'))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-root',required=True);p.add_argument('--phase',choices=['package','validate'],required=True);args=p.parse_args()
    try:globals()[args.phase](args.run_root)
    except BaseException:
        save(Path(args.run_root)/('failure_'+args.phase+'46.json'),dict(status='ACTUAL_FAILURE_PRESERVE_ALL_NO_AUTOMATIC_REPLAY',traceback=traceback.format_exc()));raise
