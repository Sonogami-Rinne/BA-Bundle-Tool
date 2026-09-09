import os
import pathlib
import shutil
import struct
import sys
import io
from UnityPy.enums import ShaderGpuProgramType


def blob_reader(buffers):
    data = {}
    save_path = 'exported'
    os.makedirs(save_path, exist_ok=True)

    pointer = 0
    count = struct.unpack('<i', buffers[0][pointer:pointer + 4])[0]
    pointer += 4
    data['block_count'] = count
    header_size = 12 * count + 4
    if len(buffers) > 1:
        assert header_size == len(buffers[0])
    blocks = []
    for i in range(count):
        blocks.append(struct.unpack('<iii', buffers[0][pointer:pointer + 12]))
        pointer += 12
    data['block_poi'] = blocks
    block_data = []
    data['block_data'] = block_data

    for offset, length, buffer_index in blocks:
        buffer = buffers[buffer_index]
        block_info = {}
        block_data.append(block_info)
        end_poi = offset + length
        pointer = offset

        version, block_type = struct.unpack('<2i', buffer[pointer:pointer + 8])
        pointer += 8

        if 0 < block_type <= 8:
            pointer += 16

            constant_buffer_infos = []
            block_info['constantBufferInfo'] = constant_buffer_infos
            for block_index in range(block_type - 1):
                cb_name_length = struct.unpack('<i', buffer[pointer:pointer + 4])[0]
                pointer += 4
                # cb_name, cb_size = struct.unpack(f'<{cb_name_length}si', buffer[pointer:pointer + cb_name_length + 4])
                cb_name = struct.unpack(f'<{cb_name_length}s', buffer[pointer:pointer+cb_name_length])[0].decode('utf-8')
                pointer += cb_name_length
                pointer += (0 if (pointer % 4 == 0) else (4 - pointer % 4))
                cb_size = struct.unpack('<i', buffer[pointer:pointer+4])[0]
                pointer += 4

                parameter_infos = []
                struct_infos = []
                constant_buffer_info = {
                    'bufferSize': cb_size,
                    'name': cb_name,
                    'parameters': parameter_infos,
                    'structs': struct_infos
                }
                constant_buffer_infos.append(constant_buffer_info)

                parameter_count = struct.unpack('<i', buffer[pointer:pointer+4])[0]
                pointer += 4

                for parameter_index in range(parameter_count):
                    parameter_name_length = struct.unpack('<i', buffer[pointer:pointer + 4])[0]
                    pointer += 4
                    parameter_name = struct.unpack(f'<{parameter_name_length}s',
                                                   buffer[pointer:pointer + parameter_name_length])[0].decode(
                        'utf-8')
                    pointer += parameter_name_length
                    pointer += (0 if (pointer % 4 == 0) else (4 - pointer % 4))
                    pointer += 4
                    parameter_row_count, parameter_dim, is_matrix, parameter_offset = struct.unpack('<iiqi', buffer[
                                                                                                      pointer:pointer + 20])
                    pointer += 20

                    para_offset = parameter_offset // 4
                    # para_array_size = parameter_array_size if parameter_array_size > 0 else 1
                    para_array_index = para_offset // 4
                    para_array_sub_offset = para_offset % 4
                    para_element_size = 4 * parameter_row_count * parameter_dim
                    parameter_info = {
                        'arrayIndex': para_array_index,
                        'arrayIndexOffset': para_array_sub_offset,
                        'arrayIndexValue': para_array_index << 2 | para_array_sub_offset,
                        'elementSize': para_element_size,
                        'type': f'Matrix{parameter_row_count}x{parameter_dim}' if is_matrix else f'float{parameter_dim}',
                        'dim': parameter_dim,
                        'name': parameter_name,
                        'offset': parameter_offset,
                        'isMatrix': is_matrix == 1,
                        'rowCount': parameter_row_count
                    }
                    assert parameter_row_count == 1 or is_matrix

                    parameter_infos.append(parameter_info)

                # pointer += 4
                structs_count = struct.unpack('<i', buffer[pointer:pointer + 4])[0]
                pointer += 4

                for struct_index in range(structs_count):
                    struct_name_length = struct.unpack('<i', buffer[pointer:pointer+4])[0]
                    pointer += 4
                    struct_name = struct.unpack(f'<{struct_name_length}s', buffer[pointer:pointer+struct_name_length])[0].decode('utf-8')
                    pointer += struct_name_length
                    pointer += (0 if (pointer % 4 == 0) else (4 - pointer % 4))
                    struct_offset, unresolved2, struct_size, struct_item_counts = struct.unpack('<iiii', buffer[pointer:pointer+16])
                    pointer += 16
                    struct_items = []
                    struct_info = {
                        'name': struct_name,
                        'index': struct_offset,
                        'unresolvedProperties': unresolved2,
                        'struct_size': struct_size,
                        'parameters': struct_items
                    }
                    struct_infos.append(struct_info)
                    for struct_item_index in range(struct_item_counts):
                        item_name_length = struct.unpack('<i', buffer[pointer:pointer+4])[0]
                        pointer += 4
                        item_name = struct.unpack(f'<{item_name_length}s', buffer[pointer:pointer+item_name_length])[0].decode('utf-8')
                        pointer += item_name_length
                        pointer += (0 if (pointer % 4 == 0) else (4 - pointer % 4))
                        unresolved, item_row_count, item_dim, is_matrix, unresolved2, item_offset = struct.unpack('<iiiiii', buffer[pointer:pointer+24])
                        pointer += 24

                        item_offset = item_offset // 4  # 先转化为字
                        item_array_index = item_offset // 4  # 一个array中float4,故数组下标还要除4
                        item_array_sub_offset = item_offset % 4
                        item_element_size = 4 * item_row_count * item_dim
                        item_info = {
                            'arrayIndex': item_array_index,
                            'arrayIndexOffset': item_array_sub_offset,
                            'arrayIndexValue': item_array_index << 2 | item_array_sub_offset,
                            'elementSize': item_element_size,
                            'type': f'Matrix{item_row_count}x{item_dim}' if is_matrix else f'float{item_dim}',
                            'dim': item_dim,
                            'name': item_name,
                            'offset': item_offset,
                            'unresolved': (unresolved, unresolved2),
                            'isMatrix': is_matrix == 1
                        }
                        assert item_row_count == 1 or is_matrix
                        struct_items.append(item_info)

            global_variables_count = struct.unpack('<i', buffer[pointer:pointer+4])[0]
            pointer += 4
            global_variable_info = []
            block_info['globalVariableInfos'] = global_variable_info
            for i in range(global_variables_count):
                str_length = struct.unpack('<i', buffer[pointer:pointer+4])[0]
                pointer += 4
                variable_name = struct.unpack(f'<{str_length}s', buffer[pointer:pointer + str_length])[0].decode(
                    'utf-8')
                pointer += str_length
                pointer += (0 if (pointer % 4 == 0) else (4 - pointer % 4))
                is_constant_buffer = struct.unpack('<i', buffer[pointer:pointer+4])[0]
                pointer += 4
                # variable_name, is_constant_buffer = struct.unpack(f'<{str_length}si', buffer[pointer:pointer+str_length+4])
                # variable_name = variable_name.decode('utf-8')

                if is_constant_buffer == 0:
                    un_property0, un_property1, un_property2 = struct.unpack('<iii', buffer[pointer:pointer+12])
                    pointer += 12
                    global_variable_info.append({
                        'index': un_property0,
                        'suffix': '' if un_property1 == 0 else f'[{un_property1}]',
                        'name': variable_name,
                        'status': is_constant_buffer,
                        'properties': (un_property0, un_property1, un_property2),
                        'type': 'Texture2D<float4>' if un_property2 == 4 else 'float4'
                    })
                    assert un_property2 == 4
                else:
                    un_property0, un_property1 = struct.unpack('<ii', buffer[pointer:pointer+8])
                    pointer += 8
                    global_variable_info.append({
                        'name': variable_name,
                        'status': is_constant_buffer,
                        'properties': (un_property0, un_property1)
                    })



        elif 15 <= block_type <= 22:
            unresolved, _, unresolved2, keywords_count = struct.unpack('<iqii', buffer[pointer:pointer + 20])
            pointer += 20
            block_info['unresolved'] = unresolved
            block_info['unresolved2'] = unresolved2
            block_info['keywords'] = []
            while keywords_count > 0:
                keywords_count -= 1
                keyword_length = struct.unpack('<i', buffer[pointer: pointer + 4])[0]
                pointer += 4
                keyword_str = struct.unpack(f'<{keyword_length}s', buffer[pointer:pointer + keyword_length])[0].decode('utf-8')
                pointer += keyword_length
                pointer += (0 if (pointer % 4 == 0) else (4 - pointer % 4))
                block_info['keywords'].append(keyword_str)
            pointer += (0 if (pointer % 4 == 0) else (4 - pointer % 4))

            unresolved, unresolved2 = struct.unpack('<ii', buffer[pointer:pointer + 8])
            pointer += 8
            block_info['unresolved3'] = unresolved
            block_info['unresolved4'] = unresolved2
            pointer += 34
            dxbc_length = struct.unpack('<i', buffer[pointer + 24:pointer + 28])[0]
            dxbc_content = buffer[pointer:pointer + dxbc_length]
            block_info['after_dxbc'] = buffer[pointer + dxbc_length:end_poi]

            bin_file_name = os.path.join(save_path, '1.bin')
            hlsl_file_name = os.path.join(save_path, '1.hlsl')
            with open(bin_file_name, 'wb+') as f:
                f.write(dxbc_content)
            os.system(rf'.\shaderTool\tools\cmd_Decompiler.exe -D .\{bin_file_name}')
            with open(hlsl_file_name, 'r') as f:
                block_info['hlsl_content'] = f.read()
        else:
            assert False
    shutil.rmtree(save_path)
    return data
