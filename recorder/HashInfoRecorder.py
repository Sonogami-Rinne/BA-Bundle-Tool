import util
from recorder.Recorder import Recorder
from util import IGNORED_ATTR, compute_unity_hash
import inspect


class HashInfoRecorder(Recorder):
    """
    只记录属性的hash,GameObject的运行时动态记录.整个过程保存一次
    """

    def notify_single(self, node):
        if (target := self.batch_data.get(node.type)) is None:
            target = {}
            self.batch_data[node.type] = target

        if len(target) == 0 or node.type == 'MonoBehaviour':
            obj = node.obj
            for attr_name in dir(obj):
                if attr_name.startswith('_') or attr_name in util.IGNORED_ATTR:
                    continue
                if inspect.isroutine((attr_value := getattr(obj, attr_name))):
                    continue
                #  对于这几个特殊的，是直接修改其内的值的
                if type(attr_value).__name__ == 'ColorRGBA':
                    if HashInfoRecorder._add_obj(target, attr_name + '.r'):
                        HashInfoRecorder._add_obj(target, attr_name + '.g')
                        HashInfoRecorder._add_obj(target, attr_name + '.b')
                        HashInfoRecorder._add_obj(target, attr_name + '.a')
                elif type(attr_value).__name__.startswith('Vector'):
                    if HashInfoRecorder._add_obj(target, attr_name + '.x'):
                        HashInfoRecorder._add_obj(target, attr_name + '.y')
                        HashInfoRecorder._add_obj(target, attr_name + '.z')  # 虽然如果是vector2的话没有这个z，但也无妨
                elif type(attr_value).__name__ == 'Quaternion':
                    if HashInfoRecorder._add_obj(target, attr_name + '.x'):
                        HashInfoRecorder._add_obj(target, attr_name + '.y')
                        HashInfoRecorder._add_obj(target, attr_name + '.z')
                        HashInfoRecorder._add_obj(target, attr_name + '.w')
                else:  # 其实应该只加入类型为基本数据类型和PPtr的。但也没事
                    HashInfoRecorder._add_obj(target, attr_name)

    @staticmethod
    def _add_obj(target_dict, value):
        if value not in target_dict.values():
            target_dict[util.compute_unity_hash(value)] = value
            return True
        return False

    def notify_total(self):
        self._save_data('hash')

