__author__ = 'scmijt'

import json
import shutil
import os

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

pcap_all_dir="/tmp/hamlet/pcap/"

if os.path.exists(pcap_all_dir):
    shutil.rmtree(pcap_all_dir)

os.makedirs(pcap_all_dir)

for node_number in range(1,35):
    pcap_node_file_name = "n" + str(node_number) + ".eth0.pcap"
    pcap_all_node_file = open(pcap_all_dir + pcap_node_file_name, "w")

    for act_name, act in sorted(play.iteritems()):
        this_act = get_act_number(act_name)
        for scene_name, scene in sorted(act.iteritems()):
            this_scene = get_scene_number(scene_name)
            scene_dir="/tmp/hamlet/" + this_act + "-" + this_scene + "/"
            pcap_node_file = open(scene_dir + pcap_node_file_name, "r")

            pcap_all_node_file.write(pcap_node_file.read())

