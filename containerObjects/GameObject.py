import pathlib

from containerObjects.ContainerObject import ContainerObject
import util
from typeId import ClassIDType


class GameObject(ContainerObject):

    def test_and_add(self, node):
        if node.type == ClassIDType.GameObject:
            self.nodes[node.get_identification()] = node
            return True
        return False

    def process(self):
        self.data_keys = list(self.nodes.keys())

    def save_data(self, base_path: pathlib.Path):
        return


