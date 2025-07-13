from recorder.Recorder import Recorder


class ExternalsRecorder(Recorder):
    """
    以该文件为起点的指定直径(半径?)上限的最大有向图的所有节点的bundle.由于单次遍历就是遍历该文件的所有子级，故此处就是简单的遍历所有节点
    """

    def __init__(self):
        super().__init__()
        self.base_bundle = None
        self.tmp = {}

    def notify_single(self, node):
        if self.base_bundle is None:
            self.base_bundle = node.bundle
            return
        if self.base_bundle == node.bundle:
            return

        if (bundle_data := self.tmp.get(node.bundle)) is None:
            bundle_data = []
            self.tmp[node.bundle] = bundle_data

        if node.bundle not in bundle_data:
            bundle_data.append(node.bundle)

    def notify_bulk(self, stu):
        self.batch_data[stu] = self.tmp
        self.tmp.clear()

    def notify_bundle(self, bundle):
        self.count -= 1
        if self.count == 0:
            self.count = self.batch_size
            self._save_data(bundle)

    # def _save_data(self, name):
    #     for _, data in self.batch_data:
    #         data.pop(0)  # 最先加进去的节点为自身，得除去
    #
    #     super()._save_data(name)
