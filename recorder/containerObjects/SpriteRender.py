import util
from recorder.containerObjects.ContainerObject import ContainerObject


class SpriteRender(ContainerObject):

    def test_and_add(self, node):
        if node.type == 'SpriteRenderer':
            self.nodes[node.get_identification()] = node
            return True
        return False

    def process(self):
        for identification, node in self.nodes.items():
            obj = node.obj

            self.data.append({
                'sprite': node.children['m_Sprite'],
                'color': obj.m_Color,
                'flip': (obj.m_FlipX, obj.m_FlipY),
                'material': obj.m_Materials,
                'drawMode': obj.m_DrawMode,
                'sortingLayer': obj.m_SortingLayer,
                'maskInteraction': obj.m_MaskInteraction,
                'transform': util.get_transform(node.children['m_GameObject'])
            })
            self.data_keys.append(identification)
