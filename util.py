import math
import os.path
import typing
import zlib

import UnityPy
import numpy as np
from scipy.spatial.transform import Rotation
from typeId import ClassIDType, inverse_map

IGNORED_RESOURCE_CLASS = [ClassIDType.AssetBundle]
"""
忽略的资源类型
"""

MAX_BUFFER_LENGTH = 100
"""
缓冲区最大文件数目
"""

BUNDLES_PATH = r"E:\BlueArchive\YostarGames\BlueArchive_JP\BlueArchive_Data\StreamingAssets\AssetBundles"
"""
bundle文件目录
"""

SAVE_RESOURCE_CLASS_DICT = True
FILE_INFO_JSON_PATH = "baseInfo.json"
"""
记录各个文件基本信息的路径
"""

"""
记录hash信息的文件的路径
"""

MAX_INFO_STR_LENGTH = 256

MAX_DEPTH = 100
"""
遍历引用时最大遍历深度
"""

CONTAINER_RECORD = True

RECORDER_EXTERNAL = False
RECORDER_HASH_INFO = False
RECORDER_TRACK_INFO = False
RECORDER_TRACK_VISUALIZATION = False
RECORDER_SHADER = False

EXPORT_HLSL_SHADER = False
IGNORE_UNITY_DEFAULT_RESOURCE = True

PREFABS_MODE = True

COLORS = (
    '#A1C0F0', '#3D9B74', '#F2856D', '#F5D547', '#8E6BD8', '#61C6CB', '#E980C2', '#B9C05F', '#DA7B89',
    '#83B1B6', '#F27D52', '#7D83C7', '#62B388', '#EAD55C', '#BE6DE2', '#68D7CE', '#E44E6D', '#A6CF63',
    '#C97AAE', '#6CA2EA', '#F9A662', '#8B9ED2', '#78C79F', '#F0D348', '#C369DA', '#4CBCC4', '#E16084',
    '#97C555', '#D07A9D', '#5E98DD', '#F2974F', '#9F94D0', '#6CD3B2', '#F2C746', '#C66FDE', '#50C9C9',
    '#E56678', '#ACC66B', '#D978AE', '#68A7EC', '#F59F60', '#5EC0A3', '#D95F9B', '#7BB14D', '#C08B5C',
    '#9B5CC0', '#4D8BB1', '#E57373', '#64B5F6', '#BA68C8', '#4DB6AC', '#FF8A65', '#7986CB', '#AED581',
    '#FFB74D', '#9575CD', '#4FC3F7', '#81C784', '#FFD54F', '#F06292'
)


def env_load(env):
    """
    根据env返回结构化的信息
    :param env:
    :return: (common_data, prefab_data)
    """
    common_data = {}
    for cab in env.assets:
        common_cab = {}
        for path_id, file in cab.files.items():
            if file.type.value not in IGNORED_RESOURCE_CLASS:
                common_cab[path_id] = (
                    file.type.value,
                    file.read()
                )
        common_data[cab.name.lower()] = common_cab
    return common_data


def env_load_prefabs(bundle):
    env = UnityPy.load(os.path.join(BUNDLES_PATH, bundle + '.bundle'))
    prefab_data = []
    for cab in env.assets:
        for prefab_name, asset_info in cab.assetbundle.m_Container:
            asset = asset_info.asset

            if asset.type.value == ClassIDType.GameObject and asset.m_PathID != 0:
                prefab_data.append((cab.name.lower(), asset.m_PathID, asset.read()))  # 默认此处的prefab都在该包内，没有外部引用
    return prefab_data


def get_data_from_obj(obj) -> str:
    """
    保存各个节点的信息(简易)
    :param obj:
    :return:
    """
    result = f'Type:{obj.object_reader.type.name}\n'
    for name, data in obj.object_reader.read_typetree().items():
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


def decompose_2d_transform(matrix_4x4):
    """
    从 4x4 变换矩阵提取 2D 变换参数（忽略 z 轴）
    :param matrix_4x4: 4x4 变换矩阵（3D 齐次坐标）
    :return: (tx, ty), theta, (sx, sy)
    """
    # 提取 2D 平移
    tx, ty = matrix_4x4[0, 3], matrix_4x4[1, 3]

    # 提取 2D 旋转角度 θ（弧度）
    theta = np.arctan2(matrix_4x4[1, 0], matrix_4x4[0, 0])

    # 提取 2D 缩放（去除旋转影响）
    sx = np.sqrt(matrix_4x4[0, 0] ** 2 + matrix_4x4[1, 0] ** 2)
    sy = np.sqrt(matrix_4x4[0, 1] ** 2 + matrix_4x4[1, 1] ** 2)

    return (round(tx, 2), round(ty, 2)), round(theta, 4), (round(sx, 2), round(sy, 2))

def euler_to_quaternion(li: tuple[float, float, float]):
    cz = math.cos(li[0] * 0.5)
    sz = math.sin(li[0] * 0.5)
    cx = math.cos(li[1] * 0.5)
    sx = math.sin(li[1] * 0.5)
    cy = math.cos(li[2] * 0.5)
    sy = math.sin(li[2] * 0.5)

    # 四元数分量（公式推导：q = q_y * q_x * q_z）
    w = cx * cy * cz + sx * sy * sz
    x = sx * cy * cz + cx * sy * sz
    y = cx * sy * cz - sx * cy * sz
    z = cx * cy * sz - sx * sy * cz

    return x, y, z, w

def get_transform(base_node):
    """
    从一个GameObject的node那里获取数据
    :param base_node:
    :return:
    """
    if (transform_matrix := base_node.process_data) is None:
        node = base_node.transform
        transform_stack = [node]
        parent_transform_node = node.children.get('m_Father', None)
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

def better_print(content, indent_num=4):
    """
    简易优质打印
    :param content:
    :param indent_num:
    :return:
    """
    parts = []
    consistent_blank_line_count = 0
    base_indent = ' ' * indent_num
    cur_indent = ''

    def process(sub_line):
        ls = sub_line.strip()
        nonlocal consistent_blank_line_count
        nonlocal cur_indent
        if len(ls) == 0:
            consistent_blank_line_count += 1
            if consistent_blank_line_count > 2:
                return
            # after += '\n'
            parts.append('')
            return
        else:
            consistent_blank_line_count = 0
        if (chr_index := ls.find('{')) >= 0:
            if chr_index > 0:
                process(ls[:chr_index])
            # after += cur_indent + '{\n'
            parts.append(f'{cur_indent}{"{"}')
            cur_indent += base_indent
            if chr_index < len(ls) - 1:
                process(ls[chr_index + 1:])
        elif (chr_index := ls.find('}')) >= 0:
            if chr_index > 0:
                # after += cur_indent + ls[:chr_index] + '\n'
                parts.append(f'{cur_indent}{ls[:chr_index]}')
            cur_indent = cur_indent[:-4]
            # after += cur_indent + '}\n'
            parts.append(f'{cur_indent}{"}"}')
            if chr_index < len(ls) - 1:
                process(ls[chr_index + 1:])
        else:
            # after += cur_indent + ls + '\n'
            parts.append(f'{cur_indent}{ls}')

    for line in content.split('\n'):
        process(line)

    return '\n'.join(parts)


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
