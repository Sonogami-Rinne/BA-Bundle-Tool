import util
from containerObjects.ContainerObject import ContainerObject
# from container import Container


class InteractiveConfig(ContainerObject):

    def fetch_data(self, item):
        spine_container = self.parent_container.container_objects[1]  # SpineClips
        obj = item.obj
        return {
            'offset': obj.BoneCenterOffset,
            'followDragSpeed': obj.FollowDragSpeed01,
            'followReleaseSpeed': obj.FollowReleaseSpeed01,
            'bounds': (obj.MinLocalPos.x, obj.MinLocalPos.y, obj.MaxLocalPos.x, obj.MaxLocalPos.y),
            'initPos': (obj.OrigLocalPos.x, obj.OrigLocalPos.y),
            'delay': obj.TriggerDelay,
            # 'in': item.children['IngClip'].get_identification(),
            # 'end': item.children['EndClip'].get_identification()
            'in': spine_container.get_index(item.children['IngClip'].get_identification()),
            'end': spine_container.get_index(item.children['EndClip'].get_identification())
        }

    def process(self):

        for identification, node in self.nodes.items():
            node_data = {}
            for attr_name, component_data in node.children.items():
                if not attr_name.startswith('m_Components'):
                    continue
                if component_data.type == 'BoxCollider':
                    component_obj = component_data.obj
                    node_data['collider'] = {
                        'offset': component_obj.m_Center,
                        'size': (component_obj.m_Size.x, component_obj.m_Size.y)
                    }
                elif node.name.endswith('IK'):
                    node_data['data'] = self.fetch_data(node)

            node_data['transform_matrix'] = util.get_transform(node)
            node_data['name'] = node.name
            node_data['gameObject'] = node.get_identification()  # 对于timeline里面对属性的修改，没办法保证是哪个的enable或者active,只能手动重定向了,因此先记录这个gameObject
            self.data_keys.append(identification)
            self.data.append(node_data)

    def test_and_add(self, node):
        if node.name == 'BodyTouch' or (node.name.endswith('IK') and node.type == 'GameObject'):
            self.nodes[node.get_identification()] = node
            return True
        return False

    # def save_data(self, base_path):
    #     base_path.mkdir(parents=True, exist_ok=True)
    #     with open(os.path.join(base_path, "interactive.json"), 'w+', encoding='utf-8') as f:
    #         json.dump(self.data, f, indent=2)
