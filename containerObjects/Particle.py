import util
from containerObjects.ContainerObject import ContainerObject
from typeId import ClassIDType


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
                if _node.type == ClassIDType.ParticleSystemRenderer:
                    obj = _node.obj
                    break
            data['rendererModule'] = Particle.process_particle_renderer(obj)
            data['name'] = node.name
            data['gameObject'] = parent.get_identification()
            #  self.data[parent.get_identification()] = data
            self.data.append(data)
            self.data_keys.append(node.get_identification())

    def test_and_add(self, node):
        if node.type == ClassIDType.ParticleSystem:
            self.nodes[node.get_identification()] = node

    # def save_data(self, base_path):
    #     base_path.mkdir(parents=True, exist_ok=True)
    #     with open(os.path.join(base_path, 'particle.json'), 'w+', encoding='utf-8') as f:
    #         json.dump(self.data, )
