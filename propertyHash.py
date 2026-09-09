import json
import pathlib

import util
from typeId import ClassIDType, inverse_map
from util import CLogging

pre_hash_dict = {
    ClassIDType.SpriteRenderer: {
        0: "m_Sprite",
    },
    ClassIDType.Transform: {
        1: [
            'm_LocalPosition.x',
            'm_LocalPosition.y',
            'm_LocalPosition.z'
        ],
        2: [
            'm_LocalRotation.x',
            'm_LocalRotation.y',
            'm_LocalRotation.z',
            'm_LocalRotation.w',
        ],
        3: [
            'm_LocalScale.x',
            'm_LocalScale.y',
            'm_LocalScale.z'
        ],
        4: [  # 欧拉角
            'm_LocalRotation.x',
            'm_LocalRotation.y',
            'm_LocalRotation.z'
        ],
    },
    ClassIDType.MeshFilter: {
        3757223753: "m_Mesh",
    },
    ClassIDType.ParticleSystemRenderer: {
        0: "m_Materials.Array.data[0]",
        2539813375: "m_ReceiveShadows",
        3762991556: "m_SortingOrder",
        3305885265: "m_Enabled",
        1232391921: "m_RendererPriority",
        3507904317: "m_MinParticleSize",
        4138547212: "m_MaxParticleSize",
        1317541591: "m_CameraVelocityScale",
        237351048: "m_VelocityScale",
        3128036037: "m_LengthScale",
        3244821577: "m_SortingFudge",
        2141240505: "m_NormalDirection",
        2179977062: "m_ShadowBias",
        3640387206: "m_Pivot.x",
        2952582672: "m_Pivot.y",
        922060714: "m_Pivot.z",
        966041755: "m_Flip.x",
        1318293517: "m_Flip.y",
        3617243575: "m_Flip.z",
        1351232598: "m_MeshWeighting",
        25465178: "m_MeshWeighting1",
        2559426784: "m_MeshWeighting2",
        4018860150: "m_MeshWeighting3",
    },
}
material_reference_hash_dict = {
        0: "m_Materials.Array.data[0]",
        1: "m_Materials.Array.data[1]",
        2: "m_Materials.Array.data[2]",
        3: "m_Materials.Array.data[3]",
        4: "m_Materials.Array.data[4]",
        5: "m_Materials.Array.data[5]",
        6: "m_Materials.Array.data[6]",
        7: "m_Materials.Array.data[7]",
}
hash_json = {}


def get_property(type_id, _hash):
    if target := hash_json[str(type_id)].get(str(_hash)):
        return target
    if target := pre_hash_dict.get(type_id):
        if target := target.get(_hash):
            return target
    if target := hash_json['material_'].get(str(_hash)):
        return target
    if type_id in [ClassIDType.MeshRenderer, ClassIDType.SpriteRenderer, ClassIDType.ParticleSystemRenderer] and (target := material_reference_hash_dict.get(_hash)):
        return target
    CLogging.error(f'Unknown hash {_hash} of {type_id}, ignored')
    return None


path = pathlib.Path("save\\recorder\\HashInfoRecorder\\hash.json")
if path.exists():
    with open(path, 'r', encoding='utf-8') as f:
        hash_json = json.load(f)
else:
    CLogging.warn('Hash info json not found')
