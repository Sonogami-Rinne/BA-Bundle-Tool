import os

import util
from containerObjects.ContainerObject import ContainerObject
from typeId import ClassIDType
from unityDefaultResource import get_unity_default_resource


class MeshRender(ContainerObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.meshes = {}
        self.glsls = {}
        self.hlsls = {}
        self.textures = []

    def test_and_add(self, node):
        if node.type == ClassIDType.MeshRenderer:
            self.nodes[node.get_identification()] = node

    def process(self):
        game_object_container = self.parent.container_objects['GameObject']
        spine_clip_container = self.parent.container_objects['SpineClips']
        for node in self.nodes.values():
            game_object = node.children['m_GameObject']
            game_object_container.register_game_object(game_object)
            mesh_filter = None
            for _child in game_object.children.values():
                if _child.type == ClassIDType.MeshFilter:
                    mesh_filter = _child
                    break
            if mesh_filter is None:
                continue
            mesh = mesh_filter.children.get('m_Mesh', None)
            if mesh is None:
                mesh = get_unity_default_resource(mesh_filter.obj.m_Mesh.m_PathID)
                if mesh is None:
                    continue
                mesh = mesh.read()
            else:
                if mesh.name.startswith('Skeleton Prefab Mesh'):
                    continue
                mesh = mesh.obj
            self.meshes[mesh.m_Name] = mesh

            parent_transform = game_object.transform
            while parent_transform is not None and not spine_clip_container.is_bone(
                    parent_transform.game_object.name):
                parent_transform = parent_transform.children.get('m_Father', None)

            if parent_transform is not None:
                game_object_container.register_game_object(parent_transform.game_object, need_middle_node=False)

            material_infos = []
            material_names = []
            material_tex_infos = []
            renderer_materials = [
                child for name, child in node.children.items()
                if name.startswith('m_Materials-')
            ]
            for renderer_material_node in renderer_materials:
                material_info, material_tex_info, hlsl_info, glsl_info, material_tex_node = self.process_material(renderer_material_node)
                if len(material_info) == 0:
                    continue

                self.textures.extend(material_tex_node)
                material_names.append(renderer_material_node.name)
                material_infos.append(material_info)
                material_tex_infos.append(material_tex_info)

                #
                # material_infos.append(material_info)
                # # material_main_texs.extend(material_main_tex)
                # material_tex_infos.append(material_tex_info)
                # self.textures.extend(material_node)
                # self.hlsls[hlsl_info[0]] = hlsl_info[1]
                if hlsl_info[1] is not None:
                    self.hlsls[hlsl_info[0]] = hlsl_info[1]
                if glsl_info[1] is not None:
                    self.glsls[glsl_info[0]] = glsl_info
            render_queue = material_infos[0].get('renderQueue') if material_infos else None
            position, rotation, scale = util.decompose_2d_transform(util.get_transform(game_object))
            transform_obj = game_object.transform.obj
            self.data.append({
                'mesh': mesh.m_Name,
                'renderQueue': render_queue,
                'sortingOrder': node.obj.m_SortingOrder,
                'sortingLayer': node.obj.m_SortingLayer,
                'materialNames': material_names,
                'materialInfo': material_infos,
                'texInfo': material_tex_infos,
                'gameObject': game_object_container.get_index(game_object.get_identification()),
                'position': position,
                'rotation': rotation,
                'scale': scale,
                'localPosition': util.to_tuple(transform_obj.m_LocalPosition),
                'localRotation': util.to_tuple(transform_obj.m_LocalRotation),
                'localScale': util.to_tuple(transform_obj.m_LocalScale)
            })
    def clear(self):
        super().clear()
        self.meshes.clear()
        self.hlsls.clear()
        self.glsls.clear()
        self.textures.clear()

    def save_data(self, base_path):
        _path = os.path.join(base_path, 'mesh')
        os.makedirs(_path, exist_ok=True)
        for mesh_name, mesh in self.meshes.items():
            with open(os.path.join(_path, mesh_name + '.obj'), 'wt', newline='') as f:
                f.write(mesh.export())

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


