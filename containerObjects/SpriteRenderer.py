import os
import pathlib

import util
from containerObjects.ContainerObject import ContainerObject
from typeId import ClassIDType
from util import to_tuple


class SpriteRender(ContainerObject):

    def __init__(self, parent_container):
        super().__init__(parent_container)
        self.sprites = []
        self.textures = []
        self.hlsls = {}
        self.glsls = {}

    def test_and_add(self, node):
        if node.type == ClassIDType.SpriteRenderer:
            self.nodes[node.get_identification()] = node
            return True
        return False

    def process(self):
        nodes_dict = self.parent_container.nodes_dict
        game_object_container = self.parent_container.container_objects['GameObject']
        for _, node in self.nodes.items():
            obj = node.obj

            dependencies = node.dependencies


            item = {
                'sprite': node.children['m_Sprite'].name,
                'color': to_tuple(obj.m_Color),
                'flip': (obj.m_FlipX, obj.m_FlipY),
                # 'material': obj.m_Materials,
                # 'materials': [
                #     material for material in obj.m_Materials
                # ],
                'drawMode': obj.m_DrawMode,
                'sortingLayer': obj.m_SortingLayer,
                'maskInteraction': obj.m_MaskInteraction,
                # 'gameObject': game_object_container.get_index(node.children['m_GameObject'].get_identification()),
                # 'gameObjectName': node.children['m_GameObject'].name,  # 如果是Glow的话直接用css渲染，不走pixi了
                # 'translate': translate,
                # 'rotation': rotation,
                # 'scale': scale
            }
            if game_object := node.children.get('m_GameObject'):
                translate, rotation, scale = util.decompose_2d_transform(util.get_transform(game_object))
                item['gameObject'] = game_object_container.get_index(game_object.get_identification())
                item['gameObjectName'] = game_object.name
                item['translate'] = translate
                item['rotation'] = rotation
                item['scale'] = scale

            else:
                item['gameObject'] = -1

            material_main_texs = []
            material_infos = []
            material_tex_infos = []
            for material in obj.m_Materials:
                material_info, material_main_tex, material_tex_info, hlsl_info, glsl_info, material_node = self.process_material(
                    node, material.m_FileID, material.m_PathID)
                if len(material_info) == 0:
                    continue
                material_infos.append(material_info)
                material_main_texs.extend(material_main_tex)
                material_tex_infos.append(material_tex_info)
                self.textures.extend(material_node)
                # self.hlsls[hlsl_info[0]] = hlsl_info[1]
                if hlsl_info[1] is not None:
                    self.hlsls[hlsl_info[0]] = hlsl_info[1]
                if glsl_info[1] is not  None:
                    self.glsls[glsl_info[0]] = glsl_info

            # item['textures'] = texture_nodes
            item['materialInfo'] = material_infos
            item['materialsMainTex'] = material_main_texs
            item['texInfo'] = material_tex_infos

            self.data.append(item)
            self.sprites.append(node.children['m_Sprite'])
            self.data_keys.append(node.get_identification())

    def save_data(self, base_path):
        _path = os.path.join(base_path, 'image')
        pathlib.Path(_path).mkdir(exist_ok=True, parents=True)
        for sprite in self.sprites:
            obj = sprite.obj
            save_name = sprite.name + '.png' if not sprite.name.endswith('.png') else sprite.name
            obj.image.save(os.path.join(_path, save_name))

        _path = os.path.join(base_path, 'image')
        os.makedirs(_path, exist_ok=True)
        for tex in self.textures:
            path = os.path.join(_path, f"{tex.name}.png")
            tex.obj.image.save(path)

        _path = os.path.join(base_path, 'rawShader')
        os.makedirs(_path, exist_ok=True)
        for k, v in self.hlsls.items():
            _shader_path = k
            if '/' in k:
                _shader_path = k[:k.rindex('/')]
            _shader_path = os.path.join(_path, _shader_path)
            os.makedirs(_shader_path, exist_ok=True)
            with open(os.path.join(_path, k + '.shader'), 'w+', encoding='utf-8') as f:
                f.write(v)
        _path = os.path.join(base_path, 'shader')
        os.makedirs(_path, exist_ok=True)
        for k, v in self.glsls.items():
            _shader_path = k
            if '/' in k:
                _shader_path = k[:k.rindex('/')]
            _shader_path = os.path.join(_path, _shader_path)
            os.makedirs(_shader_path, exist_ok=True)
            with open(os.path.join(_path, k + '.vert'), 'w+', encoding='utf-8') as f:
                f.write(v[1])
            with open(os.path.join(_path, k + '.frag'), 'w+', encoding='utf-8') as f:
                f.write(v[2])
        super().save_data(base_path)

    def clear(self):
        super().clear()
        self.sprites.clear()
        self.hlsls.clear()
        self.glsls.clear()
        self.textures.clear()
