import io
import logging
import math
import os.path
import struct

import numpy as np
import util


# from unityResourceNode import UnityResourceNode


class ContainerObject:
    def __init__(self, parent_container):
        self.data = []
        self.data_keys = []
        self.parent_container = parent_container
        self.nodes = {}

    def process(self):
        """
        处理节点
        :return:
        """
        pass

    def test_and_add(self, node):
        """
        检测node是否命中，并在命中时存入
        :param node:
        :return:
        """
        return False

    def save_data(self, folder):
        """
        保存文件
        :param folder:
        :return:
        """

    def get_index(self, identification):
        return self.data_keys.index(identification)


class GameObject(ContainerObject):
    """
    仅用于hash的，不存储
    """

    def test_and_add(self, node):
        if node.type == 'GameObject':
            self.nodes[util.compute_unity_hash(node.hierarchy_path)] = node
            return True
        return False

    def save_data(self, folder):
        pass

    def get_path(self, path_hash):
        return self.nodes[path_hash]


class SpineClips(ContainerObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.clip_keys = []
        self.skeleton_keys = []
        self.data = {
            'skeletons': [],
            'clips': [],
        }

    def process(self):
        nodes_dict = self.parent_container.nodes_dict
        for _, node in self.nodes.items():
            skeleton_node = node.children['skeletonDataAsset']
            skeleton_name = skeleton_node.children['skeletonJSON'].name
            # if (skeleton_index := self.skeleton_keys.index(skeleton_name)) < 0:
            if skeleton_name not in self.skeleton_keys:
                skeleton_index = len(self.skeleton_keys)
                self.skeleton_keys.append(skeleton_name)
                self.data['skeletons'].append({
                    'defaultMix': skeleton_node.obj.defaultMix,
                    'scale': skeleton_node.obj.scale
                })
            else:
                skeleton_index = self.skeleton_keys.index(skeleton_name)

            node_obj = node.obj
            tmp = {
                'skeleton': skeleton_index,
                'clipName': node_obj.ClipName,
                'introDelayDuration': node_obj.IntroDelayDuration,
                'introMix': node_obj.IntroMix,
                'outroMix': node_obj.OutroMix,
                'outroStartOffset': node_obj.OutroStartOffset,
                'track': node_obj.Track,  # Track为负数的话，播完就隐藏当前spine对象
                'useDefaultIntroMix': node_obj.UseDefaultIntroMix == 1,
                'useDefaultOutroMix': node_obj.UseDefaultOutroMix == 1,
                'isTrackMainIdle': node_obj.IsTrackMainIdle,
                'syncPlays': [
                    node.children[i].get_identification() for i in
                    list(filter(lambda x: x.startswith('Sync'), node.children.keys()))
                ]
            }
            sound_keys = []
            for i in node_obj.SoundKeys:
                target = i.Event
                file_id = target.m_FileID
                identification = (node.cab if file_id == 0 else node.dependencies[file_id - 1]) + str(target.m_PathID)
                target = nodes_dict[identification].obj
                sound_keys.append({
                    'time': i.Time,
                    'audio': target
                })
            tmp['soundKeys'] = sound_keys
            self.clip_keys.append(node.get_identification())
            self.data['clips'].append(tmp)

        for clip in self.data['clips']:
            if (length := len(clip['syncPlays'])) > 0:
                for i in range(length):
                    clip['syncPlays'][i] = self.clip_keys.index(clip['syncPlays'][i])

    def test_and_add(self, node):
        if hasattr(node.obj, 'ClipName'):
            self.nodes[node.get_identification()] = node
            return True
        return False

    def get_index(self, identification):
        return self.clip_keys.index(identification)


class InteractiveConfig(ContainerObject):

    def fetch_data(self, item):
        spine_container = self.parent_container.container_objects[Container.containerObjectType['SpineClips'][0]]
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
            tmp = node.name.endswith('IK')
            test = (lambda item: hasattr(item.obj, 'BoneCenterOffset')) \
                if tmp else (lambda item: item.children.get('spineCharacter') is not None)
            fetch = InteractiveConfig.fetch_data if tmp else lambda x: None
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

            node_data['transform_matrix'] = util.get_transform(node)
            self.data_keys.append(identification)
            self.data.append(node_data)

    def test_and_add(self, node):
        if node.name == 'BodyTouch' or (node.name.endswith('IK') and node.type == 'GameObject'):
            self.nodes[node.get_identification()] = node
            return True
        return False


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
        for identification, node in self.nodes.items():
            data = {}
            # low
            for attr_name, component in node.children.items():
                if attr_name.startswith('components'):
                    return_data = PostProcessing.__process__(component.obj)
                    if return_data is not None:
                        data['attr_name'] = return_data
            if len(data) > 0:
                self.data.append(data)
                self.data_keys.append(identification)

    def test_and_add(self, node):
        if node.name.startswith('PPPV'):
            self.nodes[node.get_identification()] = node
            return True
        return False


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


class Particle(ContainerObject):
    shape_process = (
        lambda obj: {  # sphere, hemisphere
            'radius': obj.radius,
            'radiusThickness': obj.radiusThickness  # 发射粒子的体积比例。值为 0 表示从形状的外表面发射粒子。值为 1 表示从整个体积发射粒子。介于两者之间的值将使用体积的一定比例。
        },
        lambda obj: {  # cone
            'angle': obj.angle,
            'radius': obj.radius.value,
            'radiusThickness': obj.radiusThickness,
            'arc': obj.arc.value,
            'arcMode': obj.arc.mode,
            'speed': obj.arc.speed,
            'spread': Particle.process_min_max_curve(obj.arc.spread),
            'length': obj.length
        },
        # lambda obj: {  # box
        #     'emitterFrom': obj.placementMode  # _Edge_, _Shell_, Volume
        # },
        lambda obj: {  # mesh, meshRenderer, skinnedMeshRenderer
            'mesh': obj.m_Mesh,
            'meshRenderer': obj.m_MeshRenderer,
            'skinnedMeshRenderer': obj.m_SkinnedMeshRenderer
        },
        lambda obj: {  # circle
            'radius': obj.radius.value,
            'radiusThickness': obj.radiusThickness,
            'arc': obj.arc.value,
            'arcMode': obj.arc.mode,
            'speed': obj.arc.speed,
            'spread': Particle.process_min_max_curve(obj.arc.spread)
        },
        lambda obj: {  # edge
            'radius': obj.radius.value,
            'radiusMode': obj.radius.mode,
            'speed': Particle.process_min_max_curve(obj.radius.speed),
            'spread': obj.radius.spread
        },
        lambda obj: {  # donut
            'radius': obj.radius.value,
            'donutRadius': obj.donutRadius,
            'radiusMode': obj.radius.mode,
            'speed': Particle.process_min_max_curve(obj.radius.speed),
            'spread': obj.radius.spread
        },
        # lambda obj: {  # rectangle
        #     ''
        # },
        lambda obj: {  # sprite
            'sprite': obj.m_Sprite,
            'spriteRenderer': obj.m_SpriteRenderer,
        }
    )

    @staticmethod
    def process_gradient(obj):
        data = {
            'atime': [],
            'ctime': [],
            'key': [],
            'mode': obj.m_Mode,
            'alphaKeys': obj.m_NumAlphaKeys,
            'colorKeys': obj.m_NumColorKeys
        }
        for i in range(0, 7):
            data['atime'].append(getattr(obj, f'atime{i}'))
            data['ctime'].append(getattr(obj, f'ctime{i}'))
            data['key'].append(util.to_tuple(getattr(obj, f'key{i}')))
        return data

    @staticmethod
    def process_min_max_gradient(obj):
        return {
            'maxColor': util.to_tuple(obj.maxColor),
            'minColor': util.to_tuple(obj.minColor),
            'maxGradient': Particle.process_gradient(obj.maxGradient),
            'minGradient': Particle.process_gradient(obj.minGradient)
        }

    @staticmethod
    def process_animation_curve(obj):
        target = obj.m_Curve
        return [
            {
                'inSlope': i.inSlope,
                'outSlope': i.outSlope,
                'inWeight': i.inWeight,
                'outWeight': i.outWeight,
                'time': i.time,
                'value': i.value,
                'weightMode': i.weightedMode
            } for i in target
        ]

    @staticmethod
    def process_min_max_curve(obj):
        return {
            'maxCurve': Particle.process_animation_curve(obj.maxCurve),
            'minCurve': Particle.process_animation_curve(obj.minCurve),
            'minMaxState': obj.minMaxState,
            'minScaler': obj.minScalar,
            'scaler': obj.scalar
        }

    @staticmethod
    def process_particle_system(obj):
        data = {}
        #  忽略的模块
        for module_name in ('CollisionModule', 'CustomDataModule', 'ExternalForcesModule', 'ForceModule',
                            'InheritVelocityModule', 'LightsModule', 'SubModule', 'TrailModule', 'TriggerModule',
                            'UVModule'):
            sub_module = getattr(obj, module_name)
            if sub_module.enabled:
                util.CLogging.warn(f'Ignored module {module_name}')

        #  颜色随速度变化模块
        sub_module = obj.ColorBySpeedModule
        if sub_module.enabled:
            data['colorBySpeedModule'] = {
                'gradient': Particle.process_min_max_gradient(sub_module.gradient),
                'range': util.to_tuple(sub_module.range)
            }

        #  颜色模块
        sub_module = obj.ColorModule
        if sub_module.enabled:
            data['colorModule'] = Particle.process_min_max_gradient(sub_module.gradient)

        #  发射器模块
        sub_module = obj.EmissionModule
        data['emissionModule'] = {
            'rateOverDistance': Particle.process_min_max_curve(sub_module.rateOverDistance),  # 每个移动单位发射的粒子数量
            'rateOverTime': Particle.process_min_max_curve(sub_module.rateOverTime),  # 每个时间单位发射的粒子数量
            'bursts': [
                {
                    'count': Particle.process_min_max_curve(i.countCurve),  # 不知道那个maxCount和minCount是否为unitypy自动生成的
                    'cycles': i.cycleCount,  # 该burst的次数
                    'probability': i.probability,
                    'interval': i.repeatInterval,  # 每个burst之间的间隔
                    'delay': i.time  # 开始到第一次burst的时间
                } for i in sub_module.m_Bursts
            ]
        }

        #  初始化模块
        sub_module = obj.InitialModule
        data['initialModule'] = {
            'emitterVelocity': util.to_tuple(sub_module.customEmitterVelocity),
            'maxNum': sub_module.maxNumParticles,
            'startColor': Particle.process_min_max_gradient(sub_module.startColor),
            'startLifeTime': Particle.process_min_max_curve(sub_module.startLifetime),
            'rotation3D': sub_module.rotation3D,
            'startRotationX': Particle.process_min_max_curve(sub_module.startRotationX),
            'startRotationY': Particle.process_min_max_curve(sub_module.startRotationY),
            'startRotation': Particle.process_min_max_curve(sub_module.startRotation),
            'size3D': sub_module.size3D,
            'startSizeY': Particle.process_min_max_curve(sub_module.startSizeY),
            'startSizeZ': Particle.process_min_max_curve(sub_module.startSizeZ),
            'startSize': Particle.process_min_max_curve(sub_module.startSize),
            'startSpeed': Particle.process_min_max_curve(sub_module.startSize),
            'duration': obj.lengthInSec,  # 粒子系统的时长。不知道为什么，这个东西放在粒子系统的根部分，而不是模块内
            'loop': obj.looping,
            'playOnAwake': obj.playOnAwake,  # 在创建对象后自动启动
            'randomSeed': obj.randomSeed,
            'autoRandomSeed': obj.autoRandomSeed,
            'prewarm': obj.prewarm,
            'scalingMode': obj.scalingMode,  # hierarchy, local(忽略父级的Transform的scale), shape(仅改变发射区域，不改变粒子大小)
            'simulationSpeed': obj.simulationSpeed,  # 更新速度
            'delay': Particle.process_min_max_curve(obj.startDelay)  # 从创建到第一次发射的时间
        }

        #  生命随速度变换模块
        sub_module = obj.LifetimeByEmitterSpeedModule
        if sub_module.enabled:
            data['lifetimeByEmitterSpeedModule'] = {
                'curve': Particle.process_min_max_curve(sub_module.m_Curve),
                'range': util.to_tuple(sub_module.m_Range)
            }

        #  柏林噪音
        sub_module = obj.NoiseModule
        if sub_module.enabled:
            data['noise'] = {
                'damping': sub_module.damping,  # 启用此属性后，强度与频率成正比。将这些值绑在一起意味着可在保持相同行为但具有不同大小的同时缩放噪声场。
                'frequency': sub_module.frequency,
                'octaveMultiplier': sub_module.octaveMultiplier,  # 强度逐层变化
                'octaveScale': sub_module.octaveScale,  # 频率逐层变化
                'octaves': sub_module.octaves,  # 叠几层
                'positionAmount': sub_module.positionAmount,  # 噪音对粒子位置影响程度的乘数
                # 'quality': sub_module.quality,  # 质量。固定2维
                'remapEnabled': sub_module.remapEnabled,  # 是否将数值重映射
                'remapY': Particle.process_min_max_curve(sub_module.remapY),
                'remapZ': Particle.process_min_max_curve(sub_module.remapZ),
                'remap': Particle.process_min_max_curve(sub_module.remap),
                'rotationAmount': sub_module.rotationAmount,  # 类似,
                'scrollSpeed': Particle.process_min_max_curve(sub_module.scrollSpeed),  # 随着时间的推移而移动噪声场可产生更不可预测和不稳定的粒子移动
                'separateAxis': sub_module.separateAxes,  # 在每个轴上独立控制强度和重新映射
                'sizeAmount': Particle.process_min_max_curve(sub_module.sizeAmount),  # 类似
                'strengthY': Particle.process_min_max_curve(sub_module.strengthY),
                'strengthZ': Particle.process_min_max_curve(sub_module.strengthZ),
                'strength': Particle.process_min_max_curve(sub_module.strength),
                # 噪声在粒子的生命周期内对粒子的影响有多强,猜测这个为基本影响参数，再分别乘上那三个
            }

        #  旋转随速度变化,以度为单位
        sub_module = obj.RotationBySpeedModule
        if sub_module.enabled:
            data['rotationBySpeedModule'] = {
                'curve': Particle.process_min_max_curve(sub_module.curve),
                'range': util.to_tuple(sub_module.range),
                'separateAxis': sub_module.separateAxes,
                'curveX': Particle.process_min_max_curve(sub_module.x),
                'curveY': Particle.process_min_max_curve(sub_module.y),
            }

        #  旋转模块,以度为单位
        sub_module = obj.RotationModule
        if sub_module.enabled:
            data['rotationModule'] = {
                'curve': Particle.process_min_max_curve(sub_module.curve),
                'separateAxes': sub_module.separateAxes,
                'curveX': Particle.process_min_max_curve(sub_module.x),
                'curvey': Particle.process_min_max_curve(sub_module.y),
            }

        #  形状模块（粒子生成区域）
        sub_module = obj.ShapeModule
        shape = sub_module.type
        data['shapeModule'] = {
            'shape': shape,
            #  这些是忽略的部分

            # 'texture': sub_module.m_Texture,
            # 'clipChannel': sub_module.m_TextureClipChannel,
            # 'clipThreshold': sub_module.m_TextureClipThreshold,
            # 'colorAffectsParticles': sub_module.m_TextureColorAffectsParticles,
            # 'alphaAffectsParticles': sub_module.m_TextureAlphaAffectsParticles,
            # 'bilinearFiltering': sub_module.BilinearFiltering,
            # 'alignToDirection': sub_module.alignToDirection,
            'position': util.to_tuple(sub_module.m_Position),
            'rotation': util.to_tuple(sub_module.m_Rotation),
            'scale': util.to_tuple(sub_module.m_Scale),
            'randomizeDirectionAmount': sub_module.randomDirectionAmount,  # 随机方向乘这个和1-这个乘原本方向混合
            'randomizePositionAmount': sub_module.randomPositionAmount,
            'sphericalDirectionAmount': sub_module.sphericalDirectionAmount  # 球面方向混合
        }
        """
        Sphere-0, HemiSphere-1, Cone-2, Box-3, Mesh-4, ConeVolume-5, Circle-6, SingleSideEdge-7, MeshRenderer-8, 
        SkinnedMeshRenderer-9, BoxShell-10, BoxEdge-11, Donut-12, Rectangle-13, Sprite-14, SpriteRenderer-15
        """
        """
        Sphere, Cone, Mesh, Circle, Edge, Donut, Sprite
        """
        if shape == 0:  # Sphere
            data.update(Particle.shape_process[shape](sub_module))
        elif shape <= 2:  # HemiSphere, Cone, Box, Mesh
            data.update(Particle.shape_process[shape - 1](sub_module))
        elif shape == 4:
            data.update(Particle.shape_process[2](sub_module))
        elif shape == 5:
            data.update(Particle.shape_process[2](sub_module))
        elif shape <= 7:
            data.update(Particle.shape_process[shape - 3](sub_module))
        elif shape <= 9:
            data.update(Particle.shape_process[2](sub_module))
        elif shape == 12:
            data.update(Particle.shape_process[5](sub_module))
        elif shape >= 14:
            data.update(Particle.shape_process[6](sub_module))

        #  旋转随速度变化,以度为单位
        sub_module = obj.SizeBySpeedModule
        if sub_module.enabled:
            data['sizeBySpeedModule'] = {
                'curve': Particle.process_min_max_curve(sub_module.curve),
                'range': util.to_tuple(sub_module.range),
                'separateAxis': sub_module.separateAxes,
                'curveY': Particle.process_min_max_curve(sub_module.y),
                'curveZ': Particle.process_min_max_curve(sub_module.z),
            }

        #  缩放模块
        sub_module = obj.SizeModule
        if sub_module.enabled:
            data['sizeModule'] = {
                'curve': Particle.process_min_max_curve(sub_module.curve),
                'separateAxes': sub_module.separateAxes,
                'curveY': Particle.process_min_max_curve(sub_module.y),
                'curveZ': Particle.process_min_max_curve(sub_module.z),
            }

        #  速度模块
        sub_module = obj.VelocityModule
        if sub_module.enabled:
            data['velocityModule'] = {
                'x': sub_module.x,
                'y': sub_module.y,
                'z': sub_module.z,
                'orbitalX': sub_module.orbitalX,
                'orbitalY': sub_module.orbitalY,
                'orbitalZ': sub_module.orbitalZ,
                'offsetX': sub_module.orbitalOffsetX,
                'offsetY': sub_module.orbitalOffsetY,
                'offsetZ': sub_module.orbitalOffsetZ,
                'radial': sub_module.radial,
                'speedModifier': sub_module.speedModifier,
            }

        #  速度限制模块
        sub_module = obj.ClampVelocityModule
        if sub_module.enabled:
            data['clampVelocityModule'] = {
                'damp': sub_module.dampen,
                'drag': Particle.process_min_max_curve(sub_module.drag),
                'magnitude': Particle.process_min_max_curve(sub_module.magnitude),
                'multiplyDragByParticleSize': sub_module.multuplyDragByParticleSize,
                'multiplyDragByParticleVelocity': sub_module.multuplyDragByParticleVelocity,
                'separateAxis': sub_module.separateAxis,
                'curveX': Particle.process_min_max_curve(sub_module.x),
                'curveY': Particle.process_min_max_curve(sub_module.y),
                'curveZ': Particle.process_min_max_curve(sub_module.z),
            }

        return data

    @staticmethod
    def process_particle_renderer(obj):
        return {
            'renderMode': obj.m_RenderMode,  # BillBoard, Stretch, HorizontalBillBoard, VerticalBillBoard, Mesh, None
            'materials': obj.m_Materials,
            'minParticleSize': obj.m_MinParticleSize,
            'maxParticleSize': obj.m_MaxParticleSize,
            'flip': util.to_tuple(obj.m_Flip),
            'pivot': util.to_tuple(obj.m_Pivot),
            'meshes': [
                obj.m_Mesh,
                obj.m_Mesh1,
                obj.m_Mesh2,
                obj.m_Mesh3
            ]
        }

    def process(self):
        for _, node in self.nodes.items():
            #  先是ParticleSystem
            obj = node.obj
            data = Particle.process_particle_system(obj)
            parent = node.children['m_GameObject']
            for _, _node in parent.children.items():
                if _node.type == 'ParticleSystemRenderer':
                    obj = _node.obj
                    break
            data['rendererModule'] = Particle.process_particle_renderer(obj)
            #  self.data[parent.get_identification()] = data
            self.data.append(data)
            self.data_keys.append(parent.get_identification())

    def test_and_add(self, node):
        if node.type == 'ParticleSystem':
            self.nodes[node.get_identification()] = node


class Timeline(ContainerObject):
    """
    总的那个时间线
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.data = {
            'animationClip': [],
            'soundFix': [],
            'spineAnimation': []
        }
        self.nodes = []

    def process_generic_bindings(self, generic_bindings, node, game_object_container):
        """
        :param game_object_container:
        :param generic_bindings:
        :param node:
        :return: list[{'node','property','isPPtrCurve','curve'}]
        """
        info_json_manager = self.parent_container.info_json_manager
        game_object_dict = self.parent_container.container_objects[Container.containerObjectType['GameObject'][0]]
        nodes_dict = self.parent_container.nodes_dict
        dependencies = node.dependencies
        generics = generic_bindings.genericBindings
        bindings = []
        for item in generics:
            script = item.script
            data = {}

            type_name = util.InfoJsonManger.get_class_type(item.typeID)
            if (path_id := script.m_PathID) != 0:  # 直接根据pathID, fileID得到对应对象
                file_id = script.m_FileID
                identification = (node.cab if file_id == 0 else dependencies[file_id - 1]) + str(path_id)
                data['node'] = nodes_dict[identification]
            else:
                #  path = info_json_manager.get_path(item['path'])

                #  path = game_object_container.get_path(item.path)
                path = game_object_dict.get_path(item.path)
                data = {}
                for node in path.children.values():
                    if node.type == type_name:
                        data['node'] = node
                        break

            if (tmp := info_json_manager.get_property_name(type_name, item.attribute)) is None:
                util.CLogging.error(f'Unknown property hash{item.attribute}, {type_name}')
            data['property'] = tmp
            data['isPPtrCurve'] = item.isPPtrCurve != 0
            data['curve'] = []
            bindings.append(data)
        # generic_bindings['genericBindings'] = bindings
        return {
            'pptrCurveMapping': generic_bindings.pptrCurveMapping,
            'genericBindings': bindings
        }

    @staticmethod
    def parse_streamed_clip(streamed, generic_bindings):
        """
        从muscleClip的m_Clip里面读取数据
        :param streamed:
        :param generic_bindings: 从process_generic_bindings返回的数据
        :return:
        """
        data_uint = streamed.data
        buf = struct.pack(f"<{len(data_uint)}I", *data_uint)
        reader = io.BytesIO(buf)
        not_first = False
        generic_bindings = generic_bindings['genericBindings']
        while reader.tell() + 8 <= len(buf):
            pos = reader.tell()
            time = struct.unpack("<f", reader.read(4))[0]

            if time == math.inf:  # 跳过最后一帧
                break

            curve_count = struct.unpack("<H", reader.read(2))[0]
            reader.read(2)  # padding, skip
            if not_first:
                for _ in range(curve_count):
                    curve_index = struct.unpack('<H', reader.read(2))[0]
                    reader.read(2)
                    data = struct.unpack("<4f", reader.read(16))

                    generic_bindings[curve_index]['curve'].append({
                        'time': time,
                        'data': data
                    })
            else:  # 跳过第一帧
                reader.read(20 * curve_count)
                not_first = True

            if reader.tell() == pos:
                break
        # return frames
        return generic_bindings

    def process(self):
        if len(self.nodes) != 1:
            util.CLogging.error('Error for unexpected number of timeline objects')
        node = self.nodes[0]
        nodes_dict = self.parent_container.nodes_dict
        game_object_container = self.parent_container.container_objects[Container.containerObjectType['GameObject'][0]]
        for name, _node in node.children.items():
            if _node.name.startswith('Ani'):  # Animation Track,读取直接子级的AnimationClip
                data = {
                    'loop': _node.obj.mInfiniteClipLoop
                }
                animation_clip = _node.children['m_InfiniteClip'].obj  # .obj.read_typetree()  # 假设只有m_InfinityClip
                # data['genericBindings'] = animation_clip['m_ClipBindingConstant']
                generic_bindings = self.process_generic_bindings(animation_clip.m_ClipBindingConstant, _node, game_object_container)

                animation_clip = animation_clip.m_MuscleClip.m_Clip.data
                if len(animation_clip.m_DenseClip.m_SampleArray) > 0:
                    util.CLogging.error('Error, length of m_SampleArray is not 0')

                data['data'] = Timeline.parse_streamed_clip(animation_clip.m_StreamedClip, generic_bindings)
                self.data['animationClip'].append(data)

            elif _node.name.startswith('SFX'):  # Sound Fix
                node_obj = _node.obj
                data = self.data['soundFix']
                for clip in node_obj.m_Clips:
                    clip_data = {
                        'clipIn': clip.m_ClipIn,
                        'duration': clip.m_Duration,
                        # 'easeInDuration': node_obj.m_EaseInDuration,  # 这两个忽略算了
                        # 'easeOutDuration': node_obj.m_EaseOutDuration,
                        'start': clip.m_Start,
                    }
                    target = clip.m_Asset.read()
                    audio_data = target.AudioData
                    externals = target.assets_file.externals
                    clip_data['volume'] = audio_data.Volume
                    clip_data['delay'] = audio_data.Delay  # emm, start和delay这两个……

                    audios = []
                    for audio in audio_data.AudioClips:
                        file_id = audio.m_FileID
                        identification = (_node.cab if file_id == 0 else
                                          externals[file_id - 1].name.lower()) + str(audio.m_PathID)
                        audios.append(nodes_dict[identification].obj)

                    clip_data['audios'] = audios

                    data.append(clip_data)

            elif _node.name.startswith('Spine'):
                data = self.data['spineAnimation']
                spine_container = self.parent_container.container_objects[
                    Container.containerObjectType['SpineClips'][0]]
                node_obj = _node.obj
                for clip in node_obj.m_Clips:
                    clip_data = {
                        'clipIn': clip.m_ClipIn,
                        'duration': clip.m_Duration,
                        # 'easeInDuration': node_obj.m_EaseInDuration,  # 这两个忽略算了
                        # 'easeOutDuration': node_obj.m_EaseOutDuration,
                        'start': clip.m_Start,
                    }
                    target = clip.m_Asset
                    file_id = target.m_FileID
                    identification = (_node.cab if file_id == 0 else _node.dependencies[file_id - 1]) + str(target.m_PathID)
                    target = nodes_dict[identification]
                    target_obj = target.obj.template
                    clip_data['ifCustomDuration'] = target_obj.customDuration == 1
                    #  忽略了一堆参数，如attachmentThreshold, dontEndWithClip, endMixOutDuration, holdPrevious.暂不清楚这些参数的作用

                    target_obj = target_obj.animationReference
                    file_id = target_obj.m_FileID
                    identification = (target.cab if file_id == 0 else target.dependencies[file_id - 1]) + str(target_obj.m_PathID)
                    target = nodes_dict[identification]
                    clip_data['animation'] = spine_container.get_index(target.get_identification())

                    data.append(clip_data)

    def test_and_add(self, node):
        if node.name.endswith('_Timeline'):
            self.nodes.append(node)
            return True
        return False


class AmbientEvent(ContainerObject):

    def process(self):
        for _, node in self.nodes.items():
            target_node = node.children['ambientEvent']
            target_obj = target_node.obj
            self.data.append({
                'crossFadeDuration': target_obj.CrossFadeDuration,  # 目前还不知道这个的具体应用
                'loop': target_obj.Loop == 1,
                'volume': target_obj.Volume,
                'audio': target_node.children['Clip'].obj
            })

    def test_and_add(self, node):
        if hasattr(node.obj, 'ambientEvent'):
            self.nodes[node.get_identification()] = node
            return True
        return False


class Container:
    containerObjectType = {
        # 'AudioClip': (0, AudioClip),
        # # 'Sprite': (1, Sprite),
        'GameObject': (0, GameObject),
        'SpineClips': (1, SpineClips),
        'InteractiveConfig': (2, InteractiveConfig),
        # 'ViewBoundsConfig': (3, ViewBoundsConfig),
        'PostProcessing': (3, PostProcessing),
        'SpriteRender': (4, SpriteRender),
        'Particle': (5, Particle),
        'Timeline': (6, Timeline),
        'AmbientEvent': (7, AmbientEvent)
    }

    def __init__(self, student_name, info_json_manager: util.InfoJsonManger, nodes_dict):
        self.name = student_name
        self.container_objects = (
            GameObject(self), SpineClips(self), InteractiveConfig(self),
            PostProcessing(self), SpriteRender(self),
            Particle(self), Timeline(self), AmbientEvent(self))
        self.info_json_manager: util.InfoJsonManger = info_json_manager
        self.nodes_dict = nodes_dict

    def test(self, node):
        for i in self.container_objects:
            i.test_and_add(node)
            # if i.test_and_add(node):
            #     return

    def process(self):
        for i in self.container_objects:
            i.process()
