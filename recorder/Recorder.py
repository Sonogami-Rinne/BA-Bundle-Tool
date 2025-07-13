import json
import os
import pathlib


class Recorder:
    def __init__(self):
        self.batch_data = {}
        self.batch_size: int = 1  # 这个size是保存一批数据前notify的次数，因此并不保证每次保存的文件大小接近
        self.count: int = self.batch_size  # notify计数

    def _save_data(self, name):
        """
        存储数据
        :return:
        """
        path = pathlib.Path(os.path.join('save', 'recorder', self.__class__.__name__, name + '.json'))
        path.mkdir(parents=True, exist_ok=True)
        with open(path, encoding='utf-8') as f:
            json.dump(self.batch_data, f, indent=2)
        self._clear()

    def notify_single(self, node):
        """
        逐文件
        :return:
        """
        return

    def notify_bulk(self, stu):
        """
        逐prefab
        :param stu:
        :return:
        """
        return

    def notify_bundle(self, bundle):
        """
        逐bundle
        :return:
        """
        return

    def notify_total(self):
        """
        所有文件
        :return:
        """
        return

    def _clear(self):
        self.batch_data.clear()

    def _add_with_test(self, *args):
        """
        逐层级向batch_data里面添加字段，如果没有则新增
        :param args:
        :return:
        """
        data = self.batch_data
        for arg in args:
            if (sub_data := data.get(arg)) is None:
                sub_data = {}
                data[arg] = sub_data
            data = sub_data
        return data
