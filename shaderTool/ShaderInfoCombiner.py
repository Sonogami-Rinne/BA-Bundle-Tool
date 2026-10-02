import re

reg_constant_buffer_declaration_operation = r'(\s*cbuffer\s*)(.*?)(\s*:.*)'
reg_global_variable_declaration_operation = r'(\s*)(\S*)(\s*)([^[]*)((?:\[\d+\])?)( : register[^0-9]*)([0-9]+)(.*)'
reg_variable_declaration_operation = r'(\s*)((?:(?:float)|(?:int)|(?:uint))[1-4]?)(\s*)(.*)(\s*;)'
reg_variable_declaration_extraction_findall = r'\s*([^,]+)\s*'
reg_variable_name_declaration_extraction = r'(\w+)((?:\[\d+\])?)'
reg_token = r'(\w+)(\W)'
reg_space = r'\s*'


def parse_shader_export(shader_export):
    """
    将由UnityPy导出的shader内容切割，以将类似GPUProgram ID 12345替换成具体的代码
    :param shader_export:
    :return:
    """
    parts = []
    content = ''
    GPU_program_ID_poi = []
    sub_shader_index = 0
    pass_index = 0

    status_stack = []
    for line in shader_export.split('\n'):
        ls = line.lstrip()
        if ls.startswith('SubShader {'):
            pass_index = 0
            status_stack.append('SubShader')
            parts.append(content)
            content = line
        elif ls.startswith('Pass {'):
            status_stack.append('Pass')
            parts.append(content)
            content = line
        elif ls.startswith('GpuProgramID'):
            parts.append(content)

            GPU_program_ID_poi.append((len(parts), sub_shader_index, pass_index))
            parts.append(line)
            content = ''
        elif ls.startswith('}'):
            content += line
            content += '\n'
            if len(status_stack) > 0:
                sta = status_stack.pop()
                parts.append(content)
                content = ''
                if sta == 'Pass':
                    pass_index += 1
                else:
                    sub_shader_index += 1
        else:
            content += line
            content += '\n'
    parts.append(content)
    return parts, GPU_program_ID_poi


