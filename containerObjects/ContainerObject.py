import json
import os.path
import pathlib

import util
from CJSONEncoder import CJSONEncoder
from shaderTool.ShaderVariantExtractor import get_variant_shader_data
from util import CLogging
from parsedShaderMap import get_parsed_shader
from shaderTool.RenderState import resolve_blend_info


class ContainerObject:
    def __init__(self, parent):
        self.data = []
        self.data_keys = []
        self.parent = parent
        self.nodes = {}

    def process(self):
        """
        处理节点
        :return:
        """
        pass

    def test_and_add(self, node):
        """
        检测node是否命中，并在命中时存入
        :param node:
        :return:
        """
        return False

    def save_data(self, base_path: pathlib.Path):
        """
        保存文件
        :return:
        """
        base_path.mkdir(parents=True, exist_ok=True)
        with open(os.path.join(base_path, self.__class__.__name__ + '.json'), 'w+', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, cls=CJSONEncoder)

        self.clear()

    def get_index(self, identification):
        try:
            return self.data_keys.index(identification)
        except ValueError:
            return None

    def clear(self):
        self.data.clear()
        self.data_keys.clear()
        self.nodes.clear()

    def process_material(self, node, first_variant=False,
                         include_parsed_shader=True):
        # texture_nodes = []
        # material_main_tex = []
        material_tex_infos = {}
        material_tex_nodes = []
        hlsl_tuple = None
        glsl_tuple = None
        material_info = {}
        data_dict = node.obj.object_reader.read_typetree()
        nodes_dict = self.parent.nodes_dict

        mat_properties = {}
        for i in data_dict['m_SavedProperties']['m_TexEnvs']:
            texture = i[1]['m_Texture']
            if texture['m_PathID'] != 0:
                iden = (node.dependencies[texture['m_FileID'] - 1] if texture[
                                                                            'm_FileID'] > 0 else node.cab) + str(
                    texture['m_PathID'])
                if _target := nodes_dict.get(iden):
                    # texture_nodes.append(_target)
                    material_tex_nodes.append(_target)
                    # if i[0] == '_MainTex':
                    #     material_main_tex.append(_target.name)
                    texture_settings = _target.obj.m_TextureSettings
                    sampler = {
                        'aniso': texture_settings.m_Aniso,  # 各向异性
                        'filterMode': texture_settings.m_FilterMode,
                        'mipBias': texture_settings.m_MipBias,
                        # 'wrapMode': texture_settings['m_WrapMode'],
                        'wrapU': texture_settings.m_WrapU,
                        'wrapV': texture_settings.m_WrapV,
                        'wrapW': texture_settings.m_WrapW
                    }
                    material_tex_infos[i[0]] = {
                        'name': _target.name,
                        'scalar': i[1]['m_Scale'],
                        'offset': i[1]['m_Offset'],
                        'sampler': sampler
                    }
                    mat_properties[i[0]] = _target.name

        for i in data_dict['m_SavedProperties']['m_Ints']:
            mat_properties[i[0]] = i[1]
        for i in data_dict['m_SavedProperties']['m_Floats']:
            mat_properties[i[0]] = i[1]
        for i in data_dict['m_SavedProperties']['m_Colors']:
            mat_properties[i[0]] = (i[1]['r'], i[1]['g'], i[1]['b'], i[1]['a'])

        if shader_node := node.children.get('m_Shader', None):
            material_info['shader'] = shader_node.name

            valid_keywords = data_dict['m_ValidKeywords']
            invalid_keywords = data_dict['m_InvalidKeywords']
            hlsl, properties, keywords, blend_info, render_queue = get_variant_shader_data(
                valid_keywords, invalid_keywords, shader_node.name, first_variant=first_variant)
            material_info['renderQueue'] = data_dict['m_CustomRenderQueue'] if data_dict['m_CustomRenderQueue'] >= 0 else render_queue
            variant_crc32 = util.compute_unity_hash(''.join(keywords))
            shader_name_with_variant = f'{shader_node.name}-{variant_crc32}'
            material_info['shaderWithVariant'] = shader_name_with_variant
            hlsl_tuple = (shader_name_with_variant, hlsl if util.EXPORT_HLSL_SHADER else None)
            if include_parsed_shader:
                vert, frag = get_parsed_shader(shader_name_with_variant)
                glsl_tuple = (shader_name_with_variant, vert, frag)
            for k, v in properties.items():
                if (tar := mat_properties.get(k, None)) is not None:
                    v['value'] = tar
            material_info['properties'] = properties
            material_info['blendInfo'] = resolve_blend_info(blend_info, properties, mat_properties)

        # return material_info, material_main_tex, material_tex_infos, hlsl_tuple, glsl_tuple, material_tex_nodes
        return material_info, material_tex_infos, hlsl_tuple, glsl_tuple, material_tex_nodes
