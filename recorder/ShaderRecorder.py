import json
import os
import pathlib
import re

import util
from recorder.BaseRecorder import BaseRecorder
from shaderTool.BlobReader import blob_reader
from util import ClassIDType, CLogging, better_print, compute_unity_hash
from UnityPy.helpers import CompressionHelper
from shaderTool.ShaderConverter import export_shader, ConvertSerializedPropertyToDict
from shaderTool.ShaderInfoCombiner import combine_info

render_queue_map = {
    'Background': 1000,
    'Geometry': 2000,
    'AlphaTest': 2450,
    'Transparent': 3000,
    'Overlay': 4000
}
render_queue_reg = r'([a-zA-Z]+)([+/-]?[0-9]*)'

class ShaderRecorder(BaseRecorder):
    def __init__(self):
        super().__init__()
        save_file = f'.\\save\\recorder\\{ShaderRecorder.__class__.__name__}\\shadermap.json'
        if pathlib.Path(save_file).exists():
            with open(save_file, 'r') as f:
                self.batch_data = json.load(f)


    def notify_single(self, node):
        if node.type != ClassIDType.Shader:
            return
        data_dict = node.obj.object_reader.parse_as_dict()
        shader_name = data_dict['m_ParsedForm']['m_Name']
        buffers = []
        compressed_bytes = bytes(data_dict['compressedBlob'])
        platform_index = data_dict['platforms'].index(4)
        for part_index, offset in enumerate(data_dict['offsets'][platform_index]):
            decompressed_length = data_dict['decompressedLengths'][platform_index][part_index]
            compressed_length = data_dict['compressedLengths'][platform_index][part_index]
            decompressedBytes = CompressionHelper.decompress_lz4(compressed_bytes[offset:offset + compressed_length],
                                                                 decompressed_length)
            buffers.append(decompressedBytes)
        crc_shader_info = blob_reader(buffers, decompile=False)
        variant_bytecode_crc32 = self._get_variant_bytecode_crc32(crc_shader_info)
        old_shader_info = self.batch_data.get(shader_name)
        old_variant_bytecode_crc32 = (
            old_shader_info.get('variantBytecodeCrc32', {})
            if isinstance(old_shader_info, dict) else {}
        )
        if old_shader_info is not None and old_variant_bytecode_crc32 == variant_bytecode_crc32:
            return

        self._log_variant_changes(
            shader_name, old_variant_bytecode_crc32, variant_bytecode_crc32
        )
        unitypy_shader_export = export_shader(node.obj)
        shader_info = blob_reader(buffers)
        combined_shader = combine_info(data_dict, shader_info, unitypy_shader_export)
        self._c_save_data(f'./save/recorder/ShaderRecorder/shader/{shader_name}.shader', better_print(combined_shader))

        shader_keywords = data_dict['m_ParsedForm']['m_KeywordNames']
        shader_keyword_default_flags = data_dict['m_ParsedForm']['m_KeywordFlags']
        properties = ConvertSerializedPropertyToDict(data_dict['m_ParsedForm']['m_PropInfo']['m_Props'])
        shader_blend_mode = None
        shader_queue_info = None
        forward_flag = False
        for sub_shader in data_dict['m_ParsedForm']['m_SubShaders']:
            for pass_info in sub_shader['m_Passes']:
                state = pass_info['m_State']
                if shader_blend_mode is None or state['m_Name'] == 'Forward':
                    rt = state['rtBlend0']
                    forward_flag = state['m_Name'] == 'Forward'
                    shader_blend_mode = {
                        'srcBlend': rt['srcBlend']['val'],
                        'dstBlend': rt['destBlend']['val'],
                        'srcBlendAlpha': rt['srcBlendAlpha']['val'],
                        'dstBlendAlpha': rt['destBlendAlpha']['val'],
                        'blendOp': rt['blendOp']['val'],
                        'blendOpAlpha': rt['blendOpAlpha']['val'],
                        'colMask': rt['colMask']['val']
                    }
                if forward_flag:
                    break

            if forward_flag or shader_queue_info is None:
                queue_tag = None
                for tag in sub_shader['m_Tags']['tags']:
                    if tag[0].lower() == 'queue':
                        queue_tag = tag[1]
                        break
                if queue_tag is None:
                    util.CLogging.warn(f'Shader queue tag not found, fallback to Background')
                    queue_tag = 'Background'
                reg_groups = re.match(render_queue_reg, queue_tag).groups()
                render_queue = render_queue_map[reg_groups[0]]
                if reg_groups[1] != '':
                    render_queue += int(reg_groups[1])
                shader_queue_info = render_queue
            if forward_flag:
                break
        self.batch_data[shader_name] = {
            'keywords': shader_keywords,
            'enableFlag': shader_keyword_default_flags,
            'properties': properties,
            'blendMode': shader_blend_mode or {},
            'variantBytecodeCrc32': variant_bytecode_crc32,
            'renderQueue': shader_queue_info
        }

    @staticmethod
    def _get_variant_bytecode_crc32(shader_info):
        result = {}
        for block in shader_info['blockData']:
            if 'dxbcCrc32' not in block:
                continue
            keyword_crc32 = str(compute_unity_hash(''.join(block['keywords'])))
            result.setdefault(keyword_crc32, []).append(block['dxbcCrc32'])
        for crc32_values in result.values():
            crc32_values.sort()
        return result

    @staticmethod
    def _log_variant_changes(shader_name, old_crc32, new_crc32):
        for keyword_crc32, bytecode_crc32 in new_crc32.items():
            if keyword_crc32 not in old_crc32:
                CLogging.info(
                    f'Shader变体新增: {shader_name}, keywords CRC32={keyword_crc32}, '
                    f'DXBC CRC32={bytecode_crc32}'
                )
            elif old_crc32[keyword_crc32] != bytecode_crc32:
                CLogging.info(
                    f'Shader变体更新: {shader_name}, keywords CRC32={keyword_crc32}, '
                    f'DXBC CRC32={old_crc32[keyword_crc32]} -> {bytecode_crc32}'
                )
        for keyword_crc32 in old_crc32.keys() - new_crc32.keys():
            CLogging.info(
                f'Shader变体移除: {shader_name}, keywords CRC32={keyword_crc32}'
            )

    def notify_total(self):
        self._save_data('shadermap')

    def _c_save_data(self, path, data):
        os.makedirs(path[:path.rindex('/')], exist_ok=True)
        with open(path, 'w+', encoding='utf-8') as f:
            f.write(data)