def parse_hlsl_shader(hlsl_shader):
    """
    将由3dmigoto反编译得到的hlsl文件切割，以替换其中的变量名字为其对应的property名字
    :param hlsl_shader:
    :return:
    """
    parts = []
    content = ''
    variable_map = {}
    cbuffer_map = {}
    global_variable_map = {}
    migoto_declaration = False
    cb_index = None

    def add(nam, var_type, dic, suffix, slot_index=None):
        if not (tar := dic.get(nam)):
            tar = {
                'type': var_type,
                'poi': [],
                'suffix': suffix
            }
            if slot_index is not None:
                tar['index'] = slot_index
            dic[nam] = tar
        tar = tar['poi']
        tar.append(len(parts))

    def test_and_add(nam):
        if not ((tar := variable_map.get(nam)) or (tar := global_variable_map.get(nam))):
            return False
        tar['poi'].append(len(parts))
        return True

    def test(nam):
        return nam in variable_map or nam in global_variable_map

    void_main_flag = False
    function_body_flag = False

    for line in hlsl_shader.split('\n'):
        ls = line.lstrip()

        if migoto_declaration:
            if ls != '':
                continue
            else:
                migoto_declaration = False
        if ls.startswith('void main'):
            void_main_flag = True
        if function_body_flag and ls.startswith('}'):
            function_body_flag = False
            void_main_flag = False

        if function_body_flag and re.match(reg_variable_declaration_operation, line) is None:
            ls = re.sub(reg_space, '', ls)
            middle_bracket_flag = False
            dot_flag = False
            while len(ls) > 0:
                if _tmp := re.match(reg_token, ls):
                    toke, symbol = _tmp.group(1), _tmp.group(2)
                    ls = ls[len(toke) + len(symbol):]
                    if dot_flag:
                        content += toke
                        parts.append(content)
                        toke = ''
                        content = ''
                        dot_flag = False

                    if symbol == '[':
                        middle_bracket_flag = True
                        parts.append(content)
                        test_and_add(toke)
                        parts.append(toke)
                        content = symbol
                        continue

                    if symbol == ']':
                        if middle_bracket_flag:
                            if toke.isnumeric():
                                content += toke + symbol
                                parts.append(content)
                                content = ''
                            else:
                                if test(toke):
                                    if content:
                                        parts.append(content)
                                    test_and_add(toke)
                                    parts.append(toke)
                                    content = symbol
                                else:
                                    content += toke + symbol
                            middle_bracket_flag = False
                        else:
                            if test(toke):
                                if content:
                                    parts.append(content)
                                test_and_add(toke)
                                parts.append(toke)
                                content = symbol
                            else:
                                content += toke + symbol
                        continue

                    middle_bracket_flag = False
                    if symbol == '.':
                        if content:
                            parts.append(content)
                        test_and_add(toke)
                        parts.append(toke)
                        content = symbol
                        dot_flag = True
                    elif symbol == '(' or symbol == ')':
                        content += toke + symbol
                    else:
                        content += toke
                        if symbol in [',', ';']:
                            content += symbol
                        else:
                            content += f' {symbol} '
                else:
                    symbol = ls[0]
                    ls = ls[1:]
                    if symbol == '.':  # ].
                        dot_flag = True
                        content += symbol
                    else:
                        if symbol == '=':
                            content = content.rstrip() + symbol + ' '
                        elif symbol == '(':
                            content = content + symbol
                        else:
                            content = content + symbol + ' '
                        # content = content.rstrip() + symbol + ' '
            content += '\n'
        elif match := re.match(reg_constant_buffer_declaration_operation, line):
            match = match.groups()
            parts.append(content + match[0])
            cbuffer_map[match[1]] = {
                'line': len(parts),
                'variables': []
            }
            cb_index = match[1]
            parts.append(match[1])
            parts.append(match[2] + '\n')
            content = ''
        elif match := re.match(reg_variable_declaration_operation, line):
            match = match.groups()
            parts.append(content)
            parts.append(match[0])
            parts.append(match[1])
            parts.append(match[2])
            for ma in re.findall(reg_variable_declaration_extraction_findall, match[3]):
                _match = re.match(reg_variable_name_declaration_extraction, ma).groups()
                add(_match[0], match[1], variable_map, _match[1])
                parts.append(_match[0])
                parts.append(_match[1])
                parts.append(',')
                if cb_index is not None:
                    cbuffer_map[cb_index]['variables'].append(_match[0])
            parts.pop()
            parts.append(match[4] + '\n')
            content = ''
        elif match := re.match(reg_global_variable_declaration_operation, line):
            match = match.groups()
            parts.append(content + match[0] + match[1] + match[2])
            add(match[3], match[1], global_variable_map, match[4], int(match[6]))
            parts.append(match[3])
            parts.append(match[4] + match[5] + match[6] + match[7] + '\n')
            content = ''
        elif ls.startswith('// 3Dmigoto declarations'):
            parts.append(content + '\n')
            content = ''
            migoto_declaration = True
        else:
            content += line
            content += '\n'
            if ls.startswith('}'):
                cb_index = None
            elif void_main_flag and ls.startswith('{'):
                function_body_flag = True
    parts.append(content)

    return parts, variable_map, global_variable_map, cbuffer_map


