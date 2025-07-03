import numpy as np
import util

from unityResourceNode import UnityResourceNode


class ContainerObject:
    def __init__(self, parent_container):
        self.data = {}
        self.parent_container = parent_container
        self.nodes = {}

    def process(self):
        """
        处理节点
        :return:
        """
        pass

    def test_and_add(self, node: UnityResourceNode):
        """
        检测node是否命中，并在命中时存入
        :param node:
        :return:
        """
        return False


class AudioClips(ContainerObject):

    def __init__(self, parent_container):
        super().__init__(parent_container)

    def process(self):
        for name, node in self.nodes.items():
            self.data[name] = node.obj.m_Length

    def test_and_add(self, node: UnityResourceNode):
        if node.type == 'AudioClip':
            self.nodes[node.get_identification()] = node
            return True
        return False


class Sprite(ContainerObject):
    """
    Sprite资源类型 (更准确地来说，是Sprite引用的图片）
    """

    def __init__(self, parent_container):
        super().__init__(parent_container)

    def process(self):
        for name, node in self.nodes.items():
            self.data[name] = node.obj.m_Length

    def test_and_add(self, node: UnityResourceNode):
        if node.type == 'Sprite':
            self.nodes[node.get_identification()] = node
            return True
        return False


class SpineClips(ContainerObject):

    def process(self):
        audio_clips = self.parent_container[Container.containerObjectType['AudioClips'][0]]
        for name, node in self.nodes.items():
            skeleton_node = node.children['skeletonDataAsset']
            skeleton_name = skeleton_node.children['skeletonJson']
            skeleton_dict = self.data.get(skeleton_name)
            if skeleton_dict is None:
                skeleton_dict = {'defaultMix': skeleton_node.obj.defaultMix, 'scale': skeleton_node.obj.scale,
                                 'clips': {}}
                self.data[skeleton_name] = skeleton_dict
            node_obj = node.obj
            skeleton_dict['clips'][name] = {
                'clipName': node_obj.ClipName,
                'introDelayDuration': node_obj.IntroDelayDuration,
                'introMix': node_obj.IntroMix,
                'outroMix': node_obj.OutroMix,
                'outroStartOffset': node_obj.OutroStartOffset,
                'track': node_obj.Track,
                'useDefaultIntroMix': node_obj.UseDefaultIntroMix == 1,
                'useDefaultOutroMix': node_obj.UseDefaultOutroMix == 1,
                'isTrackMainIdle': node_obj.IsTrackMainIdle,
                'soundKeys': [{
                    'time': i.Time,
                    'audios': [
                        (j.m_name, audio_clips[j.m_name]) for j in i['Event']['AudioData']['AudioClips']
                    ]
                } for i in node_obj.SoundKeys
                ],
            }

    def test_and_add(self, node: UnityResourceNode):
        if hasattr(node.obj, 'ClipName'):
            self.nodes[node.get_identification()] = node
            return True
        return False


class InteractiveConfig(ContainerObject):

    def process(self):

        def fetch_data(item):
            obj = item.obj
            return {
                'offset': obj.BoneCenterOffset,
                'followDragSpeed': obj.FollowDragSpeed01,
                'followReleaseSpeed': obj.FollowReleaseSpeed01,
                'bounds': (obj.MinLocalPos.x, obj.MinLocalPos.y, obj.MaxLocalPos.x, obj.MaxLocalPos.y),
                'initPos': (obj.OrigLocalPos.x, obj.OrigLocalPos.y),
                'delay': obj.TriggerDelay,
                'in': item.children['IngClip'].name,
                'end': item.children['EndClip'].name
            }

        for name, node in self.nodes.items():
            tmp = node.name.endswith('IK')
            test = (lambda item: hasattr(item.obj, 'BoneCenterOffset')) \
                if tmp else (lambda item: item.children.get('spineCharacter') is not None)
            fetch = fetch_data if tmp else lambda: None
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
                elif test(node):
                    node_data['data'] = fetch(node)

            component_node = node.children['m_Transform']
            if component_node.process_data is None:
                transform_stack = [component_node]
                parent_transform = component_node.parent['m_Father']
                transform_matrix = np.eye(4)
                while parent_transform and parent_transform.process_data is None:
                    transform_stack.append(parent_transform)
                    parent_transform = parent_transform.parent.get('m_Father')
                if parent_transform:
                    transform_matrix = parent_transform.process_data
                while len(transform_stack) > 0:
                    transform = transform_stack.pop()
                    transform_matrix = np.dot(transform_matrix, util.compose_transform_matrix(
                        transform.m_LocalPosition, transform.m_LocalRotation, transform.m_LocalScale))
                    transform.process_data = transform_matrix

            node_data['transform_matrix'] = component_node.process_data

            self.data[name] = node_data

    def test_and_add(self, node: UnityResourceNode):
        if node.name == 'BodyTouch' or node.name.endswith('IK') and node.type == 'MonoBehaviour':
            self.nodes[node.get_identification()] = node
            return True
        return False

    # class ViewBoundsConfig(ContainerObject):
    #     pass


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
        for name, node in self.nodes.items():
            data = {}
            # low
            for attr_name, component in node.children.items():
                if attr_name.startswith('components'):
                    return_data = PostProcessing.__process__(component.obj)
                    if return_data is not None:
                        data['attr_name'] = return_data
            if len(data) > 0:
                self.data[name] = data

    def test_and_add(self, node: UnityResourceNode):
        if node.name.startswith('PPPV'):
            self.nodes[node.get_identification()] = node
            return True
        return False


class SpriteRender(ContainerObject):

    def test_and_add(self, node: UnityResourceNode):
        if node.type == 'SpriteRenderer':
            self.nodes[node.get_identification()] = node
            return True
        return False

    def process(self):
        for name, node in self.nodes.items():
            obj = node.obj
            self.data = {
                'sprite': obj.m_Sprite,
                'color': obj.m_Color,
                'flip': (obj.m_FilpX, obj.m_FilpY),
                'material': obj.m_Materials,
                'drawMode': obj.m_DrawMode,
                'sortingLayer': obj.m_SortingLayer,
                'maskInteraction': obj.m_MaskInteraction
            }


class Particle(ContainerObject):

    def process(self):
        for _, node in self.nodes:
            pass

    def test_and_add(self, node: UnityResourceNode):
        if node.type == 'ParticleSystemRender':
            self.nodes[node.get_identification()] = node


class Timeline(ContainerObject):
    """
    总的那个时间线
    """

    def test_and_add(self, node: UnityResourceNode):
        if node.name.endswith('_TimeLine'):
            pass


class Container:
    containerObjectType = {
        'AudioClips': (0, AudioClips),
        'Sprites': (1,),
        'SpineClips': (2, SpineClips),
        'InteractiveConfig': (3, InteractiveConfig),
        # 'ViewBoundsConfig': (3, ViewBoundsConfig),
        'PostProcessing': (4, PostProcessing),
        'SpriteRender': (5, SpriteRender),
        'Particle': (6, Particle),
        'Timeline': (7, Timeline)
    }

    def __init__(self, student_name):
        self.name = student_name
        self.container_objects = (AudioClips(self), Sprite(self), SpineClips(self), InteractiveConfig(self),
                                  PostProcessing(self), SpriteRender(self), Particle(self), Timeline(self))
