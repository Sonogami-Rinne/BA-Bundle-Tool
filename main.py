import os

import infoJsonManager
from fileManager import FileManager
from unityResourceNode import UnityResourceNode
import util
from util import CLogging
from containerObjects.index import Container
from recorder.index import Recorder
from typeId import ClassIDType


def single(data: tuple):
    """
    :param data: cab, path_id type, name
    :return:
    """

    head = UnityResourceNode((data[0], data[1], data[2], data[3]), file_manager, info_json_manager)
    # target_nodes[Container.containerObjectType['ViewBounds'][0]].append(head)
    if not head.init():
        return

    container.notify_single(head)
    recorder.notify_single(head)

    node_dict[head.get_identification()] = head
    cur_tail = None
    tail = head
    ignored_node = []

    for turn in range(util.MAX_DEPTH):
        end_flag = True

        while head != cur_tail:
            extends = head.walk_through()
            for attr_path, item in extends.items():
                iden = item[0] + str(item[1])
                if (i_node := node_dict.get(iden)) is None:
                    node_info = info_json_manager.get_path_info(item[0], item[1])
                    if node_info is None:
                        ignored_node.append(iden)
                        CLogging.warn(f'Ignored node{iden}')
                        continue
                    i_node = UnityResourceNode((item[0], item[1], node_info[0], node_info[1]), file_manager,
                                               info_json_manager)
                    if not i_node.init():
                        ignored_node.append(iden)
                        CLogging.info(f'Ignored node{iden}')
                        continue
                    node_dict[iden] = i_node
                    tail.next = i_node
                    tail = i_node
                    if cur_tail is None:
                        cur_tail = tail

                    end_flag = False
                head.add_child(attr_path, i_node)

                container.notify_single(i_node)
                recorder.notify_single(i_node)

            head.references = None
            head = head.next

        cur_tail = None

        if end_flag:
            break
    return node_dict


def run_files_in_single_bundle(bundle):
    for cab_name, cab_data in file_manager.get_bundle(bundle).items():
        for path, data in cab_data['data'].items():
            # if data['type'] != 'GameObject' or not (
            #         data['name'].startswith('Lobby') and not data['name'].startswith('SC')):
            #     continue

            cur_student[0] = data['name'].removeprefix('Lobby')
            util.CLogging.info(f'当前学生:{cur_student[0]}')
            single((cab_name, path, data['type'], data['name']))

            container.notify_bulk(cur_student[0])
            recorder.notify_bulk(cur_student[0])


def run_bundles(bundle_filter):
    for file in os.listdir(util.BUNDLES_PATH):
        if bundle_filter is None or bundle_filter(file):
            CLogging.info(f'处理{file}')

            bundle = file.removesuffix('.bundle')
            run_files_in_single_bundle(bundle)

            container.notify_bundle(bundle)
            recorder.notify_bundle(bundle)

    container.notify_total()
    recorder.notify_total()


if __name__ == '__main__':
    info_json_manager = infoJsonManager.InfoJsonManger()
    info_json_manager.init(using_hash_info=False)
    file_manager = FileManager(info_json_manager)
    node_dict: dict[str, UnityResourceNode] = {}
    container = Container(info_json_manager, node_dict)
    recorder = Recorder()

    cur_student = ['1']

    run_bundles(None)
