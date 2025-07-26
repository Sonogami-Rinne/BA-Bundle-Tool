import util
from containerObjects.ContainerObject import ContainerObject
from typeId import ClassIDType


class SpriteRender(ContainerObject):

    def test_and_add(self, node):
        if node.type == ClassIDType.SpriteRenderer:
            self.nodes[node.get_identification()] = node
            return True
        return False

    def process(self):
        game_object_container = self.parent_container.container_objects['GameObject']
        for _, node in self.nodes.items():
            obj = node.obj

            self.data.append({
                'sprite': node.children['m_Sprite'],
                'color': obj.m_Color,
                'flip': (obj.m_FlipX, obj.m_FlipY),
                'material': obj.m_Materials,
                'drawMode': obj.m_DrawMode,
                'sortingLayer': obj.m_SortingLayer,
                'maskInteraction': obj.m_MaskInteraction,
                'transform': util.get_transform(node.children['m_GameObject']),
                'gameObject': game_object_container.get_index(node.children['m_GameObject'].get_identification())
            })
            self.data_keys.append(node.get_identification())
