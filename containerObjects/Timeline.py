import io
import math
import struct

import util
from containerObjects.ContainerObject import ContainerObject
from typeId import ClassIDType, inverse_map
from unityResourceNode import UnityResourceNode
from linkedList import LinkedList


class Timeline(ContainerObject):
    """
    总的那个时间线.说实话应该从PlayableDirector开始的
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.data = {
            'animationClip': [],
            'soundFix': [],
            'spineAnimation': []
        }
        self.nodes = []
        self.game_object_container = None

    @staticmethod
    def _get_hash_dict(node):
        result = {}
        for name, target_node in node.parents.items():
            if name.endswith('key'):
                break
        # 没有保证是否找到，没有保证是否进入循环，不过会报错的
        name = name.removesuffix('key') + 'value'

        target_node = target_node.children[name].children['m_GameObject']
        base_index = target_node.hierarchy_index

        node_list = LinkedList[UnityResourceNode](target_node)  # 忽略掉PlayableDirector和Animator的所有属性

        while node_list.head:
            head = node_list.remove()
            node_list.adds(head.hierarchy_children)
            hierarchy_path = '/'.join(head.hierarchy[base_index:])
            result[util.compute_unity_hash(hierarchy_path)] = (
                hierarchy_path,
                head
            )
        return result

    def _process_generic_bindings(self, generic_bindings, node):
        """
        :param generic_bindings:
        :param node: UnityResourceNode<AnimationClip>
        :return: list[{'node','property','isPPtrCurve','curve'}]
        """
        info_json_manager = self.parent_container.info_json_manager
        game_object_dict = self.game_object_container
        nodes_dict = self.parent_container.nodes_dict
        dependencies = node.dependencies
        generics = generic_bindings.genericBindings
        bindings = []
        hash_dict = Timeline._get_hash_dict(node)
        for item in generics:
            pass
        #     script = item.script
        #     data = {}
        #
        #     type_name = inverse_map[str(item.typeID)]
        #     #  path = game_object_dict.get_path(item.path)
        #     data['gameObject'] = path.get_identification()
        #     if (path_id := script.m_PathID) != 0:  # 直接根据pathID, fileID得到对应对象
        #         file_id = script.m_FileID
        #         identification = (node.cab if file_id == 0 else dependencies[file_id - 1]) + str(path_id)
        #         data['node'] = nodes_dict[identification]
        #     else:
        #         data = {}
        #
        #         if item.typeID == ClassIDType.GameObject:
        #             data['node'] = path
        #         else:
        #             for node in path.children.values():
        #                 if node.type == type_name:
        #                     data['node'] = node
        #                     break
        #
        #     if (tmp := info_json_manager.get_property_name(type_name, item.attribute)) is None:
        #         util.CLogging.error(f'Unknown property hash{item.attribute}, {type_name}')
        #     data['property'] = tmp
        #     data['isPPtrCurve'] = item.isPPtrCurve != 0
        #     data['curve'] = []
        #     bindings.append(data)
        # # generic_bindings['genericBindings'] = bindings
        # return {
        #     'pptrCurveMapping': generic_bindings.pptrCurveMapping,
        #     'genericBindings': bindings
        # }

    @staticmethod
    def _parse_streamed_clip(streamed, generic_bindings):
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
        self.game_object_container = self.parent_container.container_objects['GameObject']
        spine_container = self.parent_container.container_objects['SpineClips']

        if len(self.nodes) != 1:
            util.CLogging.error('Error for unexpected number of timeline objects')
        node = self.nodes[0]
        nodes_dict = self.parent_container.nodes_dict
        for name, _node in node.children.items():
            if _node.name.startswith('Ani'):  # Animation Track
                data = {
                    'loop': _node.obj.mInfiniteClipLoop
                }
                animation_clip = _node.children['m_InfiniteClip'].obj  # .obj.read_typetree()  # 假设只有m_InfinityClip
                # data['genericBindings'] = animation_clip['m_ClipBindingConstant']
                generic_bindings = self._process_generic_bindings(animation_clip.m_ClipBindingConstant, _node)

                animation_clip = animation_clip.m_MuscleClip.m_Clip.data
                if len(animation_clip.m_DenseClip.m_SampleArray) > 0:
                    util.CLogging.error('Error, length of m_SampleArray is not 0')

                data['data'] = Timeline._parse_streamed_clip(animation_clip.m_StreamedClip, generic_bindings)
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
                    identification = (_node.cab if file_id == 0 else _node.dependencies[file_id - 1]) + str(
                        target.m_PathID)
                    target = nodes_dict[identification]
                    target_obj = target.obj.template
                    clip_data['ifCustomDuration'] = target_obj.customDuration == 1
                    #  忽略了一堆参数，如attachmentThreshold, dontEndWithClip, endMixOutDuration, holdPrevious.暂不清楚这些参数的作用

                    target_obj = target_obj.animationReference
                    file_id = target_obj.m_FileID
                    identification = (target.cab if file_id == 0 else target.dependencies[file_id - 1]) + str(
                        target_obj.m_PathID)
                    target = nodes_dict[identification]
                    clip_data['animation'] = spine_container.get_index(target.get_identification())

                    data.append(clip_data)

    def test_and_add(self, node):
        if node.name.endswith('_Timeline'):
            self.nodes.append(node)
            return True
        return False

    def save_data(self, base_path):
        base_path.mkdir(parents=True, exist_ok=True)
