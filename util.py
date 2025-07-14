import zlib

import numpy as np
from scipy.spatial.transform import Rotation

IGNORED_RESOURCE_CLASS = ['AssetBundle']
"""
忽略的资源类型
"""

MAX_BUFFER_LENGTH = 100
"""
缓冲区最大文件数目
"""

BUNDLES_PATH = "E:\\@\\1\\Downloads\\BundleFiles"
"""
bundle文件目录
"""

SAVE_RESOURCE_CLASS_DICT = False
FILE_INFO_JSON_PATH = "merged.json"
"""
记录各个文件基本信息的路径
"""

HASH_INFO_PATH = "propertyHash.json"
"""
记录hash信息的文件的路径
"""

MAX_INFO_STR_LENGTH = 256

MAX_DEPTH = 0
"""
遍历引用时最大遍历深度
"""

CONTAINER_RECORD = False

RECORDER_EXTERNAL = False
RECORDER_HASH_INFO = False
RECORDER_TRACK_INFO = False
RECORDER_TRACK_VISUALIZATION = False


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
                cab_data[path_id] = file.read()
            if len(cab_data) > 0:
                file_objects[cab_name] = cab_data

    return file_objects


def get_data_from_obj(obj) -> str:
    """
    保存各个节点的信息(简易)
    :param obj:
    :return:
    """
    result = ''
    for name, data in obj.object_reader.read_typetree():
        if len(line := str(data)) > MAX_INFO_STR_LENGTH:
            line = 'Too long to display'
        result += f'{name}: {line}\n'
    return result


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


def get_transform(base_node):
    """
    从一个GameObject的node那里获取数据
    :param base_node:
    :return:
    """
    if (transform_matrix := base_node.process_data) is None:
        node = base_node.transform
        transform_stack = [node]
        parent_transform_node = node.children['m_Father']  # 有些奇怪,但m_Father确实是由该节点出去的
        while parent_transform_node and parent_transform_node.process_data is None:
            transform_stack.append(parent_transform_node)
            parent_transform_node = parent_transform_node.children.get('m_Father')
        if parent_transform_node:
            transform_matrix = parent_transform_node.process_data
        else:
            transform_matrix = np.eye(4)
        while len(transform_stack) > 0:
            transform_node = transform_stack.pop()
            obj = transform_node.obj
            transform_matrix = np.dot(transform_matrix, compose_transform_matrix(
                obj.m_LocalPosition, obj.m_LocalRotation, obj.m_LocalScale
            ))
            transform_node.process_data = transform_matrix

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


