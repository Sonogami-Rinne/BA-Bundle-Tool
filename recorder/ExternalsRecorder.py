from recorder.Recorder import Recorder


class ExternalsRecorder(Recorder):
    """
    以该文件为起点的指定直径(半径?)上限的最大有向图的所有节点的bundle.由于单次遍历就是遍历该文件的所有子级，故此处就是简单的遍历所有节点
    """

    def __init__(self):
        super().__init__()
        self.phase_bundle = None
        self.phase_stu = None
        self.base_bundle = None
        self.base_dependencies = None

    def add_node(self, node):
        if self.base_bundle is None:
            self.base_bundle = node.bundle
            self.base_dependencies = node.dependencies
            return
        if self.base_bundle == node.bundle:
            return

        data = self._add_with_test(self.phase_stu)
        if (bundle_data := data.get(node.bundle)) is None:
            bundle_data = []
            data[node.bundle] = bundle_data

        if node.bundle not in bundle_data:
            bundle_data.append(node.bundle)

    def notify_single(self, stu, saving=True):
        self.phase_stu = stu

    def notify_bundle(self, bundle, saving=True):
        self.phase_bundle = bundle
        if saving:
            self.count -= 1
            if self.count == 0:
                self.count = self.batch_size
                self._save_data(bundle)

    def _save_data(self, name):
        for _, data in self.batch_data:
            data.pop(0)  # 最先加进去的节点为自身，得除去
        
        super()._save_data(name)
