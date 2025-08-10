import os
import pathlib

import infoJsonManager
import util
from containerObjects.AmbientAudio import AmbientEvent
from containerObjects.GameObject import GameObject
from containerObjects.InteractiveConfig import InteractiveConfig
from containerObjects.Particle import Particle
from containerObjects.PostProcessing import PostProcessing
from containerObjects.SpineClips import SpineClips
from containerObjects.SpriteRenderer import SpriteRender
from containerObjects.Timeline import Timeline
from containerObjects.ResourceJS import ResourceJS


class Container:
    def __init__(self, info_json_manager: infoJsonManager.InfoJsonManger, nodes_dict):
        self.container_objects = {
            'GameObject': GameObject(self),
            'SpineClips': SpineClips(self),
            'InteractiveConfig': InteractiveConfig(self),
            'PostProcessing': PostProcessing(self),
            'SpriteRender': SpriteRender(self),
            'Particle': Particle(self),
            'Timeline': Timeline(self),
            'AmbientEvent': AmbientEvent(self),
            'ResourceJS': ResourceJS(self),
        } if util.CONTAINER_RECORD else {}
        self.info_json_manager: infoJsonManager.InfoJsonManger = info_json_manager
        self.nodes_dict = nodes_dict

    def notify_single(self, node):  # process
        for i in self.container_objects.values():
            i.test_and_add(node)

    def notify_bulk(self, stu):
        for i in self.container_objects.values():
            i.process()

        for i in self.container_objects.values():
            i.save_data(pathlib.Path(os.path.join('save','container', stu)))

    #  只是为了和Recorder保持一致。下同
    def notify_bundle(self, bundle):
        return

    def notify_total(self):
        return

