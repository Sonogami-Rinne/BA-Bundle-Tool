import json

import util
from typeId import inverse_map
from util import FILE_INFO_JSON_PATH, HASH_INFO_PATH, CLogging


class InfoJsonManger:

    def __init__(self):
        self.cab2bundle_json = {}
        self.cab_path_json = {}
        self.property_hash = {}
        self.dependencies = {}
        # self.path_hash = {}

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
        if self.cab_path_json[cab_name].get(str(path_id)) is None:
            CLogging.error(f'No {path_id} in f{cab_name}')
            return None
        return self.cab_path_json[cab_name][str(path_id)]

    def get_bundle_name(self, cab_name) -> str or None:
        if not cab_name.startswith('c'):  # unity default resources
            return None
        if self.cab2bundle_json.get(cab_name) is None:
            return None
        return self.cab2bundle_json[cab_name]

    def get_dependencies(self, cab_name):
        return self.dependencies.get(cab_name)

    def add_dependencies(self, cab_name, cab_dependencies):
        self.dependencies[cab_name] = cab_dependencies
        if len(self.dependencies) > util.MAX_BUFFER_LENGTH:
            first = next(iter(self.dependencies))
            self.dependencies.pop(first[0])

    # def add_property_hash(self, property_name):
    #     if property_name not in self.property_hash.values():
    #         self.property_hash[compute_unity_hash(property_name)] = property_name

    # def add_path_hash(self, path):
    #     if path not in self.path_hash.values():
    #         self.path_hash[compute_unity_hash(path)] = path

    def get_property_name(self, type_name, property_hash):
        tmp = self.property_hash[type_name].get(str(property_hash))
        return tmp

    # def get_path(self, path_hash):
    #     """
    #     根据path_hash返回GameObject的path(不是pathID)
    #     :param path_hash:
    #     :return:
    #     """
    #     return self.path_hash.get(path_hash)

    @staticmethod
    def get_class_type(type_id):
        return inverse_map[str(type_id)]
