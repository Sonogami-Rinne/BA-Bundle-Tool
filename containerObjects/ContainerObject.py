import json
import os.path
import pathlib


class ContainerObject:
    def __init__(self, parent_container):
        self.data = []
        self.data_keys = []
        self.parent_container = parent_container
        self.nodes = {}

    def process(self):
        """
        处理节点
        :return:
        """
        pass

    def test_and_add(self, node):
        """
        检测node是否命中，并在命中时存入
        :param node:
        :return:
        """
        return False

    def save_data(self, base_path: pathlib.Path):
        """
        保存文件
        :return:
        """
        base_path.mkdir(parents=True, exist_ok=True)
        with open(os.path.join(base_path, self.__class__.__name__ + '.json'), 'w+', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2)

    def get_index(self, identification):
        return self.data_keys.index(identification)
