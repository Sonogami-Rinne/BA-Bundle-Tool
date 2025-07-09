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

    def save_data(self, folder):
        """
        保存文件
        :param folder:
        :return:
        """

    def get_index(self, identification):
        return self.data_keys.index(identification)
