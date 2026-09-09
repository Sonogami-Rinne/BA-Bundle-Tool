import numpy as np

import util
from containerObjects.ContainerObject import ContainerObject
from typeId import ClassIDType
from util import to_tuple


class InteractionConfig(ContainerObject):

    def fetch_data(self, item):
        spine_container = self.parent_container.container_objects['SpineClips']
        game_object_container = self.parent_container.container_objects['GameObject']
        obj = item.obj
        bone = item.children['Bone'].game_object
        # bone_transform = util.get_transform(bone)
        # bone_translate, bone_theta, _ = util.decompose_2d_transform(bone_transform)
        result = {
            # 'offset': to_tuple(obj.BoneCenterOffset),
            'followDragSpeed': obj.FollowDragSpeed01,
            'followReleaseSpeed': obj.FollowReleaseSpeed01,
            # 'bounds': (obj.MinLocalPos.x, obj.MinLocalPos.y, obj.MaxLocalPos.x, obj.MaxLocalPos.y),
            # 'initPos': (obj.OrigLocalPos.x, obj.OrigLocalPos.y),
            'delay': obj.TriggerDelay,
            'bounds': {
                'minLocalX': round(obj.MinLocalPos.y, 4),
                'minLocalY': round(obj.MinLocalPos.x, 4),
                'maxLocalX': round(obj.MaxLocalPos.y, 4),
                'maxLocalY': round(obj.MaxLocalPos.x, 4),
            },
            'initPos': {
                'x': round(obj.OrigLocalPos.y, 4),
                'y': round(obj.OrigLocalPos.x, 4),
            },
            'bone': {
                'name': bone.name,
                'gameObject': game_object_container.get_index(bone.get_identification()),
                # 'translate': bone_translate,
                # 'theta': bone_theta
            }
            # 'bone': (bone.name, game_object_container.get_index(bone.get_identification()), bone_translate)
        }
        if _in := item.children.get('IngClip'):
            result['in'] = spine_container.get_index(_in.get_identification())
        else:
            util.CLogging.error('IngClip missing !')

        if _out := item.children.get('EndClip'):
            result['end'] = spine_container.get_index(_out.get_identification())
        else:
            util.CLogging.error('EndClip missing !')

        return result

    def process(self):
        game_object_container = self.parent_container.container_objects['GameObject']

        for identification, node in self.nodes.items():
            node_data = {}
            
            _base_transform = util.get_transform(node)
            translate, rotation, scale = util.decompose_2d_transform(_base_transform)
            for _, component_data in node.children.items():
                component_obj = component_data.obj

                if component_data.type == ClassIDType.BoxCollider:
                    obj = component_data.obj
                    #m_Size, m_Center
                    node_data['collider'] = {
                        'X': obj.m_Center.x + translate[0],
                        'Y': obj.m_Center.y + translate[1],
                        'scaleX': scale[0],
                        'scaleY': scale[1],
                        'halfWidth': obj.m_Size.x / 2,
                        'halfHeight': obj.m_Size.y / 2,
                        'theta': rotation
                    }

                elif hasattr(component_obj, 'IngClip'):
                    node_data['data'] = self.fetch_data(component_data)

            node_data['name'] = node.name

            # 对于timeline里面对属性的修改，没办法保证是哪个的enable或者active,只能手动重定向了,因此先记录这个gameObject
            node_data['gameObject'] = game_object_container.get_index(node.get_identification())
            self.data_keys.append(identification)
            self.data.append(node_data)

    def test_and_add(self, node):
        if node.name == 'BodyTouch' or node.type == ClassIDType.GameObject and (node.name.endswith('IK')):
            self.nodes[node.get_identification()] = node
            return True
        return False
