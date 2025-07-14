from containerObjects.ContainerObject import ContainerObject
import util
from typeId import ClassIDType


class GameObject(ContainerObject):
    """
    前一次的GameObject的Hash信息记录为当前的animationClip的hah引用的数据来源.因此建议第一次遍历不开引用相关的记录，开GameObject生成hash后第二遍再开
    """

    def test_and_add(self, node):
        if node.type == ClassIDType.GameObject:
            self.nodes[node.get_identification()] = node
            return True
        return False

    def process(self):
        for _, node in self.nodes:
            self.data[util.compute_unity_hash(node.hierarchy_path)] = node

    # def save_data(self, base_path):
    #     base_path.mkdir(parents=True, exist_ok=True)
    #     with open(os.path.join(base_path, "gameObjects.json"), 'w+', encoding='utf-8') as f:
    #         json.dump(self.data, f, indent=2)

    def get_path(self, path_hash):
        return self.data[path_hash]

