from recorder.containerObjects.ContainerObject import ContainerObject

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
