"""Read two original dog-label schemas, bound to the existing author Git blobs."""
import hashlib
import math
import traceback

from t_io import ROOT, WORK, fetch, identity, read, save


def git_blob(path):
    data = path.read_bytes()
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def main():
    output = ROOT / 'author_schema08'
    output.mkdir()
    inventory = WORK / 'i3d_umt_cross_domain_20261021_v1/source_inventory01.json'
    original = read(inventory)
    rows = sorted([r for r in original['sources'] if r['domain'] == 'dog'],
                  key=lambda r: hashlib.sha256(('T-schema-only/' + r['source_id']).encode()).hexdigest())[:2]
    save(output / 'registration.json', dict(
        inventory=identity(inventory), commit=original['commit'], selected=rows,
        scope='Two original annotation/clip schemas only, no media or quality metrics',
        subsequent_role='Schema-exposed, cannot be described as untouched confirmation',
        zero_votes_not_explicit_ordinary=True, no_implicit_training_admission=True))
    accepted, failures = [], []
    for row in rows:
        try:
            refs = {}
            for key in ['human_label_ref', 'clip_ref']:
                ref = row[key]
                path = output / (row['source_id'] + '_' + key + '.json')
                fetch('https://raw.githubusercontent.com/aliensunmin/DomainSpecificHighlight/'
                      + original['commit'] + '/' + ref['path'], path, ref['bytes'])
                if git_blob(path) != ref['git_blob']:
                    raise ValueError('Original annotation blob differs from pinned author tree')
                refs[key] = identity(path)
            labels = read(refs['human_label_ref']['path'])
            clips = read(refs['clip_ref']['path'])
            if len(labels) != 2 or labels[0] != clips or len(labels[1]) != len(clips):
                raise ValueError('Author soft-vote coordinates do not match original clip rows')
            if any(len(c) != 2 or not 0 <= c[0] < c[1] for c in clips):
                raise ValueError('Invalid original clip boundary')
            if any(not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0 for v in labels[1]):
                raise ValueError('Invalid original crowd soft vote')
            accepted.append(dict(source=row['source_id'], refs=refs, clips=len(clips),
                                 fractional_votes=sum(v != int(v) for v in labels[1]),
                                 zero_votes=sum(v == 0 for v in labels[1]),
                                 votes_are_not_clip_indices=True, no_binary_conversion=True,
                                 native_media_not_yet_admitted=True))
        except Exception:
            failures.append(dict(source=row['source_id'], traceback=traceback.format_exc()))
    save(output / 'completion.json', dict(
        state='ORIGINAL_AUTHOR_SCHEMA_AUDIT_COMPLETE', accepted=accepted, failures=failures,
        annotator_count='UNKNOWN_FROM_THIS_FILE', zero_votes_not_generic_ordinary=True,
        no_new_model_calls=True))
    print('T_AUTHOR_SCHEMA08_COMPLETE', len(accepted), len(failures), flush=True)


if __name__ == '__main__':
    main()
