import os

from fileManager import FileManager
from unityResourceNode import UnityResourceNode
import util
from util import CLogging


def single_reference(data: tuple):
    """
    :param data: cab, path_id type, name
    :return:
    """
    identifications: dict[str, UnityResourceNode] = {}
    head = UnityResourceNode((data[0], data[1], data[2], data[3]), file_manager, root=True)
    # target_nodes[Container.containerObjectType['ViewBounds'][0]].append(head)
    if not head.init():
        CLogging.error('Please select another file as this file is ignored')
        return
    identifications[(data[0] + str(data[1]))] = head
    cur_tail = None
    tail = head
    ignored_node = []

    for turn in range(util.MAX_DEPTH):
        end_flag = True

        while head != cur_tail:
            extends = head.walk_through()
            for attr_path, item in extends.items():
                iden = item[0] + str(item[1])
                i_node = identifications.get(iden)
                if i_node is None:
                    node_info = file_manager.get_path_info(item[0], item[1])
                    if node_info is None:
                        ignored_node.append(iden)
                        CLogging.warn(f'Ignored node{iden}')
                        continue
                    i_node = UnityResourceNode((item[0], item[1], node_info['type'], node_info['name']), file_manager)
                    if not i_node.init():
                        ignored_node.append(iden)
                        CLogging.info(f'Ignored node{iden}')
                        continue
                    identifications[iden] = i_node
                    tail.next = i_node
                    tail = i_node
                    if cur_tail is None:
                        cur_tail = tail
                        
                    end_flag = False
                i_node.parents[attr_path] = head
                head.children[attr_path] = i_node

            head.references = None
            head = head.next

        cur_tail = None

        if end_flag:
            break
    return identifications


def run_files_in_single_bundle(file, single, save_path, save_method):
    for cab_name, cab_data in file_manager.get_bundle_(file).items():
        for path, data in cab_data['data'].items():
            if data['type'] != 'GameObject' or not (
                    data['name'].startswith('Lobby') and not data['name'].startswith('SC')):
                continue
            #  self.net = Network(height="750px", width="100%", directed=True, notebook=True)
            cur_student[0] = data['name'].removeprefix('Lobby')
            dependency_track[cur_student[0]] = {}
            dependencies_in_total[cur_student[0]] = []
            data = single((cab_name, path, data['type'], data['name']))
            save_method(path=save_path, data=data, stu=cur_student[0], dependency_track=dependency_track,
                        dependencies_in_total=dependencies_in_total)


def run_bundles(bundle_filter, save_folder):
    if bundle_filter is None:
        bundle_filter = lambda x: True
    for file in os.listdir(util.BUNDLES_PATH):
        if bundle_filter(file):
            CLogging.info(f'处理{file}')
            # logging.info(f'处理{file}ing')
            folder = os.path.join(save_folder, file[:file.rindex('.')])
            # if not (pathlib.Path(folder)).exists():
            #     os.mkdir(folder)
            #
            # dependency_track = {}
            # missing_reference = []
            # dependencies_in_total = {}
            # cur_student = ['1']
            #
            # runner.test()


def show_network_graph(nodes: list[UnityResourceNode]):
    """
    使用pyvis生成html
    :param nodes:
    :return:
    """
    pass


def track_dependency(cab0, cab1, id1):
    bundle0 = file_manager.get_bundle_name(cab0)
    bundle1 = file_manager.get_bundle_name(cab1)
    if dependency_track[cur_student[0]].get(cab0) is None:
        dependency_track[cur_student[0]][cab0] = {}
    if id1 not in dependency_track[cur_student[0]][cab0]:
        dependency_track[cur_student[0]][cab0][id1] = cab1
    if bundle0 not in dependencies_in_total[cur_student[0]]:
        dependencies_in_total[cur_student[0]].append(bundle0)
    if bundle1 not in dependencies_in_total[cur_student[0]]:
        dependencies_in_total[cur_student[0]].append(bundle1)


if __name__ == 'main':
    file_manager = FileManager()
    dependency_track = {}
    cur_student = ['1']
    dependencies_in_total = {}
