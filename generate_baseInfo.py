import json
import os

import UnityPy

import util

if __name__ == '__main__':
    files = os.listdir(util.BUNDLES_PATH)
    data = {}
    index = 0
    for bundle in files:
        print(index)
        index += 1
        bundle_name = bundle.removesuffix('.bundle')
        env = UnityPy.load(os.path.join(util.BUNDLES_PATH, bundle))
        bundle_data = {}
        for cab_name, cab in env.cabs.items():
            if '.' not in cab_name:
                cab_data = {}
                for path_id, obj_reader in cab.objects.items():
                    obj = obj_reader.read()
                    cab_data[path_id] = (obj_reader.type_id, getattr(obj, 'm_Name', 'Unknown'))
                if len(cab_data) > 0:
                    bundle_data[cab_name] = cab_data
        if len(bundle_data) > 0:
            data[bundle_name] = bundle_data

    with open('merged.json', 'w+', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


