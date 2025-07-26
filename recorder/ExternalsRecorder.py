from recorder.Recorder import Recorder


class ExternalsRecorder(Recorder):
    """
    以该文件为起点的指定直径(半径?)上限的最大有向图的所有节点的bundle.由于单次遍历就是遍历该文件的所有子级，故此处就是简单的遍历所有节点
    """

    def __init__(self):
        super().__init__()
        self.tmp = []

    def notify_single(self, node):
        if node.bundle not in self.tmp:  # 算上自身所在的bundle
            self.tmp.append(node.bundle)

    def notify_bulk(self, stu):
        self.batch_data[stu] = self.tmp
        self.tmp = []

    def notify_total(self):
        self._save_data('externals')

    def _clear(self):
        self.batch_data.clear()
        self.tmp.clear()

    # def _save_data(self, name):
    #     for _, data in self.batch_data:
    #         data.pop(0)  # 最先加进去的节点为自身，得除去
    #
    #     super()._save_data(name)
