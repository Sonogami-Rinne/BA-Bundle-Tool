import os
import pathlib

from pyvis.network import Network

from Recorder import Recorder


class TrackVisualizationRecorder(Recorder):
    """
    使用Pyvis生成网络图.目前暂不支持hash的引用
    """

    def __init__(self):
        super().__init__()
        self.network = None
        self.node_map = None
        self._clear()

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

    def notify_single(self, node):
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

    def notify_bulk(self, stu, saving=True):
        self._save_data(stu)

    def _save_data(self, name):
        path = pathlib.Path(os.path.join('save', 'network'))
        path.mkdir(parents=True, exist_ok=True)
        self.network.show(os.path.join(path, name + '.html'))
        self._clear()

    def _clear(self):
        self.batch_data = []
        self.network = Network(height="750px", width="100%", directed=True, notebook=True)
        self.node_map = self.network.node_map
        self.network.set_options("""
                {
                  "physics": {
                    "enabled": true,
                    "solver": "forceAtlas2Based",
                    "forceAtlas2Based": {
                      "gravitationalConstant": -100,
                      "centralGravity": 0.005,
                      "springLength": 200,
                      "springConstant": 0.04
                    },
                    "minVelocity": 0.75,
                    "stabilization": {
                      "enabled": true,
                      "iterations": 1000,
                      "updateInterval": 10000
                    }
                  },
                  "interaction": {
                    "dragNodes": true,
                    "dragView": true,
                    "zoomView": true
                  },
                  "edges": {
                    "smooth": {
                      "type": "continuous",
                      "roundness": 0.2
                    },
                    "font": {
                      "align": "horizontal",
                      "strokeWidth": 3,
                      "strokeColor": "#ffffff"
                    },
                    "selectionWidth": 2,
                    "arrows": {
                      "to": {
                        "enabled": true,
                        "scaleFactor": 0.6
                      }
                    }
                  }
                }
                """)
