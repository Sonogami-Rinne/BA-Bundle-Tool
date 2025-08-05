import io
import math
import os
import pathlib
import struct

import util
from containerObjects.ContainerObject import ContainerObject
from typeId import ClassIDType, inverse_map
from unityResourceNode import UnityResourceNode
from linkedList import LinkedList
from propertyHash import get_property

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
        self.audios = []

    def _get_hash_dict_(self):
        result = {}
        nodes = list(self.parent_container.container_objects['GameObject'].nodes.values())

        for node in nodes:
            for i in range(len(node.transform.hierarchy)):
                result[util.compute_unity_hash('/'.join(node.transform.hierarchy[i:]))] = ('/'.join(node.transform.hierarchy[i:]), node)

        return result

    @staticmethod
    def _get_hash_dict(node):
        result = {}
        flag = False
        for name, target_node in node.parents:
            if name.endswith('key'):
                flag = True
                break
        # if flag:
        #     util.CLogging.error('Unhandled PlayableDirector struct')
        #     return {}
        # 没有保证是否找到，没有保证是否进入循环，不过会报错的
        if flag:
            name = name.removesuffix('key') + 'value'

            # _target_node = target_node.children[name].children['m_GameObject'].transform
            if (_target_node := target_node.children.get(name)) is None:
                _target_node = target_node

            _target_node = _target_node.children['m_GameObject'].transform
        else:
            util.CLogging.error('Unhandled playable director structure')
            return {}

        base_index = len(_target_node.hierarchy)

        node_list = LinkedList[UnityResourceNode](_target_node)  # 忽略掉PlayableDirector和Animator的所有属性

        while node_list.head:
            head = node_list.pop()
            node_list.adds(head.hierarchy_children)
            hierarchy_path = '/'.join(head.hierarchy[base_index:])
            result[util.compute_unity_hash(hierarchy_path)] = (
                hierarchy_path,
                head.game_object
            )
        return result

    def _process_generic_bindings(self, generic_bindings, node):
        """
        :param generic_bindings:
        :param node: UnityResourceNode<AnimationClip>
        :return: list[{'node','property','isPPtrCurve','curve'}]
        """
        # info_json_manager = self.parent_container.info_json_manager
        nodes_dict = self.parent_container.nodes_dict
        dependencies = node.dependencies
        generics = generic_bindings.genericBindings
        bindings = []
        hash_dict = self._get_hash_dict(node)
        _node = node
        for item in generics:
            script = item.script
            data = {}

            # type_name = inverse_map[str(item.typeID)]
            #  path = game_object_dict.get_path(item.path)
            #  data['gameObject'] = path.get_identification()
            path_object = hash_dict.get(item.path)
            # if path_object is None:
            #     _hash_dict = self._get_hash_dict_()
            #     path_object = _hash_dict.get(item.path)

            _tmp = self.game_object_container.get_index(path_object[1].get_identification()) if path_object else None
            # if _tmp is None:
            #     raise ValueError
            data['gameObject'] = _tmp
            if _tmp:
                if (path_id := script.m_PathID) != 0:  # 直接根据pathID, fileID得到对应对象
                    file_id = script.m_FileID
                    iden = (node.cab if file_id == 0 else dependencies[file_id - 1]) + str(path_id)
                    data['node'] = nodes_dict[iden].obj.object_reader.read_typetree()
                else:
                    if item.typeID == ClassIDType.GameObject:
                        data['node'] = path_object[1].obj.object_reader.read_typetree()
                    else:
                        for _node in path_object[1].children.values():
                            if _node.type == item.typeID:
                                data['node'] = _node.obj.object_reader.read_typetree()
                                break
            # if (path_id := script.m_PathID) != 0:  # 直接根据pathID, fileID得到对应对象
            #     file_id = script.m_FileID
            #     iden = (node.cab if file_id == 0 else dependencies[file_id - 1]) + str(path_id)
            #     data['node'] = nodes_dict[iden].obj.object_reader.read_typetree()
            # else:
            #     if item.typeID == ClassIDType.GameObject:
            #         data['node'] = path_object[1].obj.object_reader.read_typetree()
            #     else:
            #         for node in path_object[1].children.values():
            #             if node.type == item.typeID:
            #                 data['node'] = node.obj.object_reader.read_typetree()
            #                 break

            data['isPPtrCurve'] = item.isPPtrCurve != 0
            data['curve'] = []

            tmp = get_property(item.typeID, item.attribute)
            if isinstance(tmp, list):
                for sub_property in tmp:
                    sub_item = data.copy()
                    sub_item['property'] = sub_property
                    bindings.append(sub_item)
            else:
                data['property'] = tmp
                bindings.append(data)

            # assert False
            # if (tmp := info_json_manager.get_property_name(type_name, item.attribute)) is None:
            #     if tmp := compound_hash.get(item.attribute):
            #         for extend in tmp:
            #             extended_item = data.copy()
            #             extended_item['property'] = extend
            #             bindings.append(extended_item)
            #     else:
            #         util.CLogging.error(f'Unknown property hash {item.attribute}, {type_name}')
            #     # assert False


            # else:
            #     data['property'] = tmp
            #     bindings.append(data)
        # generic_bindings['genericBindings'] = bindings
        return {
            'pptrCurveMapping': generic_bindings.pptrCurveMapping,
            'genericBindings': bindings
        }

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

        # tmp = []
        # while reader.tell() + 8 <= len(buf):
        #     item = {}
        #
        #     pos = reader.tell()
        #     time = struct.unpack('<f', reader.read(4))[0]
        #
        #     item['time'] = time
        #
        #     curve_count = struct.unpack('<H', reader.read(2))[0]
        #     item['curve_count'] = curve_count
        #     item['padding'] = struct.unpack('<H', reader.read(2))[0]
        #
        #     item['data'] = []
        #
        #     for _ in range(curve_count):
        #         sub_item = {}
        #         curve_index = struct.unpack('<H', reader.read((2)))[0]
        #         sub_item['curve_index'] = curve_index
        #
        #         sub_item['padding'] = struct.unpack('<H', reader.read(2))[0]
        #
        #         sub_item['data'] = struct.unpack('<4f', reader.read(16))
        #         item['data'].append(sub_item)
        #
        #     tmp.append(item)
        #
        #     if reader.tell() == pos:
        #         break
        #
        # if reader.tell() < len(buf):
        #     raise IOError
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

                    if curve_index >= len(generic_bindings):
                        util.CLogging.error('Curve index out of range')
                    else:
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

        # if len(self.nodes) != 1:
        #     util.CLogging.error('Error for unexpected number of timeline objects')
        # node = self.nodes[0]
        nodes_dict = self.parent_container.nodes_dict
        for node in self.nodes:
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
                        util.CLogging.warn('Warn, length of m_SampleArray is not 0')

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
                        # target = clip.m_Asset.read()
                        iden = (_node.cab if clip.m_Asset.m_FileID == 0 else _node.dependencies[clip.m_Asset.m_FileID - 1]) + str(clip.m_Asset.m_PathID)
                        target = nodes_dict[iden].obj
                        # audio_data = target.AudioData
                        audio_data = getattr(target, 'AudioData', None)
                        if audio_data:

                            externals = target.assets_file.externals
                            clip_data['volume'] = audio_data.Volume
                            clip_data['delay'] = audio_data.Delay  # emm, start和delay这两个……

                            audios = []
                            for audio in audio_data.AudioClips:
                                file_id = audio.m_FileID
                                iden = (_node.cab if file_id == 0 else
                                        externals[file_id - 1].name.lower()) + str(audio.m_PathID)
                                _target = nodes_dict[iden]
                                self.audios.append(_target)
                                # audios.append(nodes_dict[iden].obj)
                                audios.append(_target.name)

                            clip_data['audios'] = audios

                            data.append(clip_data)

                # elif _node.name.startswith('Spine Animation'):
                elif hasattr(_node.obj, 'm_Clips') and hasattr(_node.obj, 'trackIndex'):
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
                        iden = (_node.cab if file_id == 0 else _node.dependencies[file_id - 1]) + str(target.m_PathID)
                        # target = nodes_dict[iden]
                        target = nodes_dict[iden]
                        target_obj = target.obj.template
                        clip_data['ifCustomDuration'] = target_obj.customDuration == 1
                        #  忽略了一堆参数，如attachmentThreshold, dontEndWithClip, endMixOutDuration, holdPrevious.暂不清楚这些参数的作用

                        target_obj = target_obj.animationReference
                        file_id = target_obj.m_FileID
                        iden = (target.cab if file_id == 0 else target.dependencies[file_id - 1]) + str(
                            target_obj.m_PathID)
                        if target := nodes_dict.get(iden):
                            clip_data['spineClip'] = spine_container.get_index(target.get_identification())
                            data.append(clip_data)

    def test_and_add(self, node):
        if node.name.endswith('_Timeline'):
            self.nodes.append(node)
            return True
        return False

    def clear(self):
        super().clear()
        self.audios.clear()
        self.data = {
            'animationClip': [],
            'soundFix': [],
            'spineAnimation': []
        }

    def save_data(self, base_path):
        _path = os.path.join(base_path, 'audio', 'other')
        pathlib.Path(_path).mkdir(parents=True, exist_ok=True)
        for audio in self.audios:
            for name, data in audio.obj.samples.items():
                with open(os.path.join(_path, name), 'wb+') as f:
                    f.write(data)
        _path = os.path.join(base_path, 'audio', 'voice')
        pathlib.Path(_path).mkdir(parents=True, exist_ok=True)
        super().save_data(base_path)

        # for name, data in audio_obj.samples.items():
        #     with open(os.path.join(base_path, 'ambient-' + name), 'wb+') as f:
        #         f.write(data)
