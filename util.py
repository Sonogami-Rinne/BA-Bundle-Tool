import inspect
import json
import zlib

import numpy as np
from scipy.spatial.transform import Rotation
from typeId import inverse_map

IGNORED_ATTR = ['object_reader', 'assetsfile', '__node__', 'assets_file']
"""
在遍历对象的属性时忽略的属性
"""

IGNORED_RESOURCE_CLASS = ['AssetBundle']
"""
忽略的资源类型
"""

MAX_DEPTH = 50
"""
遍历引用时最大遍历深度
"""

MAX_BUNDLE_BUFFER_LENGTH = 150
"""
缓冲区最大文件数目
"""

BUNDLES_PATH = "E:\\@\\1\\Downloads\\BundleFiles"
"""
bundle文件目录
"""

SAVE_RESOURCE_CLASS_DICT = False
FILE_INFO_JSON_PATH = ""
"""
记录各个文件基本信息的路径
"""

HASH_INFO_PATH = ""
"""
记录hash信息的文件的路径
"""

MAX_INFO_STR_LENGTH = 256


def env_load(env):
    """
    根据env返回结构化的信息
    :param env:
    :return:
    """
    file_objects = {}
    for cab_name, cab_value in env.cabs.items():
        if not hasattr(cab_value, 'files'):
            continue
        cab_data = {}
        for path_id, file in cab_value.files.items():
            if file.type.name not in IGNORED_RESOURCE_CLASS:
                file_data = file.read()
                cab_data[path_id] = {
                    'type': file.type.name,
                    'name': file_data.m_Name if hasattr(file_data, 'm_Name') else 'Unknown',
                    'obj': file_data
                }
            if len(cab_data) > 0:
                cab_dependencies = [
                    i.name.lower() for i in cab_value.externals
                ]
                if cab_dependencies is None:
                    cab_dependencies = cab_value.assetbundle.assets_file.assetbundle.m_Dependencies
                file_objects[cab_name] = {
                    'data': cab_data,
                    'dependencies': cab_dependencies
                }

    return file_objects


def get_data_from_obj(obj) -> str:
    """
    保存各个节点的信息(简易)
    :param obj:
    :return:
    """
    result = ''
    for attr_name, attr_value in obj.read_typetree():
        data = str(attr_value)
        if len(data) > MAX_INFO_STR_LENGTH:
            data = 'Too long to display'
        result += f'{attr_name}: {data}\n'
    return result
    # for attr_name in dir(obj):
    #     attr_value = getattr(obj, attr_name)
    #     if attr_name.startswith("_") or inspect.isroutine(attr_value) or type(attr_value).__name__ in (
    #             "PPtr", "SerializedFile", "ObjectReader"):
    #         continue
    #     if isinstance(attr_value, list) and len(attr_value) > 0 and type(attr_value[0]).__name__ in (
    #             "PPtr", "SerializedFile", "ObjectReader"):
    #         continue
    #     result += f'{attr_name}: {attr_value}\n'
    # return result


def compute_unity_hash(s: str) -> int:
    """
    计算s的hash
    :param s:
    :return:
    """
    return zlib.crc32(s.encode('utf-8')) & 0xFFFFFFFF


def to_tuple(obj):
    """
    转化为元组
    :param obj:
    :return:
    """
    if hasattr(obj, 'x'):
        if hasattr(obj, 'w'):
            return obj.x, obj.y, obj.z, obj.w
        return obj.x, obj.y, obj.z
    elif hasattr(obj, 'r'):
        if hasattr(obj, 'a'):
            return obj.r, obj.g, obj.b, obj.a
        return obj.r, obj.g, obj.b


def compose_transform_matrix(translation, quaternion, scale):
    """
    将Transform的数据转化为Matrix
    :param translation:
    :param quaternion:
    :param scale:
    :return:
    """
    # 确保输入是numpy数组
    translation = np.asarray(to_tuple(translation))
    quaternion = np.asarray(to_tuple(quaternion))
    scale = np.asarray(to_tuple(scale))
    if scale.ndim == 0:  # 如果是标量
        scale = np.array([scale, scale, scale])
    elif len(scale) == 1:  # 如果是一维数组但只有一个元素
        scale = np.repeat(scale, 3)
    scale_matrix = np.diag(np.append(scale, 1.0))
    rotation = Rotation.from_quat(quaternion)
    rotation_matrix = np.eye(4)
    rotation_matrix[:3, :3] = rotation.as_matrix()
    translation_matrix = np.eye(4)
    translation_matrix[:3, 3] = translation
    transform_matrix = translation_matrix @ rotation_matrix @ scale_matrix

    return transform_matrix


