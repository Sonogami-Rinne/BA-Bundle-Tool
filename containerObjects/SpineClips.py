import os

from containerObjects.ContainerObject import ContainerObject


class SpineClips(ContainerObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.clip_keys = []
        self.skeleton_keys = []
        self.data = {
            'skeletons': [],
            'clips': [],
        }
        self.audios = {}

    def process(self):
        self.clip_keys = list(self.nodes.keys())
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
                    'scale': skeleton_node.obj.scale,
                    'filename': skeleton_node.children['skeletonJSON'].name
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
                    self.clip_keys.index(node.children[i].get_identification()) for i in
                    list(filter(lambda x: x.startswith('Sync'), node.children.keys()))
                ]
            }
            sound_keys = []
            for i in node_obj.SoundKeys:
                target = i.Event
                file_id = target.m_FileID
                iden = (node.cab if file_id == 0 else node.dependencies[file_id - 1]) + str(target.m_PathID)
                target = nodes_dict[iden]
                target_obj = target.obj

                sub_item = {
                    'time': i.Time,
                    'prefix': target.name,
                    'loop': target_obj.AudioData.Loop,
                    'volume': target_obj.AudioData.Volume
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




                # if target.name not in self.audios:
                #     self.audios[target.name] = target

                # sound_keys.append({
                #     'time': i.Time,
                #     'audio': target.name
                # })
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
        for prefix, audios in self.audios.items():
            for audio in audios:
                for sample_name, sample_data in audio.obj.samples.items():
                    with open(os.path.join(base_path, prefix + '-' + sample_name), 'wb+') as f:
                        f.write(sample_data)
        # for audio in self.audios:
        #     for sample_name, sample_data in audio.obj.samples.items():
        #         with open(os.path.join(base_path, sample_name), 'wb+') as f:
        #             f.write(sample_data)
        super().save_data(base_path)

    def clear(self):
        super().clear()
        self.audios.clear()
        self.clip_keys.clear()
        self.skeleton_keys.clear()
        self.data = {
            'skeletons': [],
            'clips': [],
        }

