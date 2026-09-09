import re

reg_constant_buffer_declaration_operation = r'(\s*cbuffer\s*)(.*?)(\s*:.*)'
reg_global_variable_declaration_operation = r'(\s*)(\S*)(\s*)([^[]*)((?:\[\d+\])?)( : register[^0-9]*)([0-9]+)(.*)'
reg_variable_declaration_operation = r'(\s*)((?:(?:float)|(?:int)|(?:uint))[1-4]?)(\s*)(.*)(\s*;)'
reg_variable_declaration_extraction_findall = r'\s*([^,]+)\s*'
reg_variable_name_declaration_extraction = r'(\w+)((?:\[\d+\])?)'
reg_token = r'(\w+)(\W)'


# reg_variable_name_operation_extraction = r'(\w+)((?:\[\d+\])?)(\.\w+)'
# reg_expression_replacement = r'[()+\-*/><=^&%,!~:?]+'
# reg_space_split = r'\s+'
# reg_calculation_expression = r'(\s*)(.*?)(\s*=\s*)(.*?)(\s*;)'


def parse_shader_export(shader_export):
    parts = []
    content = ''
    GPUProgramIDPoi = []
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

            GPUProgramIDPoi.append((len(parts), sub_shader_index, pass_index))
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
    return parts, GPUProgramIDPoi


def parse_hlsl_shader(hlsl_shader):
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
            ls = re.sub(r'\s*', '', ls)
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


