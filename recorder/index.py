import util
from recorder.ExternalsRecorder import ExternalsRecorder
from recorder.HashInfoRecorder import HashInfoRecorder
from recorder.TrackInfoRecorder import TrackInfoRecorder
from recorder.TrackVisualizationRecorder import TrackVisualizationRecorder


class Recorder:
    def __init__(self):
        self.container_objects = []
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
        for i in self.container_objects:
            i.notify_bulk(stu)

    def notify_bundle(self, bundle):
        for i in self.container_objects:
            i.notify_bundle(bundle)

    def notify_total(self):
        for i in self.container_objects:
            i.notify_total()

    # def process(self):
    #     for i in self.container_objects:
    #         i.process()
