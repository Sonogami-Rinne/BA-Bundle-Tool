import os
import pathlib

import util
from containerObjects.ContainerObject import ContainerObject


class SpineClips(ContainerObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.clip_keys = []
        self.skeleton_keys = []
        self.data = {
            'voiceRedirect': None,
            'skeletons': [],
            'clips': [],
        }
        self.audios = {}

    def process(self):
        game_object_container = self.parent_container.container_objects['GameObject']
        self.clip_keys = list(self.nodes.keys())
        nodes_dict = self.parent_container.nodes_dict
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
                        for _mat_name, _mat in _node.children.items():
                            if _mat_name.startswith('materials'):
                                for _tex_name, _tex_node in _mat.children.items():
                                    if _tex_name.startswith('m_SavedProperties'):
                                        textures.append(_tex_node)

                        atlas_item['textures'] = textures
                        atlas.append(atlas_item)

                skeleton_index = len(self.skeleton_keys)
                self.skeleton_keys.append(skeleton_name)

                game_object = None

                for _name, _node in skeleton_node.parents:
                    if _name.startswith('skeletonDataAsset') and 'm_GameObject' in _node.children:
                        game_object = _node.children['m_GameObject']

                assert game_object
                # translate, rotation, scale = util.decompose_2d_transform(util.get_transform(game_object))

                self.data['skeletons'].append({
                    'defaultMix': round(skeleton_node.obj.defaultMix, 2),
                    # 'scale': skeleton_node.obj.scale,
                    'scale': 1,
                    'skeleton': skeleton_node.children['skeletonJSON'],
                    'atlas': atlas,
                    'gameObject': game_object_container.get_index(game_object.get_identification()),
                    # 'transform': {
                    #     'translate': translate,
                    #     'rotation': rotation,
                    #     'scale': scale
                    # },
                    'viewBounds': None
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
                'nextClip': self.clip_keys.index(node.children['NextClipObject'].get_identification()) if 'NextClipObject' in node.children else None
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
                        iden = (target.dependencies[audio.m_FileID - 1] if audio.m_FileID != 0 else target.cab) + str(audio.m_PathID)
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

    def save_data(self, base_path):
        _path = os.path.join(base_path, 'audio', 'other')
        pathlib.Path(_path).mkdir(parents=True, exist_ok=True)
        for _, audios in self.audios.items():
            for audio in audios:
                for sample_name, sample_data in audio.obj.samples.items():
                    with open(os.path.join(_path, sample_name), 'wb+') as f:
                        f.write(sample_data)

        _path = os.path.join(base_path, 'image')
        pathlib.Path(_path).mkdir(parents=True, exist_ok=True)
        # for audio in self.audios:
        #     for sample_name, sample_data in audio.obj.samples.items():
        #         with open(os.path.join(base_path, sample_name), 'wb+') as f:
        #             f.write(sample_data)
        for skeleton in self.data['skeletons']:
            target = skeleton['skeleton']
            with open(os.path.join(base_path, target.name), 'wb+') as f:
                f.write(target.obj.m_Script.encode("utf-8", "surrogateescape"))
            skeleton['skeleton'] = target.name

            target = skeleton['atlas']

            for atlas in target:
                atlas_node = atlas['atlas']
                with open(os.path.join(base_path, atlas_node.name), 'w+') as f:
                    f.write(atlas_node.obj.m_Script)

                atlas['atlas'] = atlas_node.name

                textures = atlas['textures']

                for i in range(len(textures)):
                    textures[i].obj.image.save(os.path.join(base_path, 'image', textures[i].name + '.png'))
                    textures[i] = textures[i].name + '.png'
                    # with open(os.path.join(base_path, 'atlas_img', textures[i].name), 'w')

        super().save_data(base_path)

    def clear(self):
        super().clear()
        self.audios.clear()
        self.clip_keys.clear()
        self.skeleton_keys.clear()
        self.data = {
            'voiceRedirect': None,
            'skeletons': [],
            'clips': [],
        }
        # self.data['skeletons'].clear()
        # self.data['clips'].clear()

