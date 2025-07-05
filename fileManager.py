import os.path

import UnityPy

import util


class FileManager:
    def __init__(self, info_json_manager: util.InfoJsonManger):
        self.buffer = {}
        self.max_length = util.MAX_BUNDLE_BUFFER_LENGTH
        self.info_json_manager = info_json_manager

    def get_obj(self, cab_name, path_id):
        if self.info_json_manager.get_path_info(cab_name, path_id) is None:
            return None
        bundle_name = self.info_json_manager.get_bundle_name(cab_name)
        if bundle_data := self.buffer.get(bundle_name) is None:
            env = UnityPy.load(os.path.join(util.BUNDLES_PATH, bundle_name, '.bundle'))
            objects = self.__add_buffer__(env, bundle_name)
            return objects[cab_name]['data'][path_id]['obj']
        else:
            return bundle_data[cab_name]['data'][path_id]['obj']

    def get_bundle_(self, bundle_name):
        if bundle_data := self.buffer.get(bundle_name) is None:
            env = UnityPy.load(os.path.join(util.BUNDLES_PATH, bundle_name))
            objects = self.__add_buffer__(env, bundle_name)
            return objects
        else:
            return bundle_data

    def __add_buffer__(self, env, bundle_name):
        env_objects = util.env_load(env)
        self.buffer[bundle_name] = env_objects
        if len(self.buffer) > self.max_length:
            first = next(iter(self.buffer))
            del first
        return env_objects

    # def get_cab_dependencies(self, cab_name):
    #     return self.cab_path_json[cab_name]['dependencies']