# 忽略Hull, Domain这两个stage
def combine_info(data_dict, blob_shader_info, shader_export):
    blob_shader_info = blob_shader_info['blockData']
    sub_shaders = data_dict['m_ParsedForm']['m_SubShaders']
    # shader_keywords = data_dict['m_ParsedForm']['m_KeywordNames']
    parsed_shader_exports, GPUPoi = parse_shader_export(shader_export)
    hlsl_map = {}
    processed_blob_blocks = set()
    props = set()
    for i in data_dict['m_ParsedForm']['m_PropInfo']['m_Props']:
        props.add(i['m_Name'])

    for index, i in enumerate(blob_shader_info):
        if hlsl := i.get('hlsl_content'):
            hlsl_map[index] = parse_hlsl_shader(hlsl) + (i['keywords'],)

    for line_index, sub_shader_index, pass_index in GPUPoi:
        pass_info = sub_shaders[sub_shader_index]['m_Passes'][pass_index]
        name_map = {i[1]: i[0] for i in pass_info['m_NameIndices']}
        GPU_program_call_cotent = ''

        for shader_stage in ['progVertex', 'progFragment', 'progGeometry']:
            shader_stage_info = pass_info.get(shader_stage)
            if len(shader_stage_info['m_PlayerSubPrograms']) > 0:
                stage_variants_funcs = shader_stage_info['m_PlayerSubPrograms'][3]
                common_parameters = shader_stage_info['m_CommonParameters']
                # constant_buffers = {i['m_NameIndex']: i for i in common_parameters['m_ConstantBuffers']}
                parameter_blob_indices = shader_stage_info['m_ParameterBlobIndices'][3]

                # 收集全局变量信息
                global_variable_infos = []
                for item in common_parameters['m_VectorParams']:
                    global_variable_infos.append({
                        'index': item['m_Index'],
                        'name': name_map[item['m_NameIndex']],
                        'type': f'float{item["m_Dim"]}',
                        'suffix': '' if item['m_ArraySize'] == 0 else f'[{item["m_ArraySize"]}]'
                    })
                for item in common_parameters['m_MatrixParams']:
                    global_variable_infos.append({
                        'index': item['m_Index'],
                        'name': name_map[item['m_NameIndex']],
                        'type': f'float{item["m_RowCount"]}',
                        'suffix': f'[{item["ArraySize"] * item["m_RowCount"]}]'
                    })
                for item in common_parameters['m_TextureParams']:
                    global_variable_infos.append({
                        'index': item['m_Index'],
                        'name': name_map[item['m_NameIndex']],
                        'type': f'Texture{item["m_Dim"]}D<float4>',
                        'suffix': ''
                    })
                # global_variable_infos.sort(key=lambda x: x['index'])

                # 收集在Constant Buffer中的变量信息
                constant_buffer_info_map = {}
                for cbb in common_parameters['m_ConstantBufferBindings']:
                    constant_buffer_info_map[cbb['m_Index']] = {
                        'name': name_map[cbb['m_NameIndex']],
                        'index': cbb['m_Index'],
                        'parameters': []
                    }
                index_less_constant_buffers = {}
                for cb_index, cb_info in enumerate(common_parameters['m_ConstantBuffers']):
                    if not(tar := constant_buffer_info_map.get(cb_index)):
                        tar = {
                            'name': None,
                            'index': cb_index,
                            'parameters': []
                        }
                        index_less_constant_buffers[name_map[cb_info['m_NameIndex']]] = tar
                    parameters = tar['parameters']
                    for item in cb_info['m_VectorParams']:
                        para_offset = item['m_Index'] >> 2
                        para_array_length = item['m_ArraySize']
                        para_array_in_buffer_index = para_offset >> 2
                        para_array_in_buffer_sub_offset = para_offset & 0x3
                        para_size = max(para_array_length, 1) * item['m_Dim']
                        para_end_poi = para_size + para_offset - 1
                        para_array_in_buffer_index_end = para_end_poi >> 2
                        para_array_in_buffer_end_sub_offset = para_end_poi & 0x3

                        parameters.append({
                            'arrayIndex': para_array_in_buffer_index,
                            'arrayIndexOffset': para_array_in_buffer_sub_offset,
                            'arrayIndexValue': para_offset,
                            'arrayEndIndex': para_array_in_buffer_index_end,
                            'arrayEndIndexOffset': para_array_in_buffer_end_sub_offset,
                            'arrayEndIndexValue': para_end_poi,
                            'arrayLength': para_array_length,
                            'name': name_map[item['m_NameIndex']],
                            'type': f'float{item["m_Dim"]}',
                            'dim': item['m_Dim'],
                            'isMatrix': False,
                            'rowCount': 1
                        })
                    for item in cb_info['m_MatrixParams']:
                        para_offset = item['m_Index'] >> 2  # 字偏移
                        para_array_length = item['m_ArraySize']
                        para_array_in_buffer_index = para_offset >> 2
                        para_array_in_buffer_sub_offset = para_offset & 0x3
                        para_size = max(para_array_length, 1) * item['m_RowCount'] * 4  # * dim = 4, 字为单位
                        para_end_poi = para_size + para_offset - 1
                        para_array_in_buffer_index_end = para_end_poi >> 2
                        para_array_in_buffer_end_sub_offset = para_end_poi & 0x3

                        parameters.append({
                            'arrayIndex': para_array_in_buffer_index,
                            'arrayIndexOffset': para_array_in_buffer_sub_offset,
                            'arrayIndexValue': para_offset,
                            'arrayEndIndex': para_array_in_buffer_index_end,
                            'arrayEndIndexOffset': para_array_in_buffer_end_sub_offset,
                            'arrayEndIndexValue': para_end_poi,
                            'arrayLength': para_array_length,
                            'name': name_map[item['m_NameIndex']],
                            'type': f'Matrix{item["m_RowCount"]}x4',
                            'dim': 4,
                            'rowCount': item['m_RowCount'],
                            'isMatrix': True,
                        })
                    for item in cb_info['m_StructParams']:
                        #  暂时不想写这部分，遇到了再说
                        struct_name = name_map[item['m_NameIndex']]
                        assert False

                # 替换变量名字
                for variant_index, variant_func in enumerate(stage_variants_funcs):
                    if variant_func['m_BlobIndex'] not in processed_blob_blocks:
                        processed_blob_blocks.add(variant_func['m_BlobIndex'])
                    else:
                        continue
                    hlsl_parts, hlsl_variable_map, hlsl_global_variable_map, hlsl_cbuffer_map, _ = hlsl_map[variant_func['m_BlobIndex']]

                    blob_index = parameter_blob_indices[variant_index]
                    blob_parameter_infos = blob_shader_info[blob_index]['constantBufferInfo']
                    blob_global_variable_infos = blob_shader_info[blob_index]['globalVariableInfo']

                    merged_constant_buffer_info = {}
                    for item in constant_buffer_info_map.values():
                        merged_constant_buffer_info[item['index']] = {
                            'name': item['name'],
                            'parameters': [i for i in item['parameters']]
                        }

                    for index, item in enumerate(blob_parameter_infos):
                        if _tar := merged_constant_buffer_info.get(index):
                            _tar['parameters'].extend(item['parameters'])
                            _tar['structs'] = item['structs']
                            # _tar['name'] = item['name']
                            # assert _tar['name'] == item['name']

                        elif _tar := index_less_constant_buffers.get(item['name']):
                            parameters = [i for i in _tar['parameters']]
                            parameters.extend(item['parameters'])
                            merged_constant_buffer_info[index] = {
                                'name': item['name'],
                                'parameters': parameters,
                                'structs': item['structs']
                            }
                        else:
                            merged_constant_buffer_info[index] = {
                                'name': item['name'],
                                'parameters': item['parameters'],
                                'structs': item['structs'],
                            }

                    # 替换Constant Buffer名字
                    for k, v in merged_constant_buffer_info.items():
                        var_name = f'cb{k}'
                        ori_name = v['name']
                        hlsl_parts[hlsl_cbuffer_map[var_name]['line']] = ori_name

                    # 替换constant buffer中各个变量的名字
                    for k, v in merged_constant_buffer_info.items():
                        arr = [i for i in v['parameters']]
                        arr.sort(key=lambda x: x['arrayIndexValue'])
                        structs = v['structs']
                        tar_name = f'cb{k}'
                        if tar_name in hlsl_variable_map:

                            pois = hlsl_variable_map[f'cb{k}']['poi']
                            # 先替换CBuffer中的申明
                            indent = hlsl_parts[pois[0] - 3]
                            hlsl_parts[pois[0] - 3] = ''
                            hlsl_parts[pois[0] - 2] = ''
                            hlsl_parts[pois[0] - 1] = ''
                            hlsl_parts[pois[0] + 1] = ''
                            hlsl_parts[pois[0] + 2] = ''

                            converted_lines = ''
                            for ar in arr:
                                line = indent + ar['type'] + ' ' + ar['name']
                                array_length = ar['arrayLength']
                                if array_length > 0:
                                    line += f'[{array_length}]'
                                line += f'    //({ar["arrayIndex"]},{ar["arrayIndexOffset"]})-({ar["arrayEndIndex"]},{ar["arrayEndIndexOffset"]});\n'
                                converted_lines += line
                            for st in structs:
                                line = indent + f'struct {st["name"]}{"" if st["arrayLength"] == 0 else "[" + str(st["arrayLength"]) + "]"}\n' + indent + '{\n'
                                for item in st['parameters']:
                                    line += (f'{indent}{item["type"]} {item["name"]}' + (
                                        '' if item['arrayLength'] == 0 else f'[{item["arrayLength"]}]') + f'    //({item["arrayIndex"]},{item["arrayIndexOffset"]})-({item["arrayEndIndex"]},{item["arrayEndIndexOffset"]});\n')
                                line += '}\n'
                                arr.extend(st['parameters'])
                                converted_lines += line
                            hlsl_parts[pois[0]] = converted_lines

                            for poi in pois[1:]:
                                if len(hlsl_parts[poi + 1]) <= 2:
                                    hlsl_parts[poi] = v['name']
                                    continue

                                items = []
                                ori_appendix = hlsl_parts[poi + 2][1:]
                                variable_array_index = int(hlsl_parts[poi + 1][1:-1])
                                certain_variable_index = None
                                variable_index_value = variable_array_index << 2
                                for char in ori_appendix:
                                    offset_val = ord(char) - 120
                                    if offset_val < 0:
                                        offset_val = 3
                                    offset_val |= variable_index_value

                                    if certain_variable_index is None or ((ar := arr[certain_variable_index]) and (ar['arrayIndexValue'] > offset_val or offset_val > ar['arrayEndIndexValue'])):
                                        #  二分吗？我不想写了
                                        for _index, ar in enumerate(arr):
                                            if ar['arrayIndexValue'] <= offset_val <= ar['arrayEndIndexValue']:
                                                certain_variable_index = _index
                                                break

                                    ar = arr[certain_variable_index]
                                    _item_name = ar['name']
                                    _item_suffix = ''
                                    parameter_dim = ar['dim']
                                    array_index_distance = offset_val - ar['arrayIndexValue']
                                    converted_array_index = array_index_distance // parameter_dim
                                    if ar['isMatrix'] or ar['arrayLength'] > 0:
                                        if ar['arrayLength'] > 0 and ar['isMatrix']:
                                            _item_suffix = f'[{converted_array_index // ar["rowCount"]}][{converted_array_index % ar["rowCount"]}]'
                                        else:
                                            _item_suffix = f'[{converted_array_index}]'
                                    if parameter_dim > 1:
                                        chr_distance = (offset_val - ar['arrayIndexOffset'] + 4) % parameter_dim
                                        if chr_distance == 3:
                                            chr_distance = -1
                                        _item_appendix = chr(120 + chr_distance)
                                    else:
                                        _item_appendix = ''
                                    if len(items) > 0 and items[-1][0] == _item_name and items[-1][
                                        1] == _item_suffix and parameter_dim > 1:
                                        items[-1][2] = items[-1][2] + _item_appendix
                                    else:
                                        items.append([_item_name, _item_suffix, _item_appendix])
                                # items = [i[0] + i[1] + i[2] for i in items]

                                first_item = items[0]
                                if first_item[2] == '':
                                    flag = True
                                    for item in items:
                                        if item[0] != first_item[0]:
                                            flag = False
                                            break
                                    if flag:
                                        items = items[:1]
                                items = [f'{i[0]}{i[1]}{"" if i[2] == "" else ("." + i[2])}' for i in items]
                                hlsl_parts[poi] = ' , '.join(items)

                                hlsl_parts[poi + 1] = ''
                                hlsl_parts[poi + 2] = ''

                    merged_global_variable_map = global_variable_infos + blob_global_variable_infos
                    merged_global_variable_map.sort(key=lambda x: x['index'])

                    # 替换全局变量名字
                    for global_variable in hlsl_global_variable_map.values():
                        for item in merged_global_variable_map:
                            if global_variable['index'] == item['index'] and global_variable['type'] == item['type'] and \
                                    global_variable['suffix'] == item['suffix']:
                                name = item['name']
                                for poi in global_variable['poi']:
                                    hlsl_parts[poi] = name
                                break
                # 构建
                sub_shader_func_content = '{\n@SHADER_STAGE: ' + shader_stage + '\n\n'

                for variant_index, variant_func in enumerate(stage_variants_funcs):
                    hlsl_parts, _, _, _, sub_pass_keywords = hlsl_map[variant_func['m_BlobIndex']]
                    sub_shader_func_content += ('{\n    @SHADER_KEYWORDS: ' + ','.join(sub_pass_keywords) + '\n\n')
                    sub_shader_func_content += (''.join(hlsl_parts) + '\n}\n')

                sub_shader_func_content += '}\n'
                GPU_program_call_cotent += sub_shader_func_content

        parsed_shader_exports[line_index] = GPU_program_call_cotent

    return ''.join(parsed_shader_exports)
