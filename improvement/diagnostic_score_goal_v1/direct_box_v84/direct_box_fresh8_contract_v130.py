"""Conditional fresh8 metadata/range/controller draft. No IO on import.

No downloader, processor, model, target reader or launcher is implemented here.
build_stage_plan returns one explicit command for separately registered new130
workers; it never executes it. Only actual128 development qualification can
justify registering those workers. See DIRECT_BOX_FRESH8_CONTRACT_V130.md.
"""
import copy
import hashlib
import json
from pathlib import PurePosixPath as Path
import struct
import zlib

SCHEMA='GNMC_FRESH8_FILE_CONFIRMATION_V130'
DEVELOPMENT_PASS='PASS_DIRECT_BOX128_NATIVE20_AND_HISTORICAL19_RELATIVE_CRITIC'
SALT='DIRECT_BOX_TRUST_REGION_GNMC_FRESH8_V125|test|'
ARCHIVE_BYTES=363946070
ORIGIN='https://zenodo.org/api/records/6228834/files/GNMC.zip/content'
EXPECTED_PAYLOAD=304262
PIPELINE=8790372845
CRITIC_PARAMETERS=135393
MEMBER_REFS={
    'test.json':dict(bytes=511519,sha256='ab44dd9de153b659fe14a07aaadd19709ff6be54619aa1886cd4684d2296b21e'),
    'zip_index.json':dict(bytes=479892,sha256='9e846cd08a3d1beade268cecc855fd00e9632f2ba8cc78f7f731891828376193'),
    'protected.json':dict(bytes=819,sha256='d6c5bd580ce1b4ae68067fb8156f7537082ddf1ee5a46eb1de73aede6e713b15')}
_ROWS=(
    ('003611',10405606,18196,18444,198173229),('006775',71541835,39743,39879,3005230874),
    ('007178',51679551,36541,36688,755554514),('004826',47838932,65177,65313,681444888),
    ('008212',55944118,27677,28342,1952776703),('002915',9873388,32243,32379,4089792296),
    ('004447',49117522,40265,40401,1291438781),('007891',7168802,44180,44333,4106580368))
EXTRA_CRC_SIZE_EXCLUSIONS=('000725','000988','001504','002733','002832','004415','004455','005661','006155','007377','007501','007826','009556')


def require(value,message):
    if not value:raise ValueError(message)


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def fixed_sources():
    return [dict(source_id='gnmc:test:'+name+'.jpeg',filename=name+'.jpeg',member='GNMC/test/'+name+'.jpeg',
        header_offset=offset,compressed_bytes=packed,bytes=raw,crc32=crc,compression=8) for name,offset,packed,raw,crc in _ROWS]


def validate_sources(rows):
    require(rows==fixed_sources(),'Exactly frozen8 files/order/range metadata; no score/identity replacement after admission')
    require(sum(r['compressed_bytes']+30 for r in rows)==EXPECTED_PAYLOAD,'Exact header-plus-packed payload')
    return digest(rows)


def range_response(status,content_range,body,*,offset,length,archive_bytes=ARCHIVE_BYTES):
    require(type(offset)==type(length)==int and offset>=0 and length>0 and offset+length<=archive_bytes,'Bounded single registered range')
    require(status==206 and content_range==f'bytes {offset}-{offset+length-1}/{archive_bytes}'
        and isinstance(body,bytes) and len(body)==length,'Strict206/Content-Range/exact bytes; no full-archive fallback')
    return body


def member_data_offset(header,row):
    require(isinstance(header,bytes) and len(header)==30,'Only actual30-byte local ZIP header')
    h=struct.unpack('<4s5H3I2H',header)
    require(h[0]==b'PK\x03\x04' and h[3]==row['compression']==8 and not h[2]&1
        and h[6] in (0,row['crc32']) and h[7] in (0,row['compressed_bytes']) and h[8] in (0,row['bytes']),
        'Unencrypted original local header/method/metadata')
    offset=row['header_offset']+30+h[9]+h[10]
    require(offset+row['compressed_bytes']<=ARCHIVE_BYTES,'Member cannot escape registered archive')
    return offset


def unpack_member(packed,row):
    """Bounded raw-DEFLATE+CRC only, no JPEG decode or image inspection."""
    require(isinstance(packed,bytes) and len(packed)==row['compressed_bytes'] and row['compression']==8,'Exact original compressed member')
    decoder=zlib.decompressobj(-15);raw=decoder.decompress(packed,row['bytes']+1)
    require(decoder.eof and not decoder.unconsumed_tail and not decoder.unused_data
        and len(raw)==row['bytes'] and zlib.crc32(raw)&0xffffffff==row['crc32'],'Original uncompressed size/CRC; no repair/fallback')
    return raw


