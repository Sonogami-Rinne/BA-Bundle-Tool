import json
import os
import pathlib

from recorder.BaseRecorder import BaseRecorder
from shaderTool.BlobReader import blob_reader
from util import ClassIDType, better_print
from UnityPy.helpers import CompressionHelper
from shaderTool.ShaderConverter import export_shader, ConvertSerializedPropertyToDict
from shaderTool.ShaderInfoCombiner import combine_info


class ShaderRecorder(BaseRecorder):
    def __init__(self):
        super().__init__()
        save_file = f'.\\save\\recorder\\{ShaderRecorder.__class__.__name__}\\shadermap.json'
        if pathlib.Path(save_file).exists():
            with open(save_file, 'r') as f:
                self.batch_data = json.load(f)


    def notify_single(self, node):
        if node.type != ClassIDType.Shader or node.obj.m_ParsedForm.m_Name in self.batch_data:
            return
        data_dict = node.obj.object_reader.parse_as_dict()
        shader_name = data_dict['m_ParsedForm']['m_Name']
        unitypy_shader_export = export_shader(node.obj)
        buffers = []
        compressed_bytes = bytes(data_dict['compressedBlob'])
        platform_index = data_dict['platforms'].index(4)
        for part_index, offset in enumerate(data_dict['offsets'][platform_index]):
            decompressed_length = data_dict['decompressedLengths'][platform_index][part_index]
            compressed_length = data_dict['compressedLengths'][platform_index][part_index]
            decompressedBytes = CompressionHelper.decompress_lz4(compressed_bytes[offset:offset + compressed_length],
                                                                 decompressed_length)
            buffers.append(decompressedBytes)
        shader_info = blob_reader(buffers)
        combined_shader = combine_info(data_dict, shader_info, unitypy_shader_export)
        self._c_save_data(f'./save/recorder/ShaderRecorder/shader/{shader_name}.shader', better_print(combined_shader))

        shader_keywords = data_dict['m_ParsedForm']['m_KeywordNames']
        shader_keyword_default_flags = data_dict['m_ParsedForm']['m_KeywordFlags']
        properties = ConvertSerializedPropertyToDict(data_dict['m_ParsedForm']['m_PropInfo']['m_Props'])
        self.batch_data[shader_name] = {
            'keywords': shader_keywords,
            'enableFlag': shader_keyword_default_flags,
            'properties': properties
        }

    def notify_total(self):
        self._save_data('shadermap')

    def _c_save_data(self, path, data):
        os.makedirs(path[:path.rindex('/')], exist_ok=True)
        with open(path, 'w+') as f:
            f.write(data)