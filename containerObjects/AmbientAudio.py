import json
import os
import pathlib

from containerObjects.ContainerObject import ContainerObject


class AmbientEvent(ContainerObject):

    def __init__(self, parent_container):
        super().__init__(parent_container)
        self.audios = []

    def process(self):
        for _, node in self.nodes.items():
            if target_node := node.children.get('ambientEvent'):
                target_obj = target_node.obj
                self.data.append({
                    # 'crossFadeDuration': target_obj.CrossFadeDuration,  # 目前还不知道这个的具体应用
                    'loop': target_obj.Loop == 1,
                    'volume': round(target_obj.Volume, 3),
                    'audio': target_node.children['Clip'].name
                })
                self.audios.append(target_node.children['Clip'])

    def test_and_add(self, node):
        if hasattr(node.obj, 'ambientEvent'):
            self.nodes[node.get_identification()] = node
            return True
        return False

    def save_data(self, base_path):
        _path = os.path.join(base_path, 'audio', 'other')
        pathlib.Path(_path).mkdir(parents=True, exist_ok=True)
        for audio in self.audios:
            for name, data in audio.obj.samples.items():
                with open(os.path.join(_path, name), 'wb+') as f:
                    f.write(data)
        super().save_data(base_path)

    def clear(self):
        super().clear()
        self.audios.clear()


