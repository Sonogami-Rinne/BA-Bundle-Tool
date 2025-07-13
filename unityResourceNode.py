import inspect
import json

from typeId import ClassIDType, inverse_map

import util
from util import CLogging, InfoJsonManger
from containerObjects.index import Container
from fileManager import FileManager


class UnityResourceNode:

    def __init__(self, target_info: tuple, file_manager: FileManager, info_json_manager: InfoJsonManger):
        self.cab = target_info[0]
        self.path_id = target_info[1]
        self.type = getattr(ClassIDType, target_info[2])
        self.name = target_info[3]
        self.file_manager = file_manager
        self.info_json_manager = info_json_manager
        self.bundle = info_json_manager.get_bundle_name(self.cab)
        self.references = {}
        self.obj = None
        self.parents: dict[str:UnityResourceNode] = {}
        self.children: dict[str:UnityResourceNode] = {}
        self.next = None  # 用于链表
        self.dependencies = None

        self.process_data = None  # Transform,GameObject的变化矩阵的存储
        self.hierarchy_path = self.name if self.type == 'GameObject' else None  # GameObject的路径
        self.transform = None  # gameObject的Transform节点，由于经常用到，故单独记录
        # self.hash_reference = {}

    def __str__(self):
        return self.get_identification()

    def init(self):
        if self.type in util.IGNORED_RESOURCE_CLASS:
            return False
        self.obj = self.file_manager.get_obj(self.cab, self.path_id)
        if self.obj is None:
            return False

        if (dependencies := self.file_manager.get_dependencies(self.cab)) is None:
            if (len(externals := self.obj.assets_file.externals) > 0 and isinstance(externals[0], str)) or len(
                    externals) == 0:
                dependencies = externals
            else:
                dependencies = [
                    i.name.lower() for i in externals
                ]
            self.file_manager.add_dependencies(self.cab, dependencies)
        self.dependencies = dependencies

        return True

    def get_node(self, ignore_identification=True):
        """
        pyvis构建network所需的当前节点的信息
        :return: (节点标识， 节点名， 节点颜色， 节点信息)
        """
        data = None
        type_name = inverse_map[str(self.type)]
        if util.SAVE_RESOURCE_CLASS_DICT:
            data = util.get_data_from_obj(self.obj)
        return (self.name, '#000000', data if util.SAVE_RESOURCE_CLASS_DICT else type_name) \
            if ignore_identification else (self.cab + str(self.path_id), self.name, '#000000',
                                           data if util.SAVE_RESOURCE_CLASS_DICT else type_name)

    def get_identification(self):
        return self.cab + str(self.path_id)

    def get_out_edges(self):
        """
        pyvis构建network所需的当前节点开始的有向边
        :return:(目标节点标识, 边名)
        """
        return [
            (identification[0] + str(identification[1]), property_path)
            for property_path, identification in self.references.items()
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
                    if (file_id := obj['m_FileID']) is None:
                        CLogging.warn('Error, object do not own file_id while owing path_id.Target:')
                        CLogging.warn(json.dumps(obj, indent=2, ensure_ascii=False))
                    else:
                        self.references[parent] = (
                            self.cab if file_id == 0 else self.dependencies[file_id - 1], path_id)
                return  # 只要有m_PathID就可以提前结束
            else:
                for name, value in obj.items():
                    if isinstance(obj, (dict, list)):
                        self.__walk_through__(value, parent_ + name)
        elif isinstance(obj, list) and (length := len(obj)) > 0:
            if isinstance((obj[0]), (str, int, float, bool)):
                return
            for index in range(length):
                self.__walk_through__(obj[index], parent_ + str(index))
        elif isinstance(obj, tuple):
            #  emm,目前只看到一个两元素的tuple有PPtr
            if len(obj) == 2:
                self.__walk_through__(obj[1], parent_ + obj[0])

    def walk_through(self):
        """
        遍历属性以获取引用。其实应该遍历object_reader.read_typetree的结果字典的
        :return:
        """
        self.__walk_through__(self.obj.object_reader.read_typetree(), None)
        return self.references

    def add_child(self, attr_path, node):
        self.children[attr_path] = node
        node.parents[attr_path] = self
        if self.hierarchy_path:
            if node.type == ClassIDType.Transform:
                node.hierarchy_path = self.hierarchy_path
                if self.type == ClassIDType.GameObject:
                    self.transform = node
            elif node.type == ClassIDType.GameObject:
                node.hierarchy_path = f'{self.hierarchy_path}/{node.hierarchy_path}'
