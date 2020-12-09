__author__ = 'scmijt'

import methods

from newt.Workflow import Endpoint
from newt.wire.Transport import Transport
from newt.Workflow import Workflow, Node, Port
import logging
from optparse import OptionParser
import time
import os



directory = os.path.dirname(os.path.realpath(__file__))

parser = OptionParser()
parser.add_option("-m", "--mode", dest="mode", default="localhost",
                  help="Mode [default: %default], Options [localhost, core]",
                  metavar="MODE")
parser.add_option("-a", "--act", dest="act", default="I",
                  help="Act [default: %default], Options [I, II, II, IV, V]",
                  metavar="ACT")
parser.add_option("-s", "--scene", dest="scene", default="I",
                  help="scene [default: %default], Options [I, II, II, IV, V, VI, VII]",
                  metavar="SCENE")

(options, args) = parser.parse_args()

act_to_conduct = options.act
scene_to_conduct = options.scene
methods.act_to_conduct = options.act
methods.scene_to_conduct = options.scene

DEBUG = False
logging.basicConfig(level=logging.INFO)
Workflow.include_args=False  # this turns off the inclusion of arguments in JSON serialisation.

import json
import newt.wire.net.Network as net
import shutil

log_dir = "/tmp/hamlet_logs/"

if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# logs
methods.rcv_logs = open(log_dir + "rcv_" + act_to_conduct + '_' + scene_to_conduct + '.csv', 'w')
methods.snd_logs = open(log_dir + "snd_" + act_to_conduct + '_' + scene_to_conduct + '.csv', 'w')

methods.rcv_logs.write("time, host_address, actor, from_actor, bytes, dialogue_id" + "\n")
methods.snd_logs.write("time, from_actor, to_actor, from_address, from_port, to_address, to_port, bytes, dialogue_id"+ "\n")

# actors
infile = open(directory + '/hamlet_actors.json', 'r')
actors = json.load(infile)

core_subnet = "10.0.0."
node_num=1

actor_core_mapping = {}

actors.sort()
for actor in actors:
    if not "-" in actor:
        actor_core_mapping[actor] = { "node" : "n" + str(node_num), "address" : core_subnet + str(node_num)}
        node_num+=1

Workflow.SIGMA_SERIALIZATION=True
with open(directory + '/data/core_actor_mapping.json', 'w') as outfile:
    outfile.write(json.dumps(actor_core_mapping, indent=4))

infile = open(directory + '/hamlet_stanzas.json', 'r')
play = json.load(infile)
methods.play = play


def get_actors_from_multiple(actor):
    return actor.split("-")


def get_actors(scene_to_process):
    keys = scene_to_process.keys()
    keys.sort(key=int)
    first_actor = None
    last_actor = None
    actors = []
    for stanza_scene_id in keys:
        stanza = scene_to_process[stanza_scene_id]
        actor = stanza['actor']
        if "-" in actor:
            multicast_actors = get_actors_from_multiple(actor)
            for multicast_actor in multicast_actors:
                #print "Scene ID " + stanza_scene_id + ", actor = " + multicast_actor
                if first_actor is None:
                    first_actor = multicast_actor
                if multicast_actor not in actors:
                    actors.append(multicast_actor)
                last_actor=multicast_actor
        else:
            #print "Scene ID " + stanza_scene_id + ", actor = " + actor
            if first_actor is None:
                first_actor = actor
            if actor not in actors:
                actors.append(actor)
            last_actor=actor
    return actors, first_actor, last_actor

thespian_workflow = Workflow("Hamlet")

process_act_name = None
process_scene_name = None
process_scene = None

def to_numeric(roman):
    if roman == "I":
        return 1
    elif roman == "II":
        return 2
    elif roman == "III":
        return 3
    elif roman == "IV":
        return 4
    elif roman == "V":
        return 5
    elif roman == "VI":
        return 6
    elif roman == "VII":
        return 7

def get_act_number(act_string):
    act_string = act_string[4:]
    parts = act_string.split(".")
    return str(parts[0])

def get_scene_number(scene_string):
    act_string = scene_string[6:]
    parts = act_string.split(".")
    return str(parts[0])

scenes = {}

if DEBUG:
    print "Processing Act/Scene = " + act_to_conduct  + "/" + scene_to_conduct

