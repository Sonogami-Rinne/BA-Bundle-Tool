import util
from containerObjects.ContainerObject import ContainerObject
from typeId import ClassIDType
from util import to_tuple


class InteractiveConfig(ContainerObject):

    def fetch_data(self, item):
        spine_container = self.parent_container.container_objects['SpineClips']
        obj = item.obj
        result = {
            'offset': to_tuple(obj.BoneCenterOffset),
            'followDragSpeed': obj.FollowDragSpeed01,
            'followReleaseSpeed': obj.FollowReleaseSpeed01,
            'bounds': (obj.MinLocalPos.x, obj.MinLocalPos.y, obj.MaxLocalPos.x, obj.MaxLocalPos.y),
            'initPos': (obj.OrigLocalPos.x, obj.OrigLocalPos.y),
            'delay': obj.TriggerDelay,
        }
        if _in := item.children.get('IngClip'):
            result['in'] = spine_container.get_index(_in.get_identification())
        else:
            util.CLogging.error('IngClip missing !')

        if _out := item.children.get('EndClip'):
            result['end'] = spine_container.get_index(_out.get_identification())
        else:
            util.CLogging.error('EndClip missing !')
        # return {
        #     'offset': to_tuple(obj.BoneCenterOffset),
        #     'followDragSpeed': obj.FollowDragSpeed01,
        #     'followReleaseSpeed': obj.FollowReleaseSpeed01,
        #     'bounds': (obj.MinLocalPos.x, obj.MinLocalPos.y, obj.MaxLocalPos.x, obj.MaxLocalPos.y),
        #     'initPos': (obj.OrigLocalPos.x, obj.OrigLocalPos.y),
        #     'delay': obj.TriggerDelay,
        #     # 'in': item.children['IngClip'].get_identification(),
        #     # 'end': item.children['EndClip'].get_identification()
        #     # 'in': spine_container.get_index(item.children['IngClip'].get_identification()),
        #     # 'end': spine_container.get_index(item.children['EndClip'].get_identification())
        # }
        return result

    def process(self):
        game_object_container = self.parent_container.container_objects['GameObject']

        for identification, node in self.nodes.items():
            node_data = {}
            for _, component_data in node.children.items():
                component_obj = component_data.obj
                if component_data.type == ClassIDType.BoxCollider:
                    node_data['collider'] = {
                        'offset': to_tuple(component_obj.m_Center),
                        'size': (component_obj.m_Size.x, component_obj.m_Size.y)
                    }
                elif hasattr(component_obj, 'IngClip'):
                    node_data['data'] = self.fetch_data(component_data)

            # node_data['transform_matrix'] = util.get_transform(node).tolist()
            translate, rotation, scale = util.decompose_2d_transform(util.get_transform(node))
            node_data['transform'] = {
                'translate': translate,
                'rotation': rotation,
                'scale': scale
            }
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

