__author__ = 'scmijt'

import json
import subprocess
import time

infile = open('hamlet_stanzas.json', 'r')
play = json.load(infile)


def get_act_number(act_string):
    act_string = act_string[4:]
    parts = act_string.split(".")
    return str(parts[0])

def get_scene_number(scene_string):
    act_string = scene_string[6:]
    parts = act_string.split(".")
    return str(parts[0])

scenes = {}

for act_name, act in sorted(play.iteritems()):
    this_act = get_act_number(act_name)
    for scene_name, scene in sorted(act.iteritems()):
        this_scene = get_scene_number(scene_name)
        command = "python workflow.py -a " + this_act + " -s " + this_scene
        print "Running " + command
        subprocess.call(command.split(" "))