for act_name, act in sorted(play.iteritems()):
    this_act = get_act_number(act_name)
    if DEBUG:
        print(this_act)
    for scene_name, scene in sorted(act.iteritems()):
        this_scene = get_scene_number(scene_name)
        #print("Act compare " + str(act_to_conduct) +" and " + str(this_act))
        #print("Scene compare " + scene_to_conduct +" and " + str(this_scene))
        if this_act == act_to_conduct and this_scene == scene_to_conduct:
           # print(" Found act/scene" + act_to_conduct  + "/" + scene_to_conduct)
            process_scene_name = scene_name
            process_scene =scene
            process_act_name=act_name
        if DEBUG:
            print(" --> " + this_scene)

#

if DEBUG:
    print "Located Act/Scene: " + process_act_name + process_scene_name + " creating workflow "

actors, first_actor, last_actor = get_actors(process_scene)

#print "Scene = " + str(process_scene)

if DEBUG:
    print "First Actor = " + first_actor
    print "Last Actor = " + last_actor
    print "Number of actors = " + str(len(actors))
    print "Actors = " + str(actors)
    print str(actors)

for actor in actors:
    node = Node(actor)

    if actor == first_actor: # first actor in scene is initiator
        node.initiator = True

    thespian_workflow.add_node(node)

# add edges based on stanzas = edges in workflow.

port_number=6000

connection_list = {} # object of list of connections

keys = process_scene.keys()
keys.sort(key=int)

#transport_prototol=Transport.ZMQ_TCP
transport_prototol=Transport.UDP
#transport_prototol=Transport.MGEN

for stanza_scene_id in keys:
    stanza = process_scene[stanza_scene_id]
    previous_actor = stanza['previous_actor']
    actor = stanza['actor']
    next_actor = stanza['next_actor']

    dialogue_id = int(stanza['dialogue_id'])
    line = stanza['line']

    if next_actor is not None:
        next_actors = None
        actors = None
        if "-" in actor:  # Many to one
            actors = actor.split("-")
        elif "-" in next_actor:  # Many to one
            next_actors = next_actor.split("-")

        if actors is None:
            actors = [actor]
        if next_actors is None:
            next_actors = [next_actor]

        for actor in actors:
            for next_actor in next_actors:
                if actor in connection_list:
                    actor_connection_list = connection_list[actor]
                else:
                    actor_connection_list = []

                if next_actor not in actor_connection_list: # create a connection
                    actor_connection_list.append(next_actor)
                    connection_list[actor] = actor_connection_list

                    actor_node = thespian_workflow.get_node(actor)
                    next_actor_node = thespian_workflow.get_node(next_actor)

                    in_address = "localhost"
                    out_address = "localhost"

                    if options.mode == "core":
                        in_address = actor_core_mapping[actor_node.unique_name]['address']
                        out_address = actor_core_mapping[actor_node.unique_name]['address']

                    if actor_node.initiator:
                        #print "I AM AN INITIATOR !!!"
                        actor_node.set_initiator_method_and_args(methods.def_actor, dialogue_id=dialogue_id, line=line)

                    output_port = actor_node.add_output_port(line="@DATA[line]", dialogue_id="@DATA[dialogue_id]", endpoint=Endpoint(out_address, port_number))
                    port_number += 1

                    if options.mode == "core":
                        in_address = actor_core_mapping[next_actor_node.unique_name]['address']

                    input_port = next_actor_node.add_input_port(methods.def_actor, endpoint=Endpoint(in_address, port_number))
                    port_number += 1

                    edge = thespian_workflow.add_edge(transport_prototol, Transport.PICKLE, output_port, input_port)

#print " MAX PORT = " + str(port_number)

Workflow.SIGMA_SERIALIZATION=True
with open(directory + '/data/hamlet_sigma.json', 'w') as outfile:
    outfile.write(thespian_workflow.serialize(True))

Workflow.SIGMA_SERIALIZATION=False
with open(directory + '/data/hamlet_workflow' + act_to_conduct + '_' + scene_to_conduct + '.json', 'w') as outfile:
    outfile.write(thespian_workflow.serialize(True))

if options.mode == "core":
    thespian_workflow.enact()
    time.sleep(30)
    thespian_workflow.clean_up()
else:
    if DEBUG:
        print("Workflow running Act/Scene: " + process_act_name + process_scene_name + " creating workflow ")

    thespian_workflow.enact()
    time.sleep(30)

    if DEBUG:
        print("Workflow Cleaning up...")

    thespian_workflow.clean_up()

    if DEBUG:
        print("Workflow Finished ... ")