# 忽略Hull, Domain
# 说实话，代码重构Constant Buffer时极度依赖边界对齐这一未确定行为
def combine_info(data_dict, blob_shader_info, shader_export):
    blob_shader_info = blob_shader_info['block_data']
    sub_shaders = data_dict['m_ParsedForm']['m_SubShaders']
    shader_keywords = data_dict['m_ParsedForm']['m_KeywordNames']
    parsed_shader_exports, GPUPoi = parse_shader_export(shader_export)
    hlsl_map = {}
    processed_blob_blocks = set()
    props = set()
    for i in data_dict['m_ParsedForm']['m_PropInfo']['m_Props']:
        props.add(i['m_Name'])

    def get_sub_range(appendix):
        min_val = ord(appendix[1]) - 120
        if min_val < 0:
            min_val = 3
        max_val = ord(appendix[-1]) - 120
        if max_val < 0:
            max_val = 3
        return min_val, max_val

    for index, i in enumerate(blob_shader_info):
        if hlsl := i.get('hlsl_content'):
            hlsl_map[index] = parse_hlsl_shader(hlsl) + (i['keywords'],)

    for line_index, sub_shader_index, pass_index in GPUPoi:
        pass_info = sub_shaders[sub_shader_index]['m_Passes'][pass_index]
        name_map = {i[1]: i[0] for i in pass_info['m_NameIndices']}
        GPU_profram_call_cotent = ''

        for sub_pass_func_name in ['progVertex', 'progFragment', 'progGeometry']:
            sub_pass_func_info = pass_info.get(sub_pass_func_name)
            if len(sub_pass_func_info['m_PlayerSubPrograms']) > 0:
                sub_pass_funcs = sub_pass_func_info['m_PlayerSubPrograms'][3]
                common_parameters = sub_pass_func_info['m_CommonParameters']
                constant_buffers = {i['m_NameIndex']: i for i in common_parameters['m_ConstantBuffers']}
                parameter_blob_indices = sub_pass_func_info['m_ParameterBlobIndices'][3]

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
                    # cb_info = constant_buffers[cbb['m_NameIndex']]
                    if not (cb_info := constant_buffers.get(cbb['m_NameIndex'])):
                        constant_buffer_info_map[cbb['m_Index']] = {
                            'name': name_map[cbb['m_NameIndex']],
                            'index': cbb['m_Index'],
                            'bufferSize': -1,
                            'parameters': []
                        }
                        continue
                    info = {
                        'name': name_map[cbb['m_NameIndex']],
                        'index': cbb['m_Index'],
                        'bufferSize': cb_info['m_Size']
                    }
                    constant_buffer_info_map[cbb['m_Index']] = info

                    cb_variables_infos = []
                    for item in cb_info['m_VectorParams']:
                        para_offset = item['m_Index'] // 4
                        para_array_size = item['m_ArraySize'] if item['m_ArraySize'] > 0 else 1
                        para_array_in_buffer_index = para_offset // 4
                        para_array_in_buffer_sub_offset = para_offset % 4
                        para_size = para_array_size * item['m_Dim']
                        para_array_in_buffer_index_end = (para_size + para_offset - 1) // 4
                        para_array_in_buffer_end_sub_offset = (para_size + para_offset - 1) % 4
                        assert (not (item['m_Dim'] == 4 and para_array_in_buffer_sub_offset != 0))

                        cb_variables_infos.append({
                            'arrayIndex': para_array_in_buffer_index,
                            'arrayIndexOffset': para_array_in_buffer_sub_offset,
                            'arrayIndexValue': para_array_in_buffer_index << 2 | para_array_in_buffer_sub_offset,
                            'arrayEndIndex': para_array_in_buffer_index_end,
                            'arrayEndIndexOffset': para_array_in_buffer_end_sub_offset,
                            'arrayEndIndexValue': para_array_in_buffer_index_end << 2 | para_array_in_buffer_end_sub_offset,
                            'arraySize': para_array_size,
                            'elementSize': item['m_Dim'] * 4,
                            'name': name_map[item['m_NameIndex']],
                            'type': f'float{item["m_Dim"]}',
                            'dim': item['m_Dim'],
                            'isMatrix': False,
                            'offset': item['m_Index']
                        })
                    for item in cb_info['m_MatrixParams']:
                        para_offset = item['m_Index'] // 4  # 字偏移
                        para_array_size = item['m_ArraySize'] if item['m_ArraySize'] > 0 else 1
                        para_array_in_buffer_index = para_offset // 4
                        para_array_in_buffer_sub_offset = para_offset % 4
                        para_size = para_array_size * item['m_RowCount'] * 4  # * dim = 4, 字为单位
                        para_array_in_buffer_index_end = (para_size + para_offset - 1) // 4
                        para_array_in_buffer_end_sub_offset = (para_size + para_offset - 1) % 4

                        cb_variables_infos.append({
                            'arrayIndex': para_array_in_buffer_index,
                            'arrayIndexOffset': para_array_in_buffer_sub_offset,
                            'arrayIndexValue': para_array_in_buffer_index << 2 | para_array_in_buffer_sub_offset,
                            'arrayEndIndex': para_array_in_buffer_index_end,
                            'arrayEndIndexOffset': para_array_in_buffer_end_sub_offset,
                            'arrayEndIndexValue': para_array_in_buffer_index_end << 2 | para_array_in_buffer_end_sub_offset,
                            'arraySize': para_array_size,
                            'elementSize': 16 * item['m_RowCount'],
                            'name': name_map[item['m_NameIndex']],
                            'type': f'Matrix{item["m_RowCount"]}x4',
                            'dim': 4,
                            'rowCount': item['m_RowCount'],
                            'isMatrix': True,
                            'offset': item['m_Index']
                        })
                    for item in cb_info['m_StructParams']:
                        struct_name = name_map[item['m_NameIndex']]
                        assert False

                    info['parameters'] = cb_variables_infos

                # 替换变量名字
                for func_index, sub_pass_func in enumerate(sub_pass_funcs):
                    if sub_pass_func['m_BlobIndex'] not in processed_blob_blocks:
                        processed_blob_blocks.add(sub_pass_func['m_BlobIndex'])
                    else:
                        continue
                    hlsl_parts, hlsl_variable_map, hlsl_global_variable_map, hlsl_cbuffer_map, _ = hlsl_map[
                        sub_pass_func['m_BlobIndex']]

                    blob_index = parameter_blob_indices[func_index]
                    blob_parameter_infos = blob_shader_info[blob_index]['constantBufferInfo']
                    blob_global_variable_infos = blob_shader_info[blob_index]['globalVariableInfos']

                    merged_constant_buffer_info = {}
                    for item in constant_buffer_info_map.values():
                        merged_constant_buffer_info[item['index']] = {
                            'name': item['name'],
                            'parameters': [i for i in item['parameters']],
                            'bufferSize': item['bufferSize']
                        }

                    for index, item in enumerate(blob_parameter_infos):
                        if _tar := merged_constant_buffer_info.get(index):
                            _tar['parameters'].extend(item['parameters'])
                            _tar['structs'] = item['structs']
                            # assert _tar['name'] == item['name']

                            _tar['bufferSize'] = max(item['bufferSize'], _tar['bufferSize'])
                        else:
                            merged_constant_buffer_info[index] = {
                                'name': item['name'],
                                'parameters': item['parameters'],
                                'structs': item['structs'],
                                'bufferSize': item['bufferSize']
                            }

                    # 替换Constant Buffer名字
                    for k, v in merged_constant_buffer_info.items():
                        var_name = f'cb{k}'
                        ori_name = v['name']
                        hlsl_parts[hlsl_cbuffer_map[var_name]['line']] = ori_name

                    for k, v in merged_constant_buffer_info.items():
                        arr = [i for i in v['parameters']]
                        structs = v['structs']
                        tar_name = f'cb{k}'
                        if tar_name in hlsl_variable_map:
                            arrrr = [i for i in arr]
                            for st in structs:
                                arrrr.extend(st['parameters'])

                            #  补全Blob中各个变量的arrayIndexEnd信息
                            arrrr.sort(key=lambda x: x['offset'])
                            arrrr.append({
                                'offset': v['bufferSize']
                            })
                            for item_index in range(len(arrrr) - 1):
                                cur = arrrr[item_index]
                                if cur.get('arrayEndIndex'):
                                    continue
                                #  如果这个属性是自定义的(在props)中，那么可以肯定它们数组长度为1.
                                #  如果是unity内置的，没办法得知，只能尽可能取
                                if cur['name'] in props:
                                    item_end_poi = cur['offset'] + cur['elementSize'] - 1
                                    item_array_size = 1
                                    item_end_word_poi = item_end_poi // 4
                                    item_array_in_buffer_end_index = item_end_word_poi // 4
                                    item_array_in_buffer_end_index_sub_offset = item_end_word_poi % 4
                                else:
                                    item_array_size = (arrrr[item_index + 1]['offset'] - cur['offset']) // cur['elementSize']
                                    item_end_poi = cur['offset'] + cur['elementSize'] * item_array_size - 1  # 最后一个byte位置
                                    item_end_word_poi = item_end_poi // 4  # 最后一个字的位置
                                    item_array_in_buffer_end_index = item_end_word_poi // 4
                                    item_array_in_buffer_end_index_sub_offset = item_end_word_poi % 4
                                cur['arrayEndIndex'] = item_array_in_buffer_end_index
                                cur['arrayEndIndexOffset'] = item_array_in_buffer_end_index_sub_offset
                                cur['arrayEndIndexValue'] = item_array_in_buffer_end_index << 2 | item_array_in_buffer_end_index_sub_offset
                                cur['arraySize'] = item_array_size
                            del arrrr

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
                                array_size = ar['arraySize']
                                if array_size > 1:
                                    line += f'[{array_size}]'
                                line += f'    //({ar["arrayIndex"]},{ar["arrayIndexOffset"]})-({ar["arrayEndIndex"]},{ar["arrayEndIndexOffset"]});\n'
                                converted_lines += line
                            for st in structs:
                                line = indent + f'struct {st["name"]}\n' + indent + '{\n'
                                for item in st['parameters']:
                                    line += (f'{indent}{item["type"]} {item["name"]}' + (
                                        '' if item['arraySize'] == 1 else f'[{item["arraySize"]}]') + f'    //({item["arrayIndex"]},{item["arrayIndexOffset"]})-({item["arrayEndIndex"]},{item["arrayEndIndexOffset"]});\n')
                                line += '}\n'
                                converted_lines += line
                            hlsl_parts[pois[0]] = converted_lines

                            for poi in pois[1:]:
                                if len(hlsl_parts[poi + 1]) <= 2:
                                    hlsl_parts[poi] = v['name']
                                    continue
                                variable_array_index = int(hlsl_parts[poi + 1][1:-1])
                                variable_min_offset, _ = get_sub_range(hlsl_parts[poi + 2])
                                ori_appendix = hlsl_parts[poi + 2][1:]
                                variable_index_value = variable_array_index << 2 | variable_min_offset
                                for ar in arr:
                                    if ar['arrayIndexValue'] <= variable_index_value <= ar['arrayEndIndexValue']:
                                        hlsl_parts[poi] = ar['name']
                                        suffix = ''
                                        parameter_dim = ar['dim']
                                        parameter_element_word_size = ar['elementSize'] // 4  # 单元素所占的字长
                                        array_index_distance = variable_index_value - ar['arrayIndexValue']
                                        # To Do 关于Matrix以及Matrix矩阵
                                        converted_array_index = array_index_distance // parameter_element_word_size
                                        converted_array_sub_offset = array_index_distance % ar['dim']

                                        if ar['isMatrix']:
                                            converted_array_index = array_index_distance // 4
                                        if ar['arraySize'] > 1 or ar['isMatrix']:
                                            suffix = f'[{converted_array_index}]'
                                        hlsl_parts[poi + 1] = suffix
                                        if parameter_dim > 1:
                                            converted_appendix = '.'
                                            first_char_ord = ord(ori_appendix[0])
                                            # variable_index是由后缀的第一个字符计算得来的，因此 converted_array_sub_offset
                                            # 也是第一个字符在variable数组空间中的偏移。举个例子，全局buffer是0.x,0.y,0.z,0.w,1.x...
                                            # 这么排列的，假设这个variable的维度是3，起始是1,那么v0.x对应全局buffer中的0.y,以此类推
                                            # v0.y,v0.z,v1.x...,我们需要计算在全局buffer中后缀各个字符与后缀第一个字符的偏移，再加上
                                            # 第一个字符在variable空间中的偏移，就是对应位置字符在variable中的偏移
                                            for char in ori_appendix:
                                                chr_distance = ord(char) - first_char_ord + converted_array_sub_offset
                                                if chr_distance < 0:
                                                    chr_distance += 4
                                                chr_distance %= parameter_dim
                                                if chr_distance == 3:
                                                    chr_distance = -1
                                                converted_appendix += chr(120 + chr_distance)
                                            hlsl_parts[poi + 2] = converted_appendix
                                        else:
                                            hlsl_parts[poi + 2] = ''
                                        break

                    merged_global_variable_map = global_variable_infos + [i for i in blob_global_variable_infos if
                                                                          i['status'] == 0]
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
                sub_shader_func_content = '{\n' + sub_pass_func_name + '\n\n'

                for func_index, sub_pass_func in enumerate(sub_pass_funcs):
                    hlsl_parts, _, _, _, sub_pass_keywords = hlsl_map[sub_pass_func['m_BlobIndex']]
                    sub_shader_func_content += ('{\n    ' + ','.join(sub_pass_keywords) + '\n\n')
                    sub_shader_func_content += (''.join(hlsl_parts) + '\n\n}')

                sub_shader_func_content += '}'
                GPU_profram_call_cotent += sub_shader_func_content

        parsed_shader_exports[line_index] = GPU_profram_call_cotent

    return ''.join(parsed_shader_exports)
