import inspect

import util
from util import CLogging, InfoJsonManger
from container import Container
from fileManager import FileManager


class UnityResourceNode:
    def __init__(self, target_info: tuple, file_manager: FileManager, info_json_manager: InfoJsonManger, root=False):
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
        self.data = None
        self.parents: dict[str:UnityResourceNode] = {}
        self.children: dict[str:UnityResourceNode] = {}
        self.next = None
        self.process_data = None
        self.hierarchy_path = self.name if self.type == 'GameObject' else None
        self.hash_reference = {}
        self.dependencies = None

    def __str__(self):
        return self.get_identification()

    def init(self):
        if self.type in util.IGNORED_RESOURCE_CLASS:
            return False
        self.obj = self.file_manager.get_obj(self.cab, self.path_id)
        if self.obj is None:
            return False
        if util.SAVE_RESOURCE_CLASS_DICT:
            self.data = util.get_data_from_obj(self)
        if (len(externals := self.obj.assets_file.externals) > 0 and isinstance(externals[0], str)) or len(externals) == 0:
            self.dependencies = self.obj.assets_file.externals
        else:
            self.dependencies = [
                i.name.lower() for i in externals
            ]

        return True

    def test(self, container: Container):
        for item in container.container_objects:
            if item.test_and_add(self):
                return

    def get_node(self):
        """
        pyvis构建network所需的当前节点的信息
        :return: (节点标识， 节点名， 节点颜色， 节点信息)
        """
        return self.cab + str(self.path_id), self.name, \
            '#000000', \
            self.data if util.SAVE_RESOURCE_CLASS_DICT else self.type

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
        if obj is None:
            return
        parent_ = "" if parent is None else parent + '-'
        if isinstance(obj, list):
            if len(obj) == 0:
                return
            for i in range(len(obj)):
                self.__walk_through__(obj[i], f'{parent_}{i}')
            return

        elif isinstance(obj, dict):
            file_id = obj.get('m_FileID')
            if path_id := obj.get('m_PathID'):
                if path_id != 0:
                    self.references[parent] = (
                        self.cab if file_id == 0 else self.dependencies[file_id - 1], path_id)
                    #  self.references[parent] = (self.cab if file_id == 0 else self.dependencies[file_id - 1], path_id)
                return True
            for key, value in obj.items():
                lower_key = key.lower()
                flag = False
                for ignored in util.IGNORED_ATTR:
                    if ignored in lower_key:
                        flag = True
                        break
                if flag:
                    continue

                self.__walk_through__(value, f'{parent_}{key}')
            return
        elif isinstance(obj, tuple):
            if len(obj) == 2:
                self.__walk_through__(obj[1], f"{parent_}{obj[0]}")
            # else:
            #     logging.info(f'Ignored tuple {str(obj)}')
        else:
            if hasattr(obj, 'm_PathID'):
                # path_id = obj.m_PathID
                file_id = obj.m_FileID
                if (path_id := obj.m_PathID) != 0:
                    self.references[parent] = (
                        self.cab if file_id == 0 else self.dependencies[file_id - 1], path_id)
                return True
            elif isinstance(obj, (int, float, bool, str)):
                return

            attr_list = dir(obj)
            for attr_name in attr_list:
                attr_value = getattr(obj, attr_name)
                if attr_name.startswith("_") or inspect.isroutine(attr_value):
                    continue
                flag = False
                for ignored in util.IGNORED_ATTR:
                    lower_attr = attr_name.lower()
                    if ignored in lower_attr:
                        flag = True
                        break
                if flag:
                    continue
                try:
                    if hasattr(attr_value, 'm_PathID') and getattr(attr_value, 'm_PathID') != 0:
                        if not hasattr(attr_value, 'm_FileID'):
                            CLogging.warn("object do not own file id while owning path id")
                            continue
                        file_id = attr_value.m_FileID
                        self.references[f"{parent_}{attr_name}"] = \
                            (self.cab if file_id == 0 else self.dependencies[file_id - 1], attr_value.m_PathID)
                    elif not isinstance(attr_value, (int, float, bool, str)):
                        self.__walk_through__(attr_value, f"{parent_}{attr_name}")
                except OverflowError:
                    pass

    def walk_through(self):


        self.__walk_through__(self.obj, None)
        return self.references

    def add_child(self, attr_path, node):
        self.children[attr_path] = node
        node.parents[attr_path] = self
        if self.hierarchy_path:
            if node.type == 'Transform':
                node.hierarchy_path = self.hierarchy_path
            elif node.type == 'GameObject':
                node.hierarchy_path = f'{self.hierarchy_path}/{node.hierarchy_path}'
