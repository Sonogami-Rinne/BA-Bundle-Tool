import os
import pathlib

import util
from containerObjects.ContainerObject import ContainerObject
from typeId import ClassIDType
from util import to_tuple


class SpriteRender(ContainerObject):

    def __init__(self, parent):
        super().__init__(parent)
        self.sprites = []
        self.textures = []
        self.hlsls = {}
        self.glsls = {}

    def test_and_add(self, node):
        if node.type == ClassIDType.SpriteRenderer:
            self.nodes[node.get_identification()] = node
            return True
        return False

    @classmethod
    def sprite_info(cls, sprite):
        """Export Unity coordinates in pixels; PNGs are already cropped/unpacked.

        rect/textureRect: (x, y, width, height), border: (left, bottom, right, top).
        renderData describes the source texture, not the exported PNG.
        """
        render_data = sprite.m_RD
        atlas = None
        if sprite.m_SpriteAtlas:
            atlas = sprite.m_SpriteAtlas.read()
        elif sprite.m_AtlasTags:
            # Match UnityPy's image exporter when only an atlas tag is available.
            for reader in sprite.assets_file.objects.values():
                if reader.type == ClassIDType.SpriteAtlas:
                    candidate = reader.read()
                    if candidate.m_Name == sprite.m_AtlasTags[0]:
                        atlas = candidate
                        break
        if atlas is not None:
            render_data = next(value for key, value in atlas.m_RenderDataMap
                               if key == sprite.m_RenderDataKey)

        settings = render_data.settingsRaw
        return {
            'rect': (sprite.m_Rect.x, sprite.m_Rect.y, sprite.m_Rect.width, sprite.m_Rect.height),
            'offset': (sprite.m_Offset.x, sprite.m_Offset.y),
            'pivot': (sprite.m_Pivot.x, sprite.m_Pivot.y),
            'border': util.to_tuple(sprite.m_Border),
            'pixelsToUnits': sprite.m_PixelsToUnits,
            'extrude': sprite.m_Extrude,
            'isPolygon': sprite.m_IsPolygon,
            'renderData': {
                'textureRect': (render_data.textureRect.x, render_data.textureRect.y, render_data.textureRect.width, render_data.textureRect.height),
                'textureRectOffset': (render_data.textureRectOffset.x, render_data.textureRectOffset.y),
                'atlasRectOffset': (render_data.atlasRectOffset.x, render_data.atlasRectOffset.y),
                'uvTransform': util.to_tuple(render_data.uvTransform),
                'downscaleMultiplier': render_data.downscaleMultiplier,
                'settingsRaw': settings,
                'packed': bool(settings & 1),
                'packingMode': (settings >> 1) & 1,
                'packingRotation': (settings >> 2) & 0xf,
                'meshType': (settings >> 6) & 1,
            },
        }

    def process(self):
        game_object_container = self.parent.container_objects['GameObject']
        spine_clip_container = self.parent.container_objects['SpineClips']
        for _, node in self.nodes.items():
            obj = node.obj

            sprite_node = node.children.get('m_Sprite')
            # Empty SpriteRenderers have no image to export.
            if sprite_node is None:
                continue
            game_object = node.children['m_GameObject']
            game_object_container.register_game_object(game_object)
            position, rotation, scale = util.decompose_2d_transform(util.get_transform(game_object))
            transform_obj = game_object.transform.obj
            sprite = sprite_node.obj
            item = {
                'sprite': sprite_node.name,
                'color': to_tuple(obj.m_Color),
                'flip': (obj.m_FlipX, obj.m_FlipY),
                # 'material': obj.m_Materials,
                # 'materials': [
                #     material for material in obj.m_Materials
                # ],
                'drawMode': obj.m_DrawMode,
                'sortingLayer': obj.m_SortingLayer,
                'sortingOrder': obj.m_SortingOrder,
                'maskInteraction': obj.m_MaskInteraction,
                'gameObject': game_object_container.get_index(game_object.get_identification()),
                'gameObjectName': game_object.name,
                'position': position,
                'rotation': rotation,
                'scale': scale,
                'localPosition': util.to_tuple(transform_obj.m_LocalPosition),
                'localRotation': util.to_tuple(transform_obj.m_LocalRotation),
                'localScale': util.to_tuple(transform_obj.m_LocalScale),
                'spriteSize': (obj.m_Size.x, obj.m_Size.y),
                **self.sprite_info(sprite),
            }
            parent_transform = game_object.transform
            while parent_transform is not None and not spine_clip_container.is_bone(
                    parent_transform.game_object.name):
                parent_transform = parent_transform.children.get('m_Father', None)

            if parent_transform is not None:
                game_object_container.register_game_object(parent_transform.game_object, need_middle_node=False)

            # material_main_texs = []
            material_infos = []
            material_tex_infos = []
            renderer_materials = [
                child for name, child in node.children.items()
                if name.startswith('m_Materials-')
            ]
            for material in renderer_materials:
                material_info, material_tex_info, hlsl_info, glsl_info, material_node = self.process_material(material)
                if len(material_info) == 0:
                    continue
                material_infos.append(material_info)
                # material_main_texs.extend(material_main_tex)
                material_tex_infos.append(material_tex_info)
                self.textures.extend(material_node)
                # self.hlsls[hlsl_info[0]] = hlsl_info[1]
                if hlsl_info is not None and hlsl_info[1] is not None:
                    self.hlsls[hlsl_info[0]] = hlsl_info[1]
                if glsl_info is not None and glsl_info[1] is not None:
                    self.glsls[glsl_info[0]] = glsl_info

            # item['textures'] = texture_nodes
            item['materialInfo'] = material_infos
            # item['materialsMainTex'] = material_main_texs
            item['texInfo'] = material_tex_infos

            self.data.append(item)
            self.sprites.append(sprite_node)
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
