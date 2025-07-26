import util
from containerObjects.ContainerObject import ContainerObject


class PostProcessing(ContainerObject):
    #  color adjustment
    color_filter = (0, 0, 0, 1)
    contrast = 0
    hue_shift = 0
    post_exposure = 0
    saturation = 0

    #  chromatic aberration
    intensity = 0

    #  lift gamma gain
    lift = (0, 0, 0, .02)
    gamma = (1, 1, 1, .02)
    gain = (1, 1, 1, .02)

    @staticmethod
    def __process__(obj):
        if obj.m_Name == 'ColorAdjustments':
            return {'colorFilter': PostProcessing.color_filter if obj.colorFilter.m_OverrideState == 0
            else util.to_tuple(obj.colorFilter.m_Value),
                    'contrast': PostProcessing.contrast if obj.contrast.m_OverrideState == 0
                    else obj.contrast.m_Value,
                    'hueShift': PostProcessing.hue_shift if obj.hueShift.m_OverrideState == 0
                    else obj.hueShift.m_Value,
                    'postExposure': PostProcessing.post_exposure if obj.postExposure.m_OverrideState == 0
                    else obj.postExposure.m_Value,
                    'saturation': PostProcessing.saturation if obj.saturation.m_OverrideState == 0
                    else obj.saturation.m_Value}

        elif obj.m_Name == 'ChromaticAberration':
            return {'intensity': PostProcessing.intensity if obj.intensity.m_OverrideState == 0
            else obj.intensity.m_Value}

        elif obj.m_Name == 'LiftGammaGain':
            return {'lift': PostProcessing.lift if obj.lift.m_OverrideState == 0
            else util.to_tuple(obj.lift.m_Value),
                    'gamma': PostProcessing.gamma if obj.gamma.m_OverrideState == 0
                    else util.to_tuple(obj.gamma.m_Value),
                    'gain': PostProcessing.gain if obj.gain.m_OverrideState == 0
                    else util.to_tuple(obj.gain.m_Value)}
        return None

    def process(self):
        game_object_container = self.parent_container.container_objects['GameObject']
        for identification, node in self.nodes.items():
            data = {}
            for attr_name, component in node.children.items():
                if attr_name.startswith('components'):
                    return_data = PostProcessing.__process__(component.obj)
                    if return_data is not None:
                        data[attr_name] = return_data

                        data['gameObject'] = game_object_container.get_index(
                            node.parents['sharedProfile'].children['m_GameObject'].get_identification()
                        )

            if len(data) > 0:
                self.data.append(data)
                self.data_keys.append(identification)

    def test_and_add(self, node):
        if node.name.startswith('PPPV'):
            self.nodes[node.get_identification()] = node
            return True
        return False
