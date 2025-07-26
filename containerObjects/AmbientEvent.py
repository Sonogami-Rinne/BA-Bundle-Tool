import json
import os

from containerObjects.ContainerObject import ContainerObject


class AmbientEvent(ContainerObject):

    def process(self):
        for _, node in self.nodes.items():
            if target_node := node.children.get('ambientEvent'):
                target_obj = target_node.obj
                self.data.append({
                    'crossFadeDuration': target_obj.CrossFadeDuration,  # 目前还不知道这个的具体应用
                    'loop': target_obj.Loop == 1,
                    'volume': target_obj.Volume,
                    'audio': target_node.children['Clip'].obj
                })

    def test_and_add(self, node):
        if hasattr(node.obj, 'ambientEvent'):
            self.nodes[node.get_identification()] = node
            return True
        return False

    def save_data(self, base_path):
        base_path.mkdir(parents=True, exist_ok=True)
        item = self.data[0]  # 估计只会有一个
        audio_obj = item['audio']
        item.pop('audio')
        for name, data in audio_obj.samples.items():
            with open(os.path.join(base_path, 'ambient-' + name), 'wb+') as f:
                f.write(data)
        with open(os.path.join(base_path, 'ambient-config.json'), 'w+', encoding='utf-8') as f:
            json.dump(item, f, indent=2)
