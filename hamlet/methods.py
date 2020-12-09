__author__ = 'scmijt'

import random
import time

info_detail=True
play = None
act_to_conduct = None
scene_to_conduct = None
rcv_logs = None
snd_logs = None

METHOD_DEBUG = True


def def_actor(node, line, dialogue_id):
    sent_stanza = find_stanza_by_dialogue_id(dialogue_id)

    if is_first_stanza_in_scene(dialogue_id) and node.unique_name == sent_stanza['actor']:
        my_stanza = find_stanza_by_dialogue_id(dialogue_id)
    else: # pick the next stanza
        my_stanza = find_stanza_by_dialogue_id(int(dialogue_id)+1)
        print node.get_host() + ": " + node.unique_name + " received " + str(len(line)) + " bytes from actor " + sent_stanza['actor'] + " dialogue id: " + str(dialogue_id)
        current_time = int(time.time() * 1000)
        rcv_logs.write(str(current_time) + "," + node.get_host() + "," + node.unique_name + "," + sent_stanza['actor'] + "," + str(len(line)) + "," + str(dialogue_id) + "\n")

    if my_stanza is None:
        print "The stanza ID of " + str(dialogue_id) + " could not be found!!"

    ports = node.get_output_ports()

    for port in ports:
        port.enabled = False

    if my_stanza is None or my_stanza['next_actor'] is None:
        print node.get_host() + ": " + "Workflow finished running Act/Scene: " + str(act_to_conduct) + "/"+ str(scene_to_conduct)
        #print "The number of messages on node " + node.get_host() + " is " + str(def_actor.message_count)

        return

    if node.unique_name not in def_actor.previous_dialog_id or def_actor.previous_dialog_id[node.unique_name] != my_stanza['dialogue_id']: # make sure you do not send duplicates
        for port in ports:
            next_actor = my_stanza['next_actor']
            output_edge = node.workflow.get_edge_for_port(port.port_id)
            current_time = int(time.time() * 1000)

            if "-" in next_actor:
                multiple_actors = get_actors_from_multiple(next_actor)
                for multiple_actor in multiple_actors:
                    if output_edge.in_node is not None:
                        if output_edge.in_node.unique_name == multiple_actor:
                            port.enabled = True
                            bind_address = None
                            snd_logs.write(str(current_time) + "," + node.unique_name + "," + multiple_actor + "," + get_port_as_string(port)
                                            + "," + str(my_stanza['speech_size']) + "," + str(my_stanza['dialogue_id']) + "\n")

                            def_actor.message_count+=1
                            if METHOD_DEBUG:
                                print "Multiple: " + node.unique_name + " is sending dialog id " + str(my_stanza['dialogue_id']) + " from " + get_port_as_string(port) + "(" + multiple_actor + ")"
            else:
                    if output_edge.in_node is not None:
                        if output_edge.in_node.unique_name == next_actor:
                            port.enabled = True
                            if METHOD_DEBUG:
                                print node.unique_name + " is sending dialog id " + str(my_stanza['dialogue_id']) + " from " + get_port_as_string(port) + "(" + next_actor + ")"
                            def_actor.message_count+=1
                            snd_logs.write(str(current_time) + "," + node.unique_name + "," + next_actor + "," + get_port_as_string(port)
                                            + "," + str(my_stanza['speech_size']) + "," + str(my_stanza['dialogue_id']) + "\n")

    def_actor.previous_dialog_id[node.unique_name] = my_stanza['dialogue_id']


   # for port in ports:
    #    print "Port " + str(port.port_id) + " is set to " + str(port.enabled)

    time.sleep(0.1)
    return {"line": my_stanza['line'], "dialogue_id": my_stanza['dialogue_id']}

def_actor.previous_dialog_id = dict()
def_actor.message_count = 0


def get_port_as_string(port):
    return port.bind_address + "," +  str(port.bind_port) + ", " + port.receiver_address + "," + str(port.receiver_port)


def get_actors_from_multiple(actor):
    return actor.split("-")


def find_stanza_by_dialogue_id(dialogue_id):
    for act_name, act in sorted(play.iteritems()):
        for scene_name, scene in sorted(act.iteritems()):
            for stanza_scene_id, stanza in scene.iteritems():
                if stanza['dialogue_id'] == dialogue_id:
                    return stanza
    return None


def is_first_stanza_in_scene(dialogue_id):
    for act_name, act in sorted(play.iteritems()):
        for scene_name, scene in sorted(act.iteritems()):
            first = True
            for stanza_scene_id, stanza in sorted(scene.iteritems()):
                if stanza['dialogue_id'] == dialogue_id:
                    if first:
                        return True
                    else:
                        return False

                first = False
    return False

def get_byte_array(speech_bytes):
    return ''.join(chr(random.randint(0,255)) for _ in range(speech_bytes))

def get_byte_array_as_list(speech_bytes):
    ba=list()
    for i in range(1,speech_bytes):
        ba.append('a')
    return ba

# Not used
def def_actor_multiple_ports(transport, speech_bytes, actor):
    node = transport.workflow.get_my_node(transport)
    print "Actor Name: " + node.unique_name
    print "Received " + str(speech_bytes) + " bytes from actor " + actor

    ports = transport.workflow.get_my_output_ports(transport)

    this_message_port = transport.workflow.get_my_input_port(transport)
    incoming_edge = transport.workflow.get_edge_for_port(this_message_port.port_id)

    next_sequence_id = incoming_edge.sequence_id + 1

    print "Calculated next sequence id= " + str(next_sequence_id)

    for port in ports:
        output_edge = transport.workflow.get_edge_for_port(port.port_id)

        if  output_edge.sequence_id == next_sequence_id:
            print "Sending to port " + str(port.port_id) + " for sequence id " + str(output_edge.sequence_id)
            port.enabled = True
        else:
            print "Disabling port " + str(port.port_id) + " because it has wrong sequence id of " + str(output_edge.sequence_id)
            port.enabled = False
