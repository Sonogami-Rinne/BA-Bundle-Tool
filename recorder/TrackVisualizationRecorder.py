from pyvis.network import Network

from Recorder import Recorder


class TrackVisualizationRecorder(Recorder):
    """
    使用Pyvis生成网络图.目前暂不支持hash的引用
    """

    def __init__(self):
        super().__init__()
        self.network = Network(height="750px", width="100%", directed=True, notebook=True)
        self.node_map = self.network.node_map

    def add_node(self, node):
        identification = node.get_identification()
        node_info = node.get_node()
        self.node_map[identification] = {
            'id': identification,
            'label': node_info[0],
            'shape': 'dot',
            'color': node_info[1],
            'title': node_info[2]
        }

        for edge in node.get_out_edges():
            if edge[0] not in self.node_map.keys():
                self.node_map[edge[1]] = {  # 先加入占位Node,等到遍历到实际的Node时再更新数据
                    id: identification,
                    'label': 'Error Node',
                    'shape': 'dot',
                }
                self.network.add_edge(identification, edge[0], label=edge[1], title=edge[1],
                                      color="#6E6E6E", width=2, arrows="to")

    # def add_hash_info(self, timeline_container):
    #     """
    #     从TimelineContainer那里获取hash信息并加入边。
    #     :param timeline_container:
    #     :return:
    #     """
    #     clips = timeline_container.data['animationClip']
    #     for clip in clips:
    #         clip_data = clip['data']
    #         for pptr in clip_data['pptrCurvingMapping']:
    #
