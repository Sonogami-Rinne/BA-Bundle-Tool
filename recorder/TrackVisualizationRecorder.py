import os
import pathlib
import shutil
from pyvis.network import Network

from recorder.Recorder import Recorder


class TrackVisualizationRecorder(Recorder):
    """
    使用Pyvis生成网络图.目前暂不支持hash的引用
    """

    def __init__(self):
        super().__init__()
        self.network = None
        self.node_map = None
        self.node_ids = None
        self.nodes = []
        self._clear()

    def notify_single(self, node):
        self.nodes.append(node)
        pass

    def notify_bulk(self, stu):
        for node in self.nodes:
            identification = node.get_identification()
            node_info = node.get_node()
            self.node_map[identification] = {
                'id': identification,
                'label': node_info[0],
                'shape': 'dot',
                'color': node_info[1],
                'title': node_info[2]
            }
            if identification not in self.node_ids:
                self.node_ids.append(identification)

            for edge in node.get_out_edges():
                if edge[0] not in self.node_ids:
                    self.node_map[edge[0]] = {  # 先加入占位Node,等到遍历到实际的Node时再更新数据
                        'id': edge[0],
                        'label': 'Error Node',
                        'shape': 'dot',
                        'color': '#FFFFFF',
                        'title': edge[0]
                    }
                    self.node_ids.append(edge[0])

                self.network.add_edge(identification, edge[0], label=edge[1], title=edge[1],
                                      color="#6E6E6E", width=2, arrows="to")
        self.network.nodes = list(self.node_map.values())
        self._save_data(stu)

    def _save_data(self, name):
        path = pathlib.Path(os.path.join('save', 'recorder', 'Networks'))
        path.mkdir(parents=True, exist_ok=True)

        with open(os.path.join(path, name + '.html'), 'w+', encoding='utf-8') as f:
            f.write(self.network.generate_html())
        #  self.network.save_graph(os.path.join(path, name + '.html'))
        self._clear()

    def _clear(self):
        self.network = Network(height="750px", width="100%", directed=True, notebook=True, cdn_resources='in_line')
        self.node_map = self.network.node_map
        self.node_ids = self.network.node_ids
        self.nodes.clear()
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
