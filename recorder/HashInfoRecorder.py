import util
from recorder.Recorder import Recorder
from typeId import ClassIDType, inverse_map
import inspect


BLACKLIST = ['m_FileID', 'm_PathID', 'm_Components', 'm_Children', 'm_PropertiesHash', 'm_ExposedReferences']
REJECTED_KEYWORDS = ["buffer", "constant"]
MAX_DEPTH = 9



class HashInfoRecorder(Recorder):
    """
    只记录属性的hash,GameObject的运行时动态记录.整个过程保存一次
    """

    def __init__(self):
        super().__init__()
        self.nameless_map = {}
        self.batch_data['material_'] = {}

    def notify_single(self, node):
        if node.type in [ClassIDType.MonoScript, ClassIDType.Shader, ClassIDType.ComputeShader, ClassIDType.ShaderImporter, ClassIDType.ComputeShaderImporter, ClassIDType.RayTracingShader, ClassIDType.RayTracingShaderImporter, ClassIDType.ShaderVariantCollection]:
            return
        if node.type == ClassIDType.Material:
            self.process_material_property_hash(node.obj.object_reader.read_typetree()['m_SavedProperties'], self.batch_data['material_'])

        if (target := self.batch_data.get(node.type)) is None:
            target = {}
            self.batch_data[node.type] = target


        if len(target) == 0 or node.type == ClassIDType.MonoBehaviour or self.nameless_map.get(node.type, True):
            self.nameless_map[node.type] = self._func(node.obj.object_reader.read_typetree(), '', target, 0)

    def _func(self, obj, cur_path, target, depth):
        tmp_flag = False
        if depth >= MAX_DEPTH:
            return tmp_flag
        # if parent_name == 'm_Materials':
        #     ___index = 0
        #     while ___index < len(obj):
        #         mat = obj[___index]
        #         if mat['m_FileID'] == 0 and mat['m_PathID'] != 0:
        #             mat = assets_file.files[mat['m_PathID']].read_typetree()
        #             for __i in range(16):
        #                 tmp_flag = self._func(mat, cur_path + f'[{__i}]', target, depth + 2, __i, assets_file) or tmp_flag
        #             break
        #         ___index += 1
        #     if ___index == len(obj):
        #         _target = self.batch_data.get(ClassIDType.Material, {})
        #         if len(_target) > 0:
        #             for __i in range(16):
        #                 for property in _target.values():
        #                     self._add_obj(target, cur_path + f'[{__i}].{property}')
        #         tmp_flag = tmp_flag or self.nameless_map.get(ClassIDType.Material, True )

        elif isinstance(obj, dict):
            cur_path = (cur_path if cur_path == '' else (cur_path + '.'))
            for ke, val in obj.items():
                if ke not in BLACKLIST:
                    flag = True
                    lower = ke.lower()
                    for item in REJECTED_KEYWORDS:
                        if item in lower:
                            flag = False
                            break
                    if flag:
                        tmp_flag = self._func(val, cur_path + ke, target, depth + 1) or tmp_flag
        elif isinstance(obj, list):
            if len(obj) == 0:
                tmp_flag = True
            elif len(obj) < 16:
                for index in range(16):
                    tmp_flag = self._func(obj[0], cur_path + f'[{index}]', target, depth + 2) or tmp_flag


        elif type(obj) in [int, float, bool] or obj is None:
            HashInfoRecorder._add_obj(target, cur_path)
        # elif type(obj) is tuple:
        #     if len(obj) == 2:
        #         tmp_flag = self._func(obj[0], cur_path + '.Key', target, depth + 1) or tmp_flag
        #         tmp_flag = self._func(obj[1], cur_path + '.Value', target, depth + 1) or tmp_flag
        #     else:
        #         util.CLogging.warn('there are more than 3 items in tuple')
        return tmp_flag

    def process_material_property_hash(self, obj, target):
        for tu in obj['m_Ints']:
            key = tu[0]
            propertyHash = util.compute_unity_hash(key) & 0xFFFFFFF | 0x80000000
            target[propertyHash] = key
        for tu in obj['m_Floats']:
            key = tu[0]
            propertyHash = util.compute_unity_hash(key) & 0xFFFFFFF | 0x80000000
            target[propertyHash] = key
        for tu in obj['m_Colors']:
            key = tu[0]
            propertyHash = util.compute_unity_hash(key) & 0xFFFFFFF
            target[propertyHash] = f'{key}.x'
            target[propertyHash | 0x10000000] = f'{key}.y'
            target[propertyHash | 0x20000000] = f'{key}.z'
            target[propertyHash | 0x30000000] = f'{key}.w'
            propertyHash |= 0x40000000
            target[propertyHash] = f'{key}.r'
            target[propertyHash | 0x10000000] = f'{key}.g'
            target[propertyHash | 0x20000000] = f'{key}.b'
            target[propertyHash | 0x30000000] = f'{key}.a'


    @staticmethod
    def _add_obj(target_dict, value):
        if value not in target_dict.values():
            target_dict[util.compute_unity_hash(value)] = value
            return True
        return False

    def notify_total(self):
        self._save_data('hash')
