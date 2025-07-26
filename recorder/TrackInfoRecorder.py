import json
import os
import pathlib

from recorder.Recorder import Recorder


class TrackInfoRecorder(Recorder):
    """
    只记录PPtr型的引用，AnimationClip的hash型的引用不记录
    """

    def __init__(self):
        super().__init__()
        self.batch_data1 = {}  # 反映射，按理来说应该全局保存的，但鉴于数据庞大，只能随着正向映射保存。因此在反映射里查找得遍历所有的文件
        self.nodes = []

    def notify_single(self, node):
        self.nodes.append(node)

    def notify_bulk(self, stu):
        for node in self.nodes:
            #  只遍历出边
            for _property, _node in node.children.items():
                path_data = self._add_with_test(node.cab, node.path_id)
                if (cab_data := path_data.get(_node.cab)) is None:
                    cab_data = []
                    path_data[_node.cab] = cab_data
                cab_data.append((_property, _node.path_id))  # 可以确保不重

    def notify_bundle(self, bundle):
        self._save_data(bundle)

    def _save_data(self, name):
        path = pathlib.Path(os.path.join('save', 'recorder', self.__class__.__name__, 'map'))
        path.mkdir(parents=True, exist_ok=True)
        with open(os.path.join(path, name + '.json'), 'w+', encoding='utf-8') as f:
            json.dump(self.batch_data, f, indent=2)

        path = pathlib.Path(os.path.join('save', 'recorder', self.__class__.__name__, 'inverseMap'))
        path.mkdir(parents=True, exist_ok=True)
        with open(os.path.join(path, name + '.json'), 'w+', encoding='utf-8') as f:
            json.dump(self.batch_data1, f, indent=2)

        self._clear()

    def _clear(self):
        self.batch_data.clear()
        self.nodes.clear()
        self.batch_data1.clear()