def check_identity(source_id,media_sha256,rgb_sha256,dhash,registry):
    """Explicit previously known identities only; global independence UNKNOWN."""
    require(source_id in {r['source_id'] for r in fixed_sources()} and type(dhash)==int and 0<=dhash<2**64,'Fixed new8 owner/dHash')
    require(len(media_sha256)==len(rgb_sha256)==64,'Actual new source/RGB hashes required')
    require(source_id not in registry['blocked_source_ids'] and media_sha256 not in registry['blocked_media_sha256']
        and rgb_sha256 not in registry['blocked_RGB_sha256']
        and all((dhash-int(old)).bit_count()>6 for old in registry['blocked_dhash9x8']),
        'Known/exact/near duplicate rejected; fail fixed8 scope rather than replace by score')
    return dict(known_identity_checks_passed=True,original_source_global_independence='UNKNOWN',pretraining_overlap='UNKNOWN')


def validate_development(admission,result,*,result_ref,model_refs,critic_refs):
    """Minimal independent handoff, not a relabelled39 confirmation."""
    require(result['status']==DEVELOPMENT_PASS and result['admitted_arms']==['JOINT'], 'Only actual128 frozen39 development PASS')
    require(admission['schema']=='ADMIT_FRESH8_AFTER_ACTUAL128_DEV39_V130' and admission['result']==result_ref
        and admission['development_only'] is True and admission['fresh8_admitted'] is True
        and admission['no_new_fit_on_fresh8'] is True and admission['file_level_only'] is True
        and admission['model_refs']==model_refs and admission['critic_refs']==critic_refs,
        'Actual frozen model/critic refs and new-purpose admission; old19 STOP is not confirmation')


def build_stage_plan(reg,stage,*,registration_path):
    """Pure one-stage controller draft. Workers must be new, exact and registered.

    Returned arguments are data; the caller must verify actual SHA-bound files,
    host/shared resources and prior gates before launching. No subprocess here.
    """
    require(reg['schema']==SCHEMA and stage in ('cpu','gpu','review'),'Independent new130 scope/stage')
    require(reg['origin_url']==ORIGIN and reg['archive_bytes']==ARCHIVE_BYTES and reg['max_range_payload_bytes']==EXPECTED_PAYLOAD
        and reg['source_plan_sha256']==validate_sources(reg['sources']),'Frozen original source/range plan')
    root=Path(reg['root']);rp=Path(registration_path)
    require(root.is_absolute() and rp==root/'fresh8_registration_130.json','Independent exact fresh8 root/registration')
    code=reg['worker_codes'][stage];expected='direct_box_fresh8_runtime_v130.py'
    require(Path(code['path']).is_absolute() and Path(code['path']).name==expected and len(code['sha256'])==64,
        'Only a separately implemented/registered new130 worker; no old40 launcher')
    require(reg['pipeline_parameters']==PIPELINE and reg['critic_parameters']==CRITIC_PARAMETERS
        and reg['new_8B_training_updates']==reg['new_critic_fits']==0,'All actual critic/PCA/RMS state counted; no fresh8 fitting')
    base=[reg['python'],'-B','-u',code['path'],'--stage',stage,'--root',str(root),'--registration',str(rp)]
    result=dict(stage=stage,argv=base,CUDA_VISIBLE_DEVICES='' if stage!='gpu' else '0',registration=str(rp),
        automatic_next_stage=False,shared_GPU_wrapper_required=stage=='gpu',implementation='COMMAND_PLAN_ONLY_NOT_LAUNCHED')
    if stage=='cpu':
        require(reg['CPU_max_seconds']>0 and reg['CPU_max_new_bytes']>0,'Explicit source/input budget')
        result.update(required_prior='ACTUAL128_DEV39_PASS_AND_EXPLICIT_NEW_FRESH8_ADMISSION',
            success_status='PASS_FRESH8_ALL8_B0_AND_DIRECT_INPUTS_FIRST_CPU_QA_V130',expected_sources=8,
            GT_read=False,new_JPEG_decodes=8,expected_new_image_encodings=16)
    elif stage=='gpu':
        require(reg['GPU_max_seconds']>0 and reg['GPU_job'] and reg['GPU_planned_output_bytes']>0,'Explicit measured shared GPU budget')
        result.update(required_prior='PASS_FRESH8_ALL8_B0_AND_DIRECT_INPUTS_FIRST_CPU_QA_V130',
            success_status='COMPLETE_FRESH8_BASE8_DIRECT8_RAW_NOT_QUALITY_V130',expected_sources=8,
            BASE_generations=8,DIRECT_hidden_head_forwards=8,BASE_max_pixels=131072,DIRECT_max_pixels=65536,
            BASE_generation=dict(max_new_tokens=128,do_sample=False,num_beams=1,use_cache=True),GT_read=False,
            model_roles=['ORIGINAL_BARE_BASE_131072_GREEDY128','FROZEN105_SOURCE_ONLY_L2_HEAD3'])
    else:
        result.update(required_prior='COMPLETE_FRESH8_BASE8_DIRECT8_RAW_NOT_QUALITY_V130',
            raw_QA_before_GT=True,success_raw_status='PASS_FRESH8_BASE_AND105_RAW_FIRST_CPU_QA_V130',
            CPU_controls=['EXACT_B0_ALWAYS_REJECT','FROZEN128_GEOM11','ALWAYS_ACCEPT_FIXED124'],
            fresh8_quality_must_be_preregistered=True,new_fit=0,automatic_production=False)
    return result
