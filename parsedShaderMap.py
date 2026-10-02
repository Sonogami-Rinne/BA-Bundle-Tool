import pathlib

import util

parsed_shaders_folder_path = r'E:\desktop1\work\BAPIXIShaderProject'
parsed_shader_folder_root = 'BAPIXIShaderProject'
parsed_shader_map = {}
for _i in pathlib.Path(parsed_shaders_folder_path).rglob('*.vert'):
    parts = _i.parts[_i.parts.index(parsed_shader_folder_root) + 1:]
    shader_name = '/'.join(parts)
    shader_name = f'{shader_name[:-5]}'
    stage_path = str(_i)
    with open(stage_path, 'r', encoding='utf-8') as f:
        vertex_content = f.read()
    stage_path = f'{stage_path[:-4]}frag'
    with open(stage_path, 'r', encoding='utf-8') as f:
        frag_content = f.read()
    parsed_shader_map[shader_name] = (vertex_content, frag_content)

def get_parsed_shader(shader_name):
    if (tar := parsed_shader_map.get(shader_name, None)) is not None:
        return tar
    util.CLogging.error(f'Shader {shader_name} not parsed!!!')
    return None, None




