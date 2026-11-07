import numpy as np

import util
from containerObjects.ContainerObject import ContainerObject
from typeId import ClassIDType


class GameObject(ContainerObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.game_objects = {}
        self.registered = {}

    def test_and_add(self, node):
        if node.type == ClassIDType.GameObject:
            self.nodes[node.get_identification()] = node
            return True
        return False

    def process(self):
        self.data_keys = list(self.nodes.keys())
        self.data = {}
        for identification, node in self.nodes.items():
            names = [node.name]
            # seen = {identification}
            transform = node.transform
            while parent_transform := transform.children.get('m_Father'):
                parent = parent_transform.game_object
                if parent is None:
                    break
                parent_id = parent.get_identification()
                if parent_id not in self.nodes:
                    break
                # if parent_id in seen:
                #     raise ValueError(f'Cycle in GameObject hierarchy: {identification}')
                names.append(parent.name)
                # seen.add(parent_id)
                transform = parent_transform

            node.transform.hierarchy = tuple(reversed(names))
            node.transform.hierarchy_children = [
                child for name, child in node.transform.children.items()
                if name.startswith('m_Children')
            ]

            self.game_objects[identification] = '/'.join(node.transform.hierarchy)

    def register_game_object(self, node, need_middle_node=True):
        iden = node.get_identification()
        need_middle_node = need_middle_node or self.registered.get(iden, False)
        self.registered[iden] = need_middle_node

    def clear(self):
        self.game_objects.clear()
        self.registered.clear()
        super().clear()

    def get_game_object_path(self, iden):
        return self.game_objects[iden]

    def save_data(self, base_path):
        def dfs(ancestor, node, could_active):
            game_object = node.game_object

            new_ancestor = ancestor
            if (iden := game_object.get_identification()) in self.registered:
                info = {
                    'name': game_object.name,
                    'hierarchy': '/'.join(game_object.transform.hierarchy),
                    'active': game_object.obj.m_IsActive,
                    'couldActive': could_active
                }
                if ancestor is None or node.children['m_Father'] == ancestor or not self.registered[iden]:
                    info['transformToParent'] = None
                    info['parent'] = -1 if ancestor is None else self.get_index(ancestor.game_object.get_identification())
                else:
                    parent_matrix = util.get_transform(node.children['m_Father'].game_object)
                    ancestor_matrix = util.get_transform(ancestor.game_object)
                    relative = np.linalg.inv(ancestor_matrix) @ parent_matrix
                    info['parent'] = self.get_index(ancestor.game_object.get_identification())
                    info['transformToParent'] = relative.tolist()
                transform = node.obj
                info['matrix'] = util.get_transform(game_object).tolist()
                info['localPosition'] = util.to_tuple(transform.m_LocalPosition)
                info['localRotation'] = util.to_tuple(transform.m_LocalRotation)
                info['localScale'] = util.to_tuple(transform.m_LocalScale)
                self.data[self.get_index(iden)] = info
                new_ancestor = node
            else:
                if not game_object.obj.m_IsActive:
                    could_active = False
            for child in node.hierarchy_children:
                dfs(new_ancestor, child, could_active)

        for _node in self.nodes.values():
            if len(_node.transform.hierarchy) == 1:
                dfs(None, _node.transform, True)

        super().save_data(base_path)
