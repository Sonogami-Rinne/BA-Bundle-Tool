import os

import infoJsonManager
from fileManager import FileManager
from unityResourceNode import UnityResourceNode
import util
from util import CLogging
from containerObjects.index import Container
from recorder.index import Recorder
from typeId import ClassIDType
from linkedList import LinkedList


def single(data: tuple):
    """
    :param data: cab, path_id type, name
    :return:
    """

    head = UnityResourceNode((data[0], data[1], data[2], data[3]), file_manager, info_json_manager, root=True)
    if not head.init():
        return

    container.notify_single(head)
    recorder.notify_single(head)

    node_dict[head.get_identification()] = head
    node_list = LinkedList[UnityResourceNode](head)

    ignored_node = []

    for turn in range(util.MAX_DEPTH):
        end_flag = True

        for node in node_list.walk_through():
            extends = node.walk_through()
            for attr_path, item in extends.items():
                iden = item[0] + str(item[1])
                if (i_node := node_dict.get(iden)) is None:
                    if (node_info := info_json_manager.get_path_info(item[0], item[1])) is None:
                        ignored_node.append(iden)
                        CLogging.warn(f'Ignored node: {iden}')
                        continue
                    i_node = UnityResourceNode((item[0], item[1], node_info[0], node_info[1]), file_manager,
                                               info_json_manager)
                    if not i_node.init():
                        ignored_node.append(iden)
                        CLogging.info(f'Ignored node: {iden}')
                        continue
                    node_dict[iden] = i_node
                    node_list.add(i_node)
                    end_flag = False

                    container.notify_single(i_node)
                    recorder.notify_single(i_node)

                node.add_child(attr_path, i_node)

            node.references.clear()

        if end_flag:
            break


def run_files_in_single_bundle(bundle):
    for cab_name, cab_data in file_manager.get_bundle(bundle).items():
        for path, data in cab_data.items():
            file_name = getattr(data[1], 'm_Name', 'Unknown')
            cur_file[0] = file_name
            util.CLogging.info(f'当前:{cur_file[0]}')
            single((cab_name, path, data[0], file_name))

            container.notify_bulk(cur_file[0])
            recorder.notify_bulk(cur_file[0])
            node_dict.clear()


def run_files_in_prefabs(bundle):
    for cab_name, path_id, obj in util.env_load_prefabs(bundle):
        file_name = getattr(obj, 'm_Name')
        cur_file[0] = file_name
        # if '0238' not in file_name:
        #     continue
        util.CLogging.info(f'当前:{cur_file[0]}')
        single((cab_name, path_id, ClassIDType.GameObject, file_name))

        container.notify_bulk(cur_file[0])
        recorder.notify_bulk(cur_file[0])
        node_dict.clear()


def run_bundles(bundle_filter, bulk_fnc):
    for file in os.listdir(util.BUNDLES_PATH):
        if bundle_filter is None or bundle_filter(file):
            CLogging.info(f'处理{file}')

            bundle = file.removesuffix('.bundle')
            bulk_fnc(bundle)

            container.notify_bundle(bundle)
            recorder.notify_bundle(bundle)

    container.notify_total()
    recorder.notify_total()


if __name__ == '__main__':
    info_json_manager = infoJsonManager.InfoJsonManger()
    info_json_manager.init()
    file_manager = FileManager(info_json_manager)
    node_dict: dict[str, UnityResourceNode] = {}
    container = Container(info_json_manager, node_dict)
    recorder = Recorder()

    cur_file = ['1']

    run_bundles(lambda x: x.startswith('ui-uilobbyelement'),
                run_files_in_prefabs if util.PREFABS_MODE else run_files_in_single_bundle)
