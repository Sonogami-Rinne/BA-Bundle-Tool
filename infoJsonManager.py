import json
import pathlib

import util
from typeId import inverse_map
from util import FILE_INFO_JSON_PATH, CLogging, COLORS


class InfoJsonManger:
    def __init__(self):
        self.cab2bundle_json = {}
        self.cab_path_json = {}
        self.property_hash = {}
        self.dependencies = {}
        self.colors = {}
        # self.path_hash = {}

    def init(self):
        path = pathlib.Path(FILE_INFO_JSON_PATH)
        if path.exists():
            with open(FILE_INFO_JSON_PATH, 'r', encoding='utf-8') as f:
                tmp = json.loads(f.read())
                for bundle_name, bundle_data in tmp.items():
                    for cab_name, cab_data in bundle_data.items():
                        self.cab2bundle_json[cab_name] = bundle_name
                        self.cab_path_json[cab_name] = cab_data
        else:
            CLogging.error('Base info not found.Use generate_baseInfo.py first')

        path = pathlib.Path("save\\recorder\\HashInfoRecorder\\hash.json")
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                self.property_hash = json.load(f)
        else:
            CLogging.warn('Hash info json not found')

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
            self.dependencies.pop(first)

    def get_property_name(self, type_name, property_hash):
        tmp = self.property_hash[type_name].get(str(property_hash))
        return tmp

    def get_color(self, type_id):
        if self.colors.get(type_id) is None:
            self.colors[type_id] = COLORS[len(self.colors) % 51]
        return self.colors[type_id]
