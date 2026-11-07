import util
from containerObjects.ContainerObject import ContainerObject


class PostProcessing(ContainerObject):
    # Keep Unity's raw trackballs (including w) and override flags. The runtime
    # blends the Volume stack before converting its values for the shader.
    parameters = {
        'ColorAdjustments': ('colorFilter', 'contrast', 'hueShift', 'postExposure', 'saturation'),
        'ChromaticAberration': ('intensity',),
        'LiftGammaGain': ('lift', 'gamma', 'gain'),
    }
    vectors = {'colorFilter', 'lift', 'gamma', 'gain'}

    @staticmethod
    def __process__(obj):
        fields = PostProcessing.parameters.get(obj.m_Name)
        if fields is None or not getattr(obj, 'active', True):
            return None
        data = {}
        for name in fields:
            parameter = getattr(obj, name)
            if parameter.m_OverrideState:
                data[name] = (util.to_tuple(parameter.m_Value)
                              if name in PostProcessing.vectors else parameter.m_Value)
        return data

    def process(self):
        game_object_container = self.parent.container_objects['GameObject']
        # References are linked after test_and_add runs, so resolve the script
        # here as well instead of relying on the asset's name prefix.
        for identification, candidate in getattr(self.parent, 'nodes_dict', {}).items():
            script = candidate.children.get('m_Script')
            if (script is not None
                    and getattr(script.obj, 'm_ClassName', None) == 'VolumeProfile'
                    and getattr(script.obj, 'm_Namespace', None) == 'UnityEngine.Rendering'):
                self.nodes[identification] = candidate
        for identification, node in self.nodes.items():
            parameters = {}
            for name, component in node.children.items():
                if name.startswith('components'):
                    values = self.__process__(component.obj)
                    if values:
                        parameters.update(values)

            # A profile may be shared by several Volumes; export each owner.
            for name, volume in node.parents:
                if name != 'sharedProfile':
                    continue
                game_object = volume.children['m_GameObject']
                game_object_container.register_game_object(game_object)
                index = game_object_container.get_index(game_object.get_identification())
                self.data.append({
                    **parameters,
                    'schemaVersion': 2,
                    'overrides': list(parameters),
                    'gameObject': index,
                    'enabled': bool(volume.obj.m_Enabled),
                    'active': bool(game_object.obj.m_IsActive),
                    'weight': float(volume.obj.weight),
                    'priority': float(volume.obj.priority),
                    'isGlobal': bool(volume.obj.m_IsGlobal),
                })
                self.data_keys.append(identification)

    def test_and_add(self, node):
        script = node.children.get('m_Script')
        if ((script is not None and getattr(script.obj, 'm_ClassName', None) == 'VolumeProfile')
                or node.name.startswith('PPPV')):
            self.nodes[node.get_identification()] = node
            return True
        return False
