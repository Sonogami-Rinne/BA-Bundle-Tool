from recorder.Recorder import Recorder


class TrackInfoRecorder(Recorder):
    """
    只记录PPtr型的引用，AnimationClip的hash型的引用不记录
    """

    def __init__(self):
        super().__init__()
        self.batch_data1 = {}  # 反映射，按理来说应该全局保存的，但鉴于数据庞大，只能随着正向映射保存。因此在反映射里查找得遍历所有的文件
        self.batch_size = 50

    def add_node(self, node):
        #  只遍历出边
        for _property, _node in node.children.items():
            path_data = self._add_with_test(node.cab, node.path_id)
            if (cab_data := path_data.get(_node.cab)) is None:
                cab_data = []
                path_data[_node.cab] = cab_data
            cab_data.append((_property, _node.path_id))  # 可以确保不重

    def notify_bundle(self, bundle, saving=True):
        if saving:
            self.count -= 1
            if self.count == 0:
                self.count = self.batch_size
                self._save_data('to' + bundle)
