import os.path

from containerObjects.ContainerObject import ContainerObject


class ResourceJS(ContainerObject):

    def test_and_add(self, node):
        return False

    def save_data(self, base_path):
        with open(os.path.join(base_path, 'resource.js'), 'w+', encoding='utf-8') as f:
            f.write('const resourceLoader = {\n')
            for file in os.listdir(base_path):
                if file.endswith('.skel'):
                    f.write(f'"{file}": () => import("@skel/{file}?binary"),\n')
                elif file.endswith('.atlas'):
                    f.write(f'"{file}": () => import("@atlas/{file}?raw"),\n')
            for file in os.listdir(os.path.join(base_path, 'image')):
                f.write(f'"{file}": () => import("@image/{file}?binary"),\n')

            f.write('}\nexport default resourceLoader;')

        # with open(os.path.join(base_path, 'resource.js'), 'w+', encoding='utf-8') as f:
        #     f.write('const resourceLoader = {\n')
        #     for i in self.data['skel']:
        #         f.write(f'"{i}": () => import("@skel/{i}?binary"),\n')
        #     for i in self.data['atlas']:
        #         f.write(f'"{i}": () => import("@atlas/{i}?raw"),\n')
        #     for i in self.data['image']:
        #         f.write(f'"{i}": () => import("@image/{i}?binary"),\n')
        # self.clear()
