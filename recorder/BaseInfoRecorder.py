import json
import os.path

from recorder.Recorder import Recorder


class BaseInfoRecorder(Recorder):
    """
    每个文件的基本信息的记录(bundle,cab,type,name,path_id
    """

    def __init__(self):
        super().__init__()
        self.batch_size = 100

    def add_node(self, node):
        data = self._add_with_test(node.bundle, node.cab, node.path_id)
        data['name'] = node.name
        data['type'] = node.type

    def notify_bundle(self, bundle):
        self.count -= 1
        if self.count == 0:
            self.count = self.batch_size
            self._save_data('to' + bundle)
