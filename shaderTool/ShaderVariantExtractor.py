import copy
import json
import pathlib

from util import CLogging


def extract_variant(shader_content, enabled_keywords):
    parts = shader_content.split('\n')
    line_index = 0
    variant_index = []
    while line_index < len(parts):
        while line_index < len(parts) and not (line := parts[line_index]).lstrip().startswith(
                '@SHADER_STAGE:'):  # 寻找SHADER_STAGE
            line_index += 1
        variants = []
        if line_index >= len(parts):
            break
        line_index += 1
        while not ((line := parts[line_index].lstrip()).startswith('@SHADER_KEYWORDS') or line.startswith(
                '}')):  # 寻找stage中的每个变体,或者当前stage结束
            line_index += 1
        while not (line := parts[line_index].lstrip()).startswith('}'):  # 遍历当前stage
            if len(line) == 0:
                line_index += 1
                continue

            while not line.startswith('@SHADER_KEYWORDS'):  # 如果非空行还不是结尾('}'),那么说明还有variant没记录
                line_index += 1
                line = parts[line_index].lstrip()
            cur_keywords = line[17:].replace(' ', '').split(',')
            if len(cur_keywords) == 1 and cur_keywords[0] == '':  # ''.split(',') -> ['']
                cur_keywords = []
            line_index2 = line_index + 1
            big_bracket_balance = 1
            while big_bracket_balance > 0:  # 找到当前variant的结尾
                _ls = parts[line_index2].lstrip()
                if len(_ls) == 0:
                    line_index2 += 1
                    continue
                if _ls[0] == '{':
                    big_bracket_balance += 1
                elif _ls[0] == '}':
                    big_bracket_balance -= 1
                line_index2 += 1
            variants.append({
                'keywords': cur_keywords,
                'begin': line_index - 1,
                'end': line_index2
            })
            line_index = line_index2

        first_variant_start = variants[0]['begin']
        max_matched_count = -1
        max_matched_index = 0
        for index, variant in enumerate(variants):
            cur_matched = 0
            for keyword in variant['keywords']:
                if keyword in enabled_keywords:
                    cur_matched += 1
            if cur_matched > max_matched_count:
                max_matched_index = index
        variant_index.append(max_matched_index)
        max_matched_parts_length = variants[max_matched_index]['end'] - variants[max_matched_index]['begin']
        del variants[max_matched_index]
        variants.reverse()
        for variant in variants:
            del parts[variant['begin']:variant['end']]
        line_index = first_variant_start + max_matched_parts_length
    return '\n'.join(parts), variant_index


shader_info = {}
file_path = '.\\save\\recorder\\ShaderRecorder\\shadermap.json'
if pathlib.Path(file_path).exists():
    with open(file_path, 'r', encoding='utf-8') as f:
        shader_info = json.load(f)
else:
    CLogging.error('shadermap.json not found')


def get_variant_shader_data(valid_keywords, invalid_keywords, shader_name):
    info = shader_info.get(shader_name)
    if info is None:
        CLogging.error('Unrecorded shader: ' + shader_name)
        return None
    variant_keywords = set([i for keyword_index, i in enumerate(info['keywords']) if info['enableFlag'] == 1])
    original_keywords = set(info['keywords'])
    for i in valid_keywords:
        if i in original_keywords:
            variant_keywords.add(i)
    for i in invalid_keywords:
        if i in variant_keywords:
            variant_keywords.remove(i)

    file_path = './save/recorder/ShaderRecorder/shader/' + shader_name + '.shader'
    if not pathlib.Path(file_path).exists():
        CLogging.error('Shader file not found: ' + shader_name)
        return None

    with open(file_path, 'r', encoding='utf-8') as f:
        shader_content = f.read()
    hlsl, varient_index = extract_variant(shader_content, variant_keywords)

    return hlsl, copy.deepcopy(info['properties']), varient_index
