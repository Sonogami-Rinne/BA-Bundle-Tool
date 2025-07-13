import util
from BaseInfoRecorder import BaseInfoRecorder
from ExternalsRecorder import ExternalsRecorder
from HashInfoRecorder import HashInfoRecorder
from TrackInfoRecorder import TrackInfoRecorder
from TrackVisualizationRecorder import TrackVisualizationRecorder


class Recorder:
    def __init__(self, student_name):
        self.name = student_name
        self.container_objects = []
        if util.RECORDER_BASE_INFO:
            self.container_objects.append(BaseInfoRecorder)
        if util.RECORDER_EXTERNAL:
            self.container_objects.append(ExternalsRecorder())
        if util.RECORDER_HASH_INFO:
            self.container_objects.append(HashInfoRecorder())
        if util.RECORDER_TRACK_INFO:
            self.container_objects.append(TrackInfoRecorder())
        if util.RECORDER_TRACK_VISUALIZATION:
            self.container_objects.append(TrackVisualizationRecorder())

    def notify_single(self, node):  # process
        for i in self.container_objects:
            i.notify_single(node)

    def notify_bulk(self, stu):
        pass

    def notify_bundle(self, bundle):
        return

    def notify_total(self):
        return

    # def process(self):
    #     for i in self.container_objects:
    #         i.process()
