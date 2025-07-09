import os
import pathlib

import util
from recorder.containerObjects.AmbientEvent import AmbientEvent
from recorder.containerObjects.GameObject import GameObject
from recorder.containerObjects.InteractiveConfig import InteractiveConfig
from recorder.containerObjects.Particle import Particle
from recorder.containerObjects.PostProcessing import PostProcessing
from recorder.containerObjects.SpineClips import SpineClips
from recorder.containerObjects.SpriteRender import SpriteRender
from recorder.containerObjects.Timeline import Timeline

"""
emm,这个类并不是Recorder的子类，只是为了方便，和那些放在一起。故命名小写，以区分
"""

class Container:
    def __init__(self, student_name, info_json_manager: util.InfoJsonManger, nodes_dict):
        self.name = student_name
        self.container_objects = (
            GameObject(self), SpineClips(self), InteractiveConfig(self),
            PostProcessing(self), SpriteRender(self),
            Particle(self), Timeline(self), AmbientEvent(self))
        self.info_json_manager: util.InfoJsonManger = info_json_manager
        self.nodes_dict = nodes_dict

    def add_node(self, node):  # test_and_add
        for i in self.container_objects:
            i.test_and_add(node)
            # if i.test_and_add(node):
            #     return

    def notify_single(self, stu, saving=True):  # process
        if saving:
            for i in self.container_objects:
                i.process()

            for i in self.container_objects:
                i.save_data(os.path.join('container', stu))

    #  只是为了和Recorder保持一致。下同
    def notify_bundle(self, bundle, saving=True):
        return

    def notify_total(self, saving=True):
        return

    # def process(self):
    #     for i in self.container_objects:
    #         i.process()
