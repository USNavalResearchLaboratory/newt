__author__ = 'scmijt'

import methods

from newt.Workflow import Endpoint
from newt.wire.Transport import Transport
from newt.Workflow import Workflow, Node
import logging
from optparse import OptionParser
from itertools import cycle

parser = OptionParser()
parser.add_option("-m", "--mode", dest="mode", default="localhost",
                  help="Mode [default: %default], Options [localhost, core]",
                  metavar="MODE")
(options, args) = parser.parse_args()

logging.basicConfig(level=logging.INFO)

import json

infile = open('hamlet_stanzas.json', 'r')
play = json.load(infile)

print "The outline is:"

def get_actors(scene):
    first_actor=None
    last_actor=None
    actors = []
    for stanza_scene_id, stanza in scene.iteritems():
        actor = stanza['actor']
        if first_actor is None:
            first_actor = actor
        if actor not in actors:
            actors.append(actor)
        last_actor=actor
    return actors, first_actor, last_actor

thespian_workflow = Workflow("Hamlet")
thespian_workflow.single_port_initiator=True

process_scene = None

for act_name, act in sorted(play.iteritems()):
    print(act_name)
    for scene_name, scene in sorted(act.iteritems()):
        print(scene_name)
        process_scene = scene

actors, first_actor, last_actor = get_actors(process_scene)

print "Scene = " + scene_name
print "First Actor = " + first_actor
print "Last Actor = " + last_actor
print "Number of actors = " + str(len(actors))
print "Actors = " + str(actors)

# add nodes, sorry actors...

core_subnet = "10.0.0."
node_num=1

print str(actors)

for actor in actors:
    if options.mode == "core":
        address = core_subnet + str(node_num)
    else:
        address = "localhost"

    node = Node(actor)

    if actor == first_actor: # first actor in scene is initiator
        node.initiator = True

    thespian_workflow.add_node(node)

# add edges based on stanzas = edges in workflow.

port_number=5348

for stanza_scene_id, stanza in process_scene.iteritems():
    previous_actor = stanza['previous_actor']
    actor = stanza['actor']
    next_actor = stanza['next_actor']
    speech_bytes = int(stanza['speech_size'])
    byte_array = bytearray()

    for i in range(speech_bytes):
        byte_array.append(0)

    actor_node = thespian_workflow.get_node(actor)
    next_actor_node = thespian_workflow.get_node(next_actor)

    if next_actor is not None:
        input_port = next_actor_node.add_input_port(methods.def_actor_multiple_ports, endpoint=Endpoint(address, port_number))
        port_number += 1
        output_port = actor_node.add_output_port(speech_bytes=speech_bytes, actor=actor, endpoint=Endpoint(address, port_number))
        port_number += 1
        thespian_workflow.add_edge(Transport.UDP, Transport.PICKLE, output_port, input_port)


Workflow.SIGMA_SERIALIZATION=True
with open('data/hamlet_sigma.json', 'w') as outfile:
    outfile.write(thespian_workflow.serialize(True))

Workflow.SIGMA_SERIALIZATION=False
with open('data/hamlet_workflow.json', 'w') as outfile:
    outfile.write(thespian_workflow.serialize(True))


if options.mode == "core":
    thespian_workflow.enact()
    import time
    time.sleep(1000)
else:
    try:
        print("Workflow running...")
        thespian_workflow.enact()
        raw_input('Hit any key to exit the program ...\n')
    except KeyboardInterrupt:
        pass

    thespian_workflow.clean_up()

    print("Workflow Finished ... ")


