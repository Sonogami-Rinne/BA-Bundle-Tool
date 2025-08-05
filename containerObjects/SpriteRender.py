import os
import pathlib

import util
from containerObjects.ContainerObject import ContainerObject
from typeId import ClassIDType
from util import to_tuple


class SpriteRender(ContainerObject):

    def __init__(self, parent_container):
        super().__init__(parent_container)
        self.sprites = []

    def test_and_add(self, node):
        if node.type == ClassIDType.SpriteRenderer:
            self.nodes[node.get_identification()] = node
            return True
        return False

    def process(self):
        nodes_dict = self.parent_container.nodes_dict
        game_object_container = self.parent_container.container_objects['GameObject']
        for _, node in self.nodes.items():
            obj = node.obj

            dependencies = node.dependencies

            translate, rotation, scale = util.decompose_2d_transform(util.get_transform(node.children['m_GameObject']))
            item = {
                'sprite': node.children['m_Sprite'].name,
                'color': to_tuple(obj.m_Color),
                'flip': (obj.m_FlipX, obj.m_FlipY),
                # 'material': obj.m_Materials,
                # 'materials': [
                #     material for material in obj.m_Materials
                # ],
                'drawMode': obj.m_DrawMode,
                'sortingLayer': obj.m_SortingLayer,
                'maskInteraction': obj.m_MaskInteraction,
                'gameObject': game_object_container.get_index(node.children['m_GameObject'].get_identification()),
                'translate': translate,
                'rotation': rotation,
                'scale': scale
            }
            material_data = []
            images = []
            for material in obj.m_Materials:
                iden = (dependencies[material.m_FileID - 1] if material.m_FileID != 0 else node.cab) + str(material.m_PathID)
                if target := nodes_dict.get(iden):
                    material_data.append(target.obj.object_reader.read_typetree())

            item['materials'] = material_data
            self.data.append(item)
            self.sprites.append(node.children['m_Sprite'])
            self.data_keys.append(node.get_identification())

    def save_data(self, base_path):
        _path = os.path.join(base_path, 'image')
        pathlib.Path(_path).mkdir(exist_ok=True, parents=True)
        for sprite in self.sprites:
            obj = sprite.obj
            save_name = sprite.name + '.png' if not sprite.name.endswith('.png') else sprite.name
            obj.image.save(os.path.join(_path, save_name))
        super().save_data(base_path)

    def clear(self):
        super().clear()
        self.sprites.clear()

