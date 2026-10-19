"""Real fresh-process imports of synthetic code only; no business modules."""
import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import star_import_bootstrap_v78 as boot


def fixture(root):
    p=Path(root);paths={}
    definitions=dict(
        pair_common=('pair/pair_common.py','VERIFIED=17\n'),
        geometry31=('crop/crop_geometry_v31.py','VERIFIED=31\n'),
        math55=('utility/explicit_math55.py','VERIFIED=55\n'),
        image31=('image/crop_image_input_v31.py','import crop_geometry_v31\nassert crop_geometry_v31.VERIFIED==31\nVERIFIED=31\n'),
        frozen55=('utility/utility_value_gpu_v55.py',"raise RuntimeError('FROZEN GPU MODULE MUST NOT EXECUTE')\n"))
    modules=[]
    for role,(relative,source) in definitions.items():
        path=p/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(source,encoding='utf-8')
        paths[role]=boot.reference(path);modules.append(dict(role=role,module_name=path.stem,reference=paths[role]))
    sources=dict(CPU68=dict(schema='UTILITY_CONNECTED_STAR_CPU_V68',helper_code=paths['pair_common'],geometry_code=paths['geometry31']),
        GPU69=dict(schema='UTILITY_CONNECTED_STAR_CONTINUATION_V69',image_code=paths['image31'],frozen_GPU55_code=paths['frozen55']),
        GPU55=dict(math_code=paths['math55'],GPU_code=paths['frozen55']))
    reg=dict(modules=modules)
    return reg,sources,paths


class BootstrapTests(unittest.TestCase):
    def test_fresh_process_imports_image_dependency_and_only_resolves_frozen_GPU(self):
        with tempfile.TemporaryDirectory() as directory:
            reg,sources,paths=fixture(directory);plan=boot.dependency_plan(reg,sources)
            self.assertEqual(len(plan['pythonpath']),3)
            self.assertNotIn(str(Path(paths['image31']['path']).parent),plan['pythonpath'])
            actual=boot.fresh_preflight(plan,cwd=directory)
            self.assertEqual(actual['status'],'PASS_FRESH_CPU_IMPORT_BINDINGS_ONLY_NOT_INPUT_QA')
            self.assertEqual([m['executed'] for m in actual['modules']],[True,True,True,True,False])
            self.assertFalse(actual['frozen_GPU_helper_executed']);self.assertEqual(actual['CUDA_VISIBLE_DEVICES'],'')
            self.assertEqual(actual['pixel_tensor_target_reads'],0)

    def test_missing_dependency_and_wrong_same_name_are_reproduced_in_fresh_process(self):
        with tempfile.TemporaryDirectory() as directory:
            reg,sources,paths=fixture(directory);plan=boot.dependency_plan(reg,sources)
            missing=copy.deepcopy(plan);missing['pythonpath'].remove(str(Path(paths['geometry31']['path']).parent))
            with self.assertRaises(ValueError):boot.fresh_preflight(missing,cwd=directory)
            shadow=Path(paths['math55']['path']).parent/'crop_geometry_v31.py';shadow.write_text('VERIFIED=-1\n',encoding='utf-8')
            with self.assertRaises(ValueError):boot.fresh_preflight(plan,cwd=directory)

    def test_inherited_pythonpath_is_replaced_and_no_unbound_directory_is_added(self):
        with tempfile.TemporaryDirectory() as directory:
            reg,sources,paths=fixture(directory);plan=boot.dependency_plan(reg,sources)
            unbound=Path(directory)/'unbound';unbound.mkdir();(unbound/'crop_geometry_v31.py').write_text('VERIFIED=-100\n',encoding='utf-8')
            with mock.patch.dict(os.environ,dict(PYTHONPATH=str(unbound),CUDA_VISIBLE_DEVICES='9')):
                actual=boot.fresh_preflight(plan,cwd=directory)
                self.assertNotIn(str(unbound),actual['pythonpath'])
                self.assertEqual(os.environ['PYTHONPATH'],str(unbound))
                self.assertEqual(boot.child_environment(plan,stage=True)['CUDA_VISIBLE_DEVICES'],'0')

    def test_exact_source_field_name_and_minimal_roles_are_required(self):
        with tempfile.TemporaryDirectory() as directory:
            reg,sources,_=fixture(directory)
            for mode in ('name','source','extra'):
                bad=copy.deepcopy(reg)
                if mode=='name':bad['modules'][2]['module_name']='guessed_math_name'
                elif mode=='source':bad['modules'][0]['reference']=bad['modules'][1]['reference']
                else:bad['modules'].append(dict(role='arbitrary_runtime',module_name='runtime',reference=bad['modules'][0]['reference']))
                with self.subTest(mode=mode),self.assertRaises(ValueError):boot.dependency_plan(bad,sources)

    def test_preflight_blocks_tensor_or_media_read_at_import(self):
        with tempfile.TemporaryDirectory() as directory:
            reg,sources,paths=fixture(directory)
            image=Path(paths['image31']['path']);image.write_text("open('forbidden_tensor.npy','rb')\n",encoding='utf-8')
            changed=boot.reference(image);sources['GPU69']['image_code']=changed
            next(m for m in reg['modules'] if m['role']=='image31')['reference']=changed
            with self.assertRaises(ValueError):boot.fresh_preflight(boot.dependency_plan(reg,sources),cwd=directory)

    def test_one_existing_scientific_admission_is_forwarded_without_modification(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);reg=dict(stage73_code=dict(path=str(root/'73.py'),sha256='a'*64),
                production74_code=dict(path=str(root/'74.py'),sha256='b'*64),deployment_receipt=dict(path=str(root/'72.json'),sha256='c'*64))
            for stage in ('GPU_resized20','CPU_remaining'):
                production=stage in boot.PRODUCTION;selected=reg['production74_code' if production else 'stage73_code']
                path=root/(stage+'.json');data=dict(stage=stage,launch_approved=True,deadline_utc=boot.DEADLINE,
                    register_code=selected,deployment_receipt=reg['deployment_receipt'])
                if production:data['stage73_code']=reg['stage73_code']
                boot.save(path,data);original=path.read_bytes()
                with mock.patch.object(boot,'bound',side_effect=lambda r:Path(r['path'])):
                    argv=boot.stage_command(root,stage,path,reg)
                    self.assertEqual(argv.count('--stage'),1);self.assertEqual(argv[argv.index('--stage')+1],stage)
                    self.assertEqual(path.read_bytes(),original)
                    bad=dict(reg,stage73_code=dict(path='wrong',sha256='d'*64))
                    with self.assertRaises(ValueError):boot.stage_command(root,stage,path,bad)


if __name__=='__main__':unittest.main()
