import util
from recorder.Recorder import Recorder
from typeId import ClassIDType, inverse_map
import inspect


class HashInfoRecorder(Recorder):
    """
    只记录属性的hash,GameObject的运行时动态记录.整个过程保存一次
    """

    def notify_single(self, node):
        if (target := self.batch_data.get(inverse_map[str(node.type)])) is None:
            target = {}
            self.batch_data[inverse_map[str(node.type)]] = target

        if len(target) == 0 or node.type == ClassIDType.MonoBehaviour:
            for name, value in node.obj.object_reader.read_typetree().items():
                if value.get('r') is not None and HashInfoRecorder._add_obj(target, name + '.r'):
                    HashInfoRecorder._add_obj(target, name + '.g')
                    HashInfoRecorder._add_obj(target, name + '.b')
                    HashInfoRecorder._add_obj(target, name + '.a')
                elif value.get('x') is not None and HashInfoRecorder._add_obj(target, name + '.x'):
                    HashInfoRecorder._add_obj(target, name + '.y')
                    HashInfoRecorder._add_obj(target, name + '.z')
                    HashInfoRecorder._add_obj(target, name + '.w')
                else:
                    HashInfoRecorder._add_obj(target, name)

    @staticmethod
    def _add_obj(target_dict, value):
        if value not in target_dict.values():
            target_dict[util.compute_unity_hash(value)] = value
            return True
        return False

    def notify_total(self):
        self._save_data('hash')
