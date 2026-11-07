import os
import pathlib
import shutil
import struct

import xxhash

import util
from containerObjects.ContainerObject import ContainerObject
from excelInfo import db_voice_spine, base_voice_path, db_character_dialog, db_memory_lobby
from typeId import ClassIDType

class SpineClips(ContainerObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.clip_keys = []
        self.skeleton_keys = []
        self.sentences = []
        self.data = {
            'skeletons': [],
            'clips': [],
            'eventAudioMap': {},
            'text': {}
        }
        self.audios = {}
        self.glsls = {}
        self.hlsls = {}
        self.bones = set()

    def export_material(self, material_node):
        info, tex_info, hlsl, glsl, _ = self.process_material(
            material_node, first_variant=True)
        if glsl is not None and glsl[1] is not None:
            self.glsls[glsl[0]] = glsl
        if hlsl is not None and hlsl[1] is not None:
            self.hlsls[hlsl[0]] = hlsl
        return info, tex_info

    def process(self):
        game_object_container = self.parent.container_objects['GameObject']
        self.clip_keys = list(self.nodes.keys())
        nodes_dict = self.parent.nodes_dict
        for _, node in self.nodes.items():
            skeleton_node = node.children['skeletonDataAsset']
            skeleton_name = skeleton_node.children['skeletonJSON'].name
            # if (skeleton_index := self.skeleton_keys.index(skeleton_name)) < 0:
            if skeleton_name not in self.skeleton_keys:
                atlas = []
                # self.skeletons.append(node.children['skeletonJSON'])
                for _name, _node in skeleton_node.children.items():
                    if _name.startswith('atlasAssets'):
                        atlas_item = {
                            'atlas': _node.children['atlasFile']
                        }
                        # self.atlas.append(_node.children['atlasFile'])
                        textures = []
                        material_infos = []
                        material_names = []
                        # material_main_texs = []
                        material_tex_infos = []
                        for _mat_name, _mat in _node.children.items():
                            if _mat_name.startswith('materials-'):
                                info, tex_info = self.export_material(_mat)
                                material_names.append(_mat.name)
                                material_infos.append(info)
                                # material_main_texs.extend(main_tex)
                                material_tex_infos.append(tex_info)
                                for _tex_name, _tex_node in _mat.children.items():
                                    if _tex_name.startswith('m_SavedProperties'):
                                        textures.append(_tex_node)

                        atlas_item['textures'] = textures
                        atlas_item['materialNames'] = material_names
                        atlas_item['materialInfo'] = material_infos
                        atlas_item['texInfo'] = material_tex_infos
                        atlas.append(atlas_item)

                skeleton_index = len(self.skeleton_keys)
                self.skeleton_keys.append(skeleton_name)

                game_object = None

                for _name, _node in skeleton_node.parents:
                    if _name.startswith('skeletonDataAsset') and 'm_GameObject' in _node.children:
                        game_object = _node.children['m_GameObject']

                assert game_object
                translate, _, game_object_scale = util.decompose_2d_transform(util.get_transform(game_object))
                mesh = None
                mesh_renderer = None
                for child in game_object.children.values():
                    if child.type == ClassIDType.MeshRenderer:
                        mesh_renderer = child
                    elif child.type == ClassIDType.MeshFilter:
                        mesh = child.children['m_Mesh'].obj
                # mesh_renderer = next(
                #     (child for child in game_object.children.values() if child.type == ClassIDType.MeshRenderer),
                #     None
                # )
                renderer_materials = [
                    child for name, child in mesh_renderer.children.items()
                    if name.startswith('m_Materials-')
                ] if mesh_renderer else []
                material_infos = []
                material_names = []
                # material_main_texs = []
                material_tex_infos = []
                for renderer_material in renderer_materials:
                    info, tex_info = self.export_material(renderer_material)
                    material_names.append(renderer_material.name)
                    material_infos.append(info)
                    # material_main_texs.extend(main_tex)
                    material_tex_infos.append(tex_info)
                # render_queue = material_infos[0]['renderQueue']

                game_object_path = game_object_container.get_game_object_path(game_object.get_identification())
                skeleton_root_path = game_object_path + '/SkeletonUtility-SkeletonRoot'
                is_main_spine = any(
                    path == skeleton_root_path
                    for path in game_object_container.data.values()
                )

                skel_Json = skeleton_node.children['skeletonJSON']
                skel_byte = skel_Json.obj.m_Script.encode("utf-8", "surrogateescape")

                SpineClips.parse_skel_file(skel_byte, get_bone=True)
                game_object_container.register_game_object(game_object)
                mesh_data = mesh.export().split('\n')

                self.data['skeletons'].append({
                    'defaultMix': round(skeleton_node.obj.defaultMix, 2),
                    'skeletonScale': round(skeleton_node.obj.scale, 6),
                    'gameObjectScale': game_object_scale,
                    'skeleton': skeleton_node.children['skeletonJSON'],
                    'atlas': atlas,
                    'gameObject': game_object_container.get_index(game_object.get_identification()),
                    'isMainSpine': is_main_spine,
                    'translate': translate,
                    'sortingOrder': mesh_renderer.obj.m_SortingOrder,
                    'sortingLayer': mesh_renderer.obj.m_SortingLayer,
                    'materialNames': material_names,
                    'materialInfo': material_infos,
                    # 'materialsMainTex': material_main_texs,
                    'texInfo': material_tex_infos,
                    'subMeshPositionZ': [int(mesh_data[i.firstVertex + 1].split(' ')[-1]) for i in mesh.m_SubMeshes],
                    # 'rendererSortingOrder': mesh_renderer.obj.m_SortingOrder,
                    # 'rendererSortingLayer': mesh_renderer.obj.m_SortingLayer
                })

            else:
                skeleton_index = self.skeleton_keys.index(skeleton_name)

            node_obj = node.obj
            tmp = {
                'skeleton': skeleton_index,
                'clipName': node_obj.ClipName,
                'loop': node_obj.Loop == 1,
                'introDelayDuration': round(node_obj.IntroDelayDuration, 2),
                'introMix': round(node_obj.IntroMix, 2),
                'outroMix': round(node_obj.OutroMix, 2),
                'outroStartOffset': round(node_obj.OutroStartOffset, 2),
                'track': node_obj.Track,  # Track为负数的话，播完就隐藏当前spine对象
                'useDefaultIntroMix': node_obj.UseDefaultIntroMix == 1,
                'useDefaultOutroMix': node_obj.UseDefaultOutroMix == 1,
                'isTrackMainIdle': node_obj.IsTrackMainIdle == 1,
                'syncPlays': [
                    self.clip_keys.index(node.children[i].get_identification()) for i in
                    list(filter(lambda x: x.startswith('Sync'), node.children.keys()))
                ],
                'nextClip': self.clip_keys.index(
                    node.children['NextClipObject'].get_identification()) if 'NextClipObject' in node.children else None
            }

            sound_keys = []
            for i in node_obj.SoundKeys:
                target = i.Event
                file_id = target.m_FileID
                iden = (node.cab if file_id == 0 else node.dependencies[file_id - 1]) + str(target.m_PathID)
                target = nodes_dict[iden]
                target_obj = target.obj

                sub_item = {
                    # 'time': i.Time,
                    'delay': round(i.Time),  # hmm
                    'loop': target_obj.AudioData.Loop == 1,
                    'volume': round(target_obj.AudioData.Volume, 2)
                }

                audios = []
                self.audios[target.name] = []
                for audio in target_obj.AudioData.AudioClips:
                    if audio.m_PathID != 0:
                        iden = (target.dependencies[audio.m_FileID - 1] if audio.m_FileID != 0 else target.cab) + str(
                            audio.m_PathID)
                        if _target := nodes_dict.get(iden):
                            self.audios[target.name].append(_target)
                            audios.append(_target.name)

                sub_item['audios'] = audios
                sound_keys.append(sub_item)

            tmp['soundKeys'] = sound_keys
            self.data['clips'].append(tmp)

    def test_and_add(self, node):
        if hasattr(node.obj, 'ClipName'):
            self.nodes[node.get_identification()] = node
            return True
        return False

    def get_index(self, identification):
        return self.clip_keys.index(identification)

    def is_bone(self, name):
        return name in self.bones

    def save_data(self, base_path):
        audio_path = os.path.join(base_path, 'audio')
        pathlib.Path(audio_path).mkdir(parents=True, exist_ok=True)
        for _, audios in self.audios.items():
            for audio in audios:
                for sample_name, sample_data in audio.obj.samples.items():
                    with open(os.path.join(audio_path, sample_name), 'wb+') as f:
                        f.write(sample_data)

        _path = os.path.join(base_path, 'image')
        pathlib.Path(_path).mkdir(parents=True, exist_ok=True)
        for skeleton in self.data['skeletons']:
            target = skeleton['skeleton']
            skel_byte = target.obj.m_Script.encode("utf-8", "surrogateescape")
            with open(os.path.join(base_path, target.name), 'wb+') as f:
                f.write(skel_byte)
            skeleton['skeleton'] = target.name

            events = SpineClips.parse_skel_file(skel_byte)
            for event in events:
                if event['audioPath'] is not None or event['stringValue'] == '' or event['stringValue'] in self.data['eventAudioMap']:
                    continue
                name_hash = SpineClips.xxh32_intdigest(event['stringValue'])
                if name_hash not in db_voice_spine:
                    util.CLogging.warn(f'Event {event["stringValue"]} do not have a matched audio source')
                    continue

                tar = db_voice_spine[name_hash]
                new_dict = {
                    'path': [i[i.index('/') + 1:] for i in tar['path']],
                    'volume': tar['volume']
                }
                self.data['eventAudioMap'][event['stringValue']] = new_dict

                for audio in db_voice_spine[name_hash]['path']:
                    shutil.copy(os.path.join(base_voice_path, audio), audio_path)

            target = skeleton['atlas']

            for atlas in target:
                atlas_node = atlas['atlas']
                with open(os.path.join(base_path, atlas_node.name), 'w+', encoding='utf-8', newline='') as f:
                    f.write(atlas_node.obj.m_Script)

                atlas['atlas'] = atlas_node.name

                textures = atlas['textures']

                for i in range(len(textures)):
                    textures[i].obj.image.save(os.path.join(base_path, 'image', textures[i].name + '.png'))
                    textures[i] = textures[i].name + '.png'
                    # with open(os.path.join(base_path, 'atlas_img', textures[i].name), 'w')

        # self.data['text'] = db_character_dialog[db_memory_lobby[self.parent.prefab]['character']]
        if chr_info := db_memory_lobby.get(self.parent.prefab.lower(), None):
            self.data['text'] = db_character_dialog[chr_info['character']]

        shader_root = pathlib.Path(base_path) / 'shader'
        for shader_name, (_, vertex, fragment) in self.glsls.items():
            shader_path = shader_root / shader_name
            shader_path.parent.mkdir(parents=True, exist_ok=True)
            shader_path.with_suffix('.vert').write_text(vertex, encoding='utf-8')
            shader_path.with_suffix('.frag').write_text(fragment, encoding='utf-8')

        _path = os.path.join(base_path, 'rawShader')
        os.makedirs(_path, exist_ok=True)
        for k, v in self.hlsls.items():
            _shader_path = k
            if '/' in k:
                _shader_path = k[:k.rindex('/')]
            _shader_path = os.path.join(_path, _shader_path)
            os.makedirs(_shader_path, exist_ok=True)
            with open(os.path.join(_path, k + '.shader'), 'w+', encoding='utf-8') as f:
                f.write(v[1])

        super().save_data(base_path)

    @staticmethod
    def parse_skel_file(skel: bytes, get_bone=False):
        """Read animation events and the slot-to-bone map from a Spine 4.2 skeleton."""
        reader = Reader(skel)
        bones = set()

        def skip_indices():
            for _ in range(reader.read_int(True)):
                reader.read_int(True)

        def skip_sequence():
            # count, start, digits, setup index
            for _ in range(4):
                reader.read_int(True)

        def skip_vertices(weighted):
            vertex_count = reader.read_int(True)
            vertices_length = vertex_count * 2
            if not weighted:
                reader.escape(vertices_length * 4)
                return vertices_length

            for _ in range(vertex_count):
                bone_count = reader.read_int(True)
                for __ in range(bone_count):
                    reader.read_int(True)  # bone index
                    reader.escape(12)  # x, y, weight
            return vertices_length

        def skip_attachment(nonessential):
            flags = reader.read_byte()
            attachment_type = flags & 0x07

            if flags & 0x08:
                reader.read_int(True)  # name string reference

            if attachment_type == 0:  # Region
                if flags & 0x10:
                    reader.read_int(True)  # path string reference
                if flags & 0x20:
                    reader.escape(4)  # color
                if flags & 0x40:
                    skip_sequence()
                if flags & 0x80:
                    reader.escape(4)  # rotation
                reader.escape(24)  # x, y, scaleX, scaleY, width, height
            elif attachment_type == 1:  # Bounding box
                skip_vertices((flags & 0x10) != 0)
                if nonessential:
                    reader.escape(4)  # color
            elif attachment_type == 2:  # Mesh
                if flags & 0x10:
                    reader.read_int(True)  # path string reference
                if flags & 0x20:
                    reader.escape(4)  # color
                if flags & 0x40:
                    skip_sequence()
                hull_length = reader.read_int(True)
                vertices_length = skip_vertices((flags & 0x80) != 0)
                reader.escape(vertices_length * 4)  # UVs
                triangle_count = (vertices_length - hull_length - 2) * 3
                for _ in range(triangle_count):
                    reader.read_int(True)
                if nonessential:
                    for _ in range(reader.read_int(True)):
                        reader.read_int(True)  # edge
                    reader.escape(8)  # width, height
            elif attachment_type == 3:  # Linked mesh
                if flags & 0x10:
                    reader.read_int(True)  # path string reference
                if flags & 0x20:
                    reader.escape(4)  # color
                if flags & 0x40:
                    skip_sequence()
                reader.read_int(True)  # skin index
                reader.read_int(True)  # parent string reference
                if nonessential:
                    reader.escape(8)  # width, height
            elif attachment_type == 4:  # Path
                vertices_length = skip_vertices((flags & 0x40) != 0)
                reader.escape((vertices_length // 6) * 4)  # lengths
                if nonessential:
                    reader.escape(4)  # color
            elif attachment_type == 5:  # Point
                reader.escape(12)  # rotation, x, y
                if nonessential:
                    reader.escape(4)  # color
            elif attachment_type == 6:  # Clipping
                reader.read_int(True)  # end slot index
                skip_vertices((flags & 0x10) != 0)
                if nonessential:
                    reader.escape(4)  # color
            else:
                raise ValueError(f"Unsupported attachment type: {attachment_type}")

        def skip_skin(default_skin, nonessential):
            if default_skin:
                slot_count = reader.read_int(True)
                if slot_count == 0:
                    return
            else:
                reader.read_string()  # skin name
                if nonessential:
                    reader.escape(4)  # color
                skip_indices()  # bones
                skip_indices()  # IK constraints
                skip_indices()  # transform constraints
                skip_indices()  # path constraints
                skip_indices()  # physics constraints
                slot_count = reader.read_int(True)

            for _ in range(slot_count):
                reader.read_int(True)  # slot index
                for __ in range(reader.read_int(True)):
                    reader.read_int(True)  # attachment name string reference
                    skip_attachment(nonessential)

        def skip_curve_timeline(frame_count, value_count):
            if frame_count == 0:
                return
            reader.escape((value_count + 1) * 4)  # time and values
            for _ in range(1, frame_count):
                reader.escape((value_count + 1) * 4)
                curve = reader.read_byte()
                if curve == 2:  # CURVE_BEZIER
                    reader.escape(value_count * 16)

        def skip_slot_timeline(timeline_type, frame_count):
            if timeline_type == 0:  # SLOT_ATTACHMENT
                for _ in range(frame_count):
                    reader.escape(4)  # time
                    reader.read_int(True)  # attachment string reference
                return

            channel_counts = {
                1: 4,  # SLOT_RGBA
                2: 3,  # SLOT_RGB
                3: 7,  # SLOT_RGBA2
                4: 6,  # SLOT_RGB2
                5: 1,  # SLOT_ALPHA
            }
            channel_count = channel_counts.get(timeline_type)
            if channel_count is None:
                raise ValueError(f"Unsupported slot timeline type: {timeline_type}")

            reader.read_int(True)  # bezier count
            if frame_count == 0:
                return
            reader.escape(4 + channel_count)  # time and color bytes
            for _ in range(1, frame_count):
                reader.escape(4 + channel_count)
                curve = reader.read_byte()
                if curve == 2:  # CURVE_BEZIER
                    reader.escape(channel_count * 16)

        def read_animation(animation_name, event_data):
            animation_events = []
            reader.read_int(True)  # timeline count/capacity

            # Slot timelines.
            for _ in range(reader.read_int(True)):
                reader.read_int(True)  # slot index
                for __ in range(reader.read_int(True)):
                    timeline_type = reader.read_byte()
                    skip_slot_timeline(timeline_type, reader.read_int(True))

            # Bone timelines.
            value_counts = {
                0: 1,  # rotate
                1: 2,  # translate
                2: 1,  # translate X
                3: 1,  # translate Y
                4: 2,  # scale
                5: 1,  # scale X
                6: 1,  # scale Y
                7: 2,  # shear
                8: 1,  # shear X
                9: 1,  # shear Y
            }
            for _ in range(reader.read_int(True)):
                reader.read_int(True)  # bone index
                for __ in range(reader.read_int(True)):
                    timeline_type = reader.read_byte()
                    frame_count = reader.read_int(True)
                    if timeline_type == 10:  # BONE_INHERIT
                        reader.escape(frame_count * 5)  # time and inherit mode
                        continue
                    value_count = value_counts.get(timeline_type)
                    if value_count is None:
                        raise ValueError(f"Unsupported bone timeline type: {timeline_type}")
                    reader.read_int(True)  # bezier count
                    skip_curve_timeline(frame_count, value_count)

            # IK constraint timelines.
            for _ in range(reader.read_int(True)):
                reader.read_int(True)  # constraint index
                frame_count = reader.read_int(True)
                reader.read_int(True)  # bezier count
                for frame in range(frame_count):
                    flags = reader.read_byte()
                    reader.escape(4)  # time
                    if (flags & 1) != 0 and (flags & 2) != 0:
                        reader.escape(4)  # mix
                    if (flags & 4) != 0:
                        reader.escape(4)  # softness
                    if frame > 0 and (flags & 128) != 0:
                        reader.escape(32)  # two Bezier curves

            # Transform constraint timelines.
            for _ in range(reader.read_int(True)):
                reader.read_int(True)  # constraint index
                frame_count = reader.read_int(True)
                reader.read_int(True)  # bezier count
                skip_curve_timeline(frame_count, 6)

            # Path constraint timelines.
            for _ in range(reader.read_int(True)):
                reader.read_int(True)  # constraint index
                for __ in range(reader.read_int(True)):
                    timeline_type = reader.read_byte()
                    frame_count = reader.read_int(True)
                    reader.read_int(True)  # bezier count
                    if timeline_type in (0, 1):
                        skip_curve_timeline(frame_count, 1)
                    elif timeline_type == 2:
                        skip_curve_timeline(frame_count, 3)
                    else:
                        raise ValueError(f"Unsupported path timeline type: {timeline_type}")

            # Physics constraint timelines.
            for _ in range(reader.read_int(True)):
                reader.read_int(True)  # constraint index + 1
                for __ in range(reader.read_int(True)):
                    timeline_type = reader.read_byte()
                    frame_count = reader.read_int(True)
                    if timeline_type == 8:  # PHYSICS_RESET
                        reader.escape(frame_count * 4)
                    elif timeline_type in (0, 1, 2, 4, 5, 6, 7):
                        reader.read_int(True)  # bezier count
                        skip_curve_timeline(frame_count, 1)
                    else:
                        raise ValueError(f"Unsupported physics timeline type: {timeline_type}")

            # Attachment timelines.
            for _ in range(reader.read_int(True)):
                reader.read_int(True)  # skin index
                for __ in range(reader.read_int(True)):
                    reader.read_int(True)  # slot index
                    for ___ in range(reader.read_int(True)):
                        reader.read_int(True)  # attachment name string reference
                        timeline_type = reader.read_byte()
                        frame_count = reader.read_int(True)
                        if timeline_type == 0:  # ATTACHMENT_DEFORM
                            reader.read_int(True)  # bezier count
                            if frame_count > 0:
                                reader.escape(4)  # first frame time
                            for frame in range(frame_count):
                                end = reader.read_int(True)
                                if end > 0:
                                    reader.read_int(True)  # start
                                    reader.escape(end * 4)
                                if frame < frame_count - 1:
                                    reader.escape(4)  # next frame time
                                    curve = reader.read_byte()
                                    if curve == 2:  # CURVE_BEZIER
                                        reader.escape(16)
                        elif timeline_type == 1:  # ATTACHMENT_SEQUENCE
                            reader.escape(frame_count * 12)
                        else:
                            raise ValueError(f"Unsupported attachment timeline type: {timeline_type}")

            # Draw order timeline.
            for _ in range(reader.read_int(True)):
                reader.escape(4)  # time
                for __ in range(reader.read_int(True)):
                    reader.read_int(True)  # slot index
                    reader.read_int(True)  # offset

            # Event timeline.
            for _ in range(reader.read_int(True)):
                time = reader.read_float()
                event_index = reader.read_int(True)
                if event_index >= len(event_data):
                    raise ValueError(f"EventData index out of range: {event_index}")
                data = event_data[event_index]
                event = {
                    'animation': animation_name,
                    'time': time,
                    'name': data['name'],
                    'intValue': reader.read_int(False),
                    'floatValue': reader.read_float(),
                    'stringValue': reader.read_string(),
                    'audioPath': data['audioPath'],
                    'volume': 1.0,
                    'balance': 0.0,
                }
                if event['stringValue'] is None:
                    event['stringValue'] = data['stringValue']
                if data['audioPath'] is not None:
                    event['volume'] = reader.read_float()
                    event['balance'] = reader.read_float()
                animation_events.append(event)

            return animation_events

        # Skeleton header.
        reader.escape(8)
        version = reader.read_string()
        if version is None or not version.startswith('4.2'):
            raise ValueError(f"Expected a Spine 4.2 binary skeleton, got {version!r}")
        reader.escape(20)
        nonessential = reader.read_byte() != 0
        if nonessential:
            reader.escape(4)
            reader.read_string()
            reader.read_string()
        # Strings
        list_len = reader.read_int(True)
        for _ in range(list_len):
            reader.read_string()

        # Bones
        list_len = reader.read_int(True)
        for index in range(list_len):
            bones.add(reader.read_string()) if get_bone else reader.read_string()
            if index != 0:
                reader.read_int(True)  # parent index
            reader.escape(32)  # rotation, x, y, scaleX/Y, shearX/Y, length
            reader.read_int(True)  # inherit mode
            reader.read_byte()  # skin required
            if nonessential:
                reader.escape(4)
                reader.read_string()
                reader.read_byte()
        if get_bone:
            return bones
        # Slots
        list_len = reader.read_int(True)
        for _ in range(list_len):
            reader.read_string()  # slot name
            reader.read_int(True)  # bone index
            reader.escape(8)  # light and dark colors
            reader.read_int(True)  # attachment name string reference
            reader.read_int(True)  # blend mode
            if nonessential:
                reader.read_byte()  # visible

        # IK
        list_len = reader.read_int(True)
        for _ in range(list_len):
            reader.read_string()
            reader.read_int(True)  # order
            skip_indices()  # constrained bones
            reader.read_int(True)  # target bone
            flag = reader.read_byte()
            if (flag & 32) != 0 and (flag & 64) != 0:
                reader.escape(4)
            if (flag & 128) != 0:
                reader.escape(4)

        # Transform
        list_len = reader.read_int(True)
        for _ in range(list_len):
            reader.read_string()
            reader.read_int(True)  # order
            skip_indices()  # constrained bones
            reader.read_int(True)  # target bone
            flag = reader.read_byte()
            reader.escape(4 * sum((flag & bit) != 0 for bit in (8, 16, 32, 64, 128)))
            flag = reader.read_byte()
            reader.escape(4 * sum((flag & bit) != 0 for bit in (1, 2, 4, 8, 16, 32, 64)))

        # Path Constraint
        list_len = reader.read_int(True)
        for _ in range(list_len):
            reader.read_string()
            reader.read_int(True)  # order
            reader.read_byte()  # skin required
            skip_indices()  # constrained bones
            reader.read_int(True)  # target slot
            flag = reader.read_byte()
            if (flag & 128) != 0:
                reader.escape(4)
            reader.escape(20)

        # Physics Constraint
        list_len = reader.read_int(True)
        for _ in range(list_len):
            reader.read_string()
            reader.read_int(True)  # order
            reader.read_int(True)  # bone index
            flag = reader.read_byte()
            reader.escape(4 * sum((flag & bit) != 0 for bit in (2, 4, 8, 16, 32, 64)))
            reader.read_byte()  # step
            reader.escape(12)  # inertia, strength, damping
            if (flag & 128) != 0:
                reader.escape(4)
            reader.escape(8)  # wind, gravity
            flag = reader.read_byte()
            if (flag & 128) != 0:
                reader.escape(4)

        # Default skin, then additional skins.
        skip_skin(True, nonessential)
        for _ in range(reader.read_int(True)):
            skip_skin(False, nonessential)

        # EventData is the lookup table used by animation event timelines.
        event_data = []
        for _ in range(reader.read_int(True)):
            data = {
                'name': reader.read_string(),
                'intValue': reader.read_int(False),
                'floatValue': reader.read_float(),
                'stringValue': reader.read_string(),
                'audioPath': reader.read_string(),
                'volume': 1.0,
                'balance': 0.0,
            }
            if data['audioPath'] is not None:
                data['volume'] = reader.read_float()
                data['balance'] = reader.read_float()
            event_data.append(data)

        # Flatten the events from every animation into one list.
        events = []
        for _ in range(reader.read_int(True)):
            animation_name = reader.read_string()
            events.extend(read_animation(animation_name, event_data))
        return events

    @staticmethod
    def xxh32_intdigest(data: bytes | str, seed: int = 0) -> int:
        payload = data.encode("utf8") if isinstance(data, str) else data
        return xxhash.xxh32_intdigest(payload, seed)
    def clear(self):
        super().clear()
        self.audios.clear()
        self.glsls.clear()
        self.clip_keys.clear()
        self.skeleton_keys.clear()
        self.data = {
            'skeletons': [],
            'clips': [],
            'eventAudioMap': {},
            'text': {}
        }
        self.hlsls.clear()
        self.bones.clear()
        # self.data['skeletons'].clear()
        # self.data['clips'].clear()


class Reader:
    def __init__(self, buffer):
        self.buffer = buffer
        self.pointer = 0

    def escape(self, length):
        if length < 0 or self.pointer + length > len(self.buffer):
            raise EOFError('Unexpected end of Spine binary data')
        self.pointer += length

    def read_byte(self):
        result = self.buffer[self.pointer]
        self.pointer += 1
        return result

    def read_float(self):
        result = struct.unpack_from('>f', self.buffer, self.pointer)[0]
        self.pointer += 4
        return result

    def read_int(self, optimize):
        b = self.read_byte()
        result = b & 0x7f
        if (b & 0x80) != 0:
            b = self.read_byte()
            result |= (b & 0x7f) << 7
            if (b & 0x80) != 0:
                b = self.read_byte()
                result |= (b & 0x7f) << 14
                if (b & 0x80) != 0:
                    b = self.read_byte()
                    result |= (b & 0x7f) << 21
                    if (b & 0x80) != 0:
                        b = self.read_byte()
                        result |= (b & 0x7f) << 28
        return result if optimize else ((result >> 1) ^ -(result & 1))

    def read_string(self):
        str_length = self.read_int(True)
        if str_length == 0:
            return None
        if str_length == 1:
            return ""
        str_length -= 1
        result = self.buffer[self.pointer:self.pointer + str_length].decode('utf-8')
        self.pointer += str_length
        return result

