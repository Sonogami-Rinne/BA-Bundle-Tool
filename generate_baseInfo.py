import json
import os

import UnityPy

import util

if __name__ == '__main__':
    files = os.listdir(util.BUNDLES_PATH)
    data = {}
    index = 1
    length = len(files)
    for bundle in files:
        util.CLogging.info(f'当前bundle:{bundle},进度:{index}/{length}')
        index += 1
        bundle_name = bundle.removesuffix('.bundle')
        env = UnityPy.load(os.path.join(util.BUNDLES_PATH, bundle))
        bundle_data = {}
        for cab in env.assets:
            cab_data = {}
            for path_id, obj_reader in cab.objects.items():
                obj = obj_reader.read()
                cab_data[path_id] = (obj_reader.type.value, getattr(obj, 'm_Name', 'Unknown'))
            if len(cab_data) > 0:
                bundle_data[cab.name.lower()] = cab_data
        if len(bundle_data) > 0:
            data[bundle_name] = bundle_data

    with open('baseInfo.json', 'w+', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


