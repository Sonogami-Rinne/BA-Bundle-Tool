from recorder.containerObjects.ContainerObject import ContainerObject


class AmbientEvent(ContainerObject):

    def process(self):
        for _, node in self.nodes.items():
            target_node = node.children['ambientEvent']
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