class CLogging:
    """
    日志输出
    """

    @staticmethod
    def error(message):
        print(f"\033[91m{message}\033[0m")

    @staticmethod
    def warn(message):
        print(f"\033[93m{message}\033[0m")

    @staticmethod
    def info(message):
        print(f"\033[97m{message}\033[0m")


class InfoJsonManger:

    def __init__(self):
        self.cab2bundle_json = {}
        self.cab_path_json = {}
        self.property_hash = {}
        self.path_hash = {}

    def init(self, using_file_info=True, using_hash_info=True):
        if using_file_info:
            with open(FILE_INFO_JSON_PATH, 'r', encoding='utf-8') as f:
                tmp = json.loads(f.read())
                for bundle_name, bundle_data in tmp.items():
                    for cab_name, cab_data in bundle_data.items():
                        self.cab2bundle_json[cab_name] = bundle_name
                        self.cab_path_json[cab_name] = cab_data
        if using_hash_info:
            with open(HASH_INFO_PATH, 'r', encoding='utf-8') as f:
                self.property_hash = json.load(f)

    def get_path_info(self, cab_name, path_id) -> dict or None:
        if not cab_name.startswith('c'):  # unity default resources
            return None
        if self.cab_path_json.get(cab_name) is None:
            return None
        if self.cab_path_json[cab_name]['data'].get(str(path_id)) is None:
            CLogging.error(f'No {path_id} in f{cab_name}')
            return None
        return self.cab_path_json[cab_name]['data'][str(path_id)]

    def get_bundle_name(self, cab_name) -> str or None:
        if not cab_name.startswith('c'):  # unity default resources
            return None
        if self.cab2bundle_json.get(cab_name) is None:
            return None
        return self.cab2bundle_json[cab_name]

    def add_property_hash(self, property_name):
        if property_name not in self.property_hash.values():
            self.property_hash[compute_unity_hash(property_name)] = property_name

    def add_path_hash(self, path):
        if path not in self.path_hash.values():
            self.path_hash[compute_unity_hash(path)] = path

    def get_property_name(self, property_hash):
        return self.property_hash.get(property_hash)

    def get_path(self, path_hash):
        """
        根据path_hash返回GameObject的path(不是pathID)
        :param path_hash:
        :return:
        """
        return self.path_hash.get(path_hash)

    @staticmethod
    def get_class_type(type_id):
        return inverse_map[str(type_id)]


class Recorder:
    def __init__(self):
        self.batch_data = {}

    def clear(self):
        self.batch_data.clear()

    def add(self, *args):
        data = self.batch_data
        sub_data = None
        for i in args:
            sub_data = data.get(i)
            if sub_data is None:
                sub_data = {}
                data[i] = sub_data
            data = sub_data
        return sub_data

    def get_save(self):
        return self.batch_data


class BaseInfoRecorder(Recorder):
    """
    MAX_DEPTH 设置为 0, 头节点创建后调用add,自行决定保存时机。保存完手动clear
    """

    def clear(self):
        self.batch_data.clear()

    def add(self, bundle_name, cab_name, path_id, node):
        cab_data = super().add(bundle_name, cab_name, path_id)
        cab_data[path_id] = {
            'name': node.name,
            'type': node.type
        }


class TrackInfoRecorder(Recorder):
    """
    遍历extends里面创建一个节点后调用,自行决定保存时机，保存完手动clear
    """

    def add(self, cab_name, path_id, cab_name1, path_id1, reference_name):
        path_data = super().add(cab_name, path_id, cab_name1)
        path_data[path_id1] = reference_name


class HashInfoRecorder(Recorder):
    """
    新节点创建后调用。不可分批保存，以避免重复.考虑运行时动态获得hash,那么这个就可以废弃了
    """

    def add(self, node_obj):
        for attr_name in dir(node_obj):
            if attr_name.startswith('_') or attr_name in IGNORED_ATTR:
                continue
            attr_value = getattr(node_obj, attr_name)
            if inspect.isroutine(attr_value) or attr_name in self.batch_data.values():
                continue
            self.batch_data[compute_unity_hash(attr_name)] = attr_name


class ExternalsRecorder(Recorder):
    """
    每个bundle或整个流程保存一次。每创建一个Node时add
    """

    def __init__(self):
        super().__init__()
        self.info_json_file_manager: InfoJsonManger or None = None

    def set_info_json_file_manager(self, obj: InfoJsonManger):
        self.info_json_file_manager = obj

    def add(self, stu_name, node):
        data = self.batch_data.get(stu_name)
        if data is None:
            data = []
            self.batch_data[stu_name] = data

        for _, tu in node.references:
            if tu[0] == node.cab:
                continue
            bundle_name = self.info_json_file_manager.get_bundle_name(tu[0])
            if bundle_name not in data:
                data.append(bundle_name)
