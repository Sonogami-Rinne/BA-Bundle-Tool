import UnityPy

UNITY_DEFAULT_RESOURCE_PATH = r"E:\D\Program\YostarGames\BlueArchive_JP\BlueArchive_Data\Resources\unity default resources"

datas = {
    'bundle_data': None
}

def get_unity_default_resource(path):
    bundle_data = datas['bundle_data']
    if bundle_data is None:
        bundle_data = UnityPy.load(UNITY_DEFAULT_RESOURCE_PATH).assets[0].files

    return bundle_data.get(path, None)

