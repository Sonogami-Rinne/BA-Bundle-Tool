import os
import UnityPy
from UnityPy.helpers import CompressionHelper
from shaderTool.BlobReader import blob_reader
from shaderTool.ShaderConverter import export_shader
from shaderTool.ShaderInfoCombiner import combine_info
from util import better_print

file = r'C:\Users\Administrator\Desktop\assets-_mx-shaders-_mxdependency-shaders-2025-07-02_assets_all_2493779052.bundle'
# file = r'C:\Users\Administrator\Desktop\prologdepengroup-assets-_mx-shaders-_mxprolog-2025-07-02_assets_all_1537986602.bundle'
# file = r'prologdepengroup-assets-_mx-shaders-_mxprolog-2025-07-02_assets_all_1537986602.bundle'
env = UnityPy.load(file)
a = 0
for obj in env.objects:
    if obj.type.name == 'Shader':
        a += 1
        # if a <= 77:
        #     continue

        data = obj.parse_as_object()
        data1 = obj.parse_as_dict()
        shader_name = data1['m_ParsedForm']['m_Name']
        if shader_name != 'DSFX/FX_SHADER_AlphaBlend_Add_Distort_1a':
            continue
        compressed_blob = bytes(data1['compressedBlob'])
        platform_index = data1['platforms'].index(4)
        ori_shader_export = export_shader(data)
        buffers = []
        for part_index, offset in enumerate(data1['offsets'][platform_index]):
            decompressed_length = data1['decompressedLengths'][platform_index][part_index]
            compressed_length = data1['compressedLengths'][platform_index][part_index]
            decompressedBytes = CompressionHelper.decompress_lz4(compressed_blob[offset:offset + compressed_length],
                                                                 decompressed_length)
            buffers.append(decompressedBytes)

        with open("E:\\test.bin", 'wb+') as f:
            f.write(b''.join(buffers))
        shader_info = blob_reader(buffers)
        combined_shader = combine_info(data1, shader_info, ori_shader_export)

        with open('E:\\1.shader', 'w+', encoding='utf-8') as f:
            f.write(better_print(combined_shader))

        print(a)
        b = 1
        b += 1
