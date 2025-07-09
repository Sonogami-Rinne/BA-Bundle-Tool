from recorder.containerObjects.ContainerObject import ContainerObject
import util


class GameObject(ContainerObject):
    """
    仅用于hash的，不存储
    """

    def test_and_add(self, node):
        if node.type == 'GameObject':
            self.nodes[util.compute_unity_hash(node.hierarchy_path)] = node
            return True
        return False

    def save_data(self, folder):
        pass

    def get_path(self, path_hash):
        return self.nodes[path_hash]
