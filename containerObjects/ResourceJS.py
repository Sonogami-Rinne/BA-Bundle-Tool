import os.path
import pathlib

from containerObjects.ContainerObject import ContainerObject


class ResourceJS(ContainerObject):

    def test_and_add(self, node):
        return False

    def save_data(self, base_path):
        with open(os.path.join(base_path, 'resource.js'), 'w+', encoding='utf-8') as f:
            f.write('const resourceLoader = {\n')
            for file in os.listdir(base_path):
                if file.endswith('.skel'):
                    f.write(f'"{file}": () => import("@assets/{file}?binary"),\n')
                elif file.endswith('.atlas'):
                    f.write(f'"{file}": () => import("@assets/{file}?raw"),\n')
            for file in os.listdir(os.path.join(base_path, 'image')):
                f.write(f'"{file}": () => import("@image/{file}?binary"),\n')
            for folder in os.listdir(os.path.join(base_path, 'shader')):
                folder_path = os.path.join(base_path, 'shader', folder)
                for file in pathlib.Path(folder_path).rglob('*.vert'):
                    file_name = '/'.join(file.parts[5:])
                    file_name = file_name[:file_name.rindex('.')]
                    f.write(f'"{folder}/{file_name}.vert": () => import("@shader/{folder}/{file_name}.vert?raw"),\n')
                    f.write(f'"{folder}/{file_name}.frag": () => import("@shader/{folder}/{file_name}.frag?raw"),\n')

            f.write('}\nexport default resourceLoader;')
