import inspect
import json
import typing

from typeId import ClassIDType, inverse_map

import util
from util import CLogging
from infoJsonManager import InfoJsonManger
from fileManager import FileManager


class UnityResourceNode:

    def __init__(self, target_info: tuple, file_manager: FileManager, info_json_manager: InfoJsonManger, root=False):
        """
        :param target_info: (cab, path_id, type_id, name)
        :param file_manager:
        :param info_json_manager:
        :param root:
        """
        self.root = root
        self.cab = target_info[0]
        self.path_id = target_info[1]
        self.type = target_info[2]
        self.name = target_info[3]
        self.file_manager = file_manager
        self.info_json_manager = info_json_manager
        self.bundle = info_json_manager.get_bundle_name(self.cab)
        self.references = {}
        self.obj = None
        self.parents: dict[str:UnityResourceNode] = {}
        self.children: dict[str:UnityResourceNode] = {}
        self.dependencies = None

        self.process_data = None  # Transform,GameObject的变化矩阵的存储
        self.transform = None  # gameObject的Transform节点，由于经常用到，故单独记录
        self.game_object = None

        self.hierarchy = None
        self.hierarchy_children = None
        # self.father = None

    def __str__(self):
        return self.get_identification()

    def init(self):
        if self.type in util.IGNORED_RESOURCE_CLASS:
            return False
        self.obj = self.file_manager.get_obj(self.cab, self.path_id)
        if self.obj is None:
            return False

        if (dependencies := self.info_json_manager.get_dependencies(self.cab)) is None:
            if (len(externals := self.obj.assets_file.externals) > 0 and isinstance(externals[0], str)) or len(
                    externals) == 0:
                dependencies = externals
            else:
                dependencies = [
                    i.name.lower() for i in externals
                ]
            self.info_json_manager.add_dependencies(self.cab, dependencies)
        self.dependencies = dependencies

        return True

    def get_node(self):
        """
        pyvis构建network所需的当前节点的信息
        :return: (节点标识， 节点名， 节点颜色， 节点信息)
        """
        data = None
        type_name = inverse_map[str(self.type)]
        if util.SAVE_RESOURCE_CLASS_DICT:
            data = util.get_data_from_obj(self.obj)
        return (
            self.name,
            '#000000' if self.root else self.info_json_manager.get_color(self.type),
            data if util.SAVE_RESOURCE_CLASS_DICT else type_name
        )

    def get_identification(self):
        return self.cab + str(self.path_id)

    def get_out_edges(self):
        """
        pyvis构建network所需的当前节点开始的有向边
        :return:(目标节点标识, 边名)
        """
        return [
            (node.get_identification(), property_path)
            for property_path, node in self.children.items()
        ]

    def __walk_through__(self, obj, parent):
        """
        遍历dict或list.起始为object_reader.read_typetree()
        :param obj:
        :param parent:
        :return:
        """
        if obj is None:
            return
        parent_ = parent + '-' if parent else parent
        if isinstance(obj, dict):
            if (path_id := obj.get('m_PathID')) is not None:
                if path_id != 0:
                    if (file_id := obj.get('m_FileID')) is None:
                        CLogging.warn('Warn, object do not own file_id while owing path_id.')
                    else:
                        self.references[parent] = (
                            self.cab if file_id == 0 else self.dependencies[file_id - 1], path_id)
                return  # 只要有m_PathID就可以提前结束
            else:
                for name, value in obj.items():
                    if isinstance(value, (dict, list, tuple)):
                        self.__walk_through__(value, f'{parent_}{name}')
        elif isinstance(obj, list) and (length := len(obj)) > 0:
            if isinstance((obj[0]), (str, int, float, bool)):
                return
            for index in range(length):
                self.__walk_through__(obj[index], f'{parent_}{index}')
        elif isinstance(obj, tuple):
            #  emm,目前只看到一个两元素的tuple有PPtr
            if len(obj) == 2 and not isinstance(obj[1], (int, float, str, bool)):
                self.__walk_through__(obj[1], f'{parent_}{obj[0]}')

    def walk_through(self) -> dict[str, tuple[str, int]]:
        """
        遍历属性以获取引用
        :return:dict[attr_path : (cab, path_id)]
        """
        self.__walk_through__(self.obj.object_reader.read_typetree(), '')
        return self.references

    def add_child(self, attr_path, node):
        self.children[attr_path] = node
        node.parents[attr_path] = self

        if self.type == ClassIDType.GameObject:
            if node.type == ClassIDType.Transform:
                self.transform = node
                node.game_object = self

        elif self.type == ClassIDType.Transform:
            if node.type == ClassIDType.GameObject:
                self.game_object = node
                node.transform = self

