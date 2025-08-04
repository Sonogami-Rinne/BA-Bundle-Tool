import json
import os
import pathlib

from containerObjects.ContainerObject import ContainerObject
from typeId import ClassIDType
from linkedList import LinkedList


class GameObject(ContainerObject):

    def test_and_add(self, node):
        if node.type == ClassIDType.GameObject:
            self.nodes[node.get_identification()] = node
            return True
        return False

    def process(self):
        self.data_keys = list(self.nodes.keys())
        self.data = {
            i: '' for i in self.data_keys
        }
        root = next(iter(self.nodes.values()))
        linked_list = LinkedList(root.transform)
        linked_list.head.data.hierarchy = ()

        while linked_list.head:
            for node in linked_list.walk_through():
                node.hierarchy += (node.game_object.name,)
                self.data[node.game_object.get_identification()] = '/'.join(node.hierarchy)
                # self.data.append('/'.join(node.hierarchy))
                to_adds = []
                for _name, _node in node.children.items():
                    if _name.startswith('m_Children'):
                        _node.hierarchy = node.hierarchy
                        to_adds.append(_node)
                node.hierarchy_children = to_adds
                linked_list.adds(node.hierarchy_children)

    def save_data(self, base_path):
        base_path.mkdir(parents=True, exist_ok=True)
        with open(os.path.join(base_path, self.__class__.__name__ + '.json'), 'w+', encoding='utf-8') as f:
            json.dump(list(self.data.values()), f, indent=2)

        self.clear()
