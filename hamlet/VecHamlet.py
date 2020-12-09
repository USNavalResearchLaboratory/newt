from __future__ import print_function    # (at top of module)

import json
import subprocess
import time
import operator
from vectors import *
#from newt.wire.Adapter import Adapter
#from newt.wire.Transport import Transport

import logging
import time
import timeit
import bitarray as ba
import cPickle
from operator import itemgetter
from collections import Counter

__author__ = 'simpkin'


def get_act_number(act_string):
    act_string = act_string[4:]
    parts = act_string.split(".")
    return str(parts[0])


def get_scene_number(scene_string):
    act_string = scene_string[6:]
    parts = act_string.split(".")
    return str(parts[0])


def split_stanza(lns, splitters, maxwords):
    '''
    we want to split the stanza so the the number of words is less than maxWords 
    we will split based on knowledge punctuation creating natural splits, then by maxwords
    
    :param lns: stanza to split 
    :param splitters: an ordered list to try the split on, e.g. ['.', ';', ':', ','] 
    :param maxwords: Max number of words in one section 
    :return: array of lines
    '''

    newlines = []
    for l1 in lns:
        l1 = l1.replace("\n", "").strip()
        if len(l1.split()) > maxwords:
            if len(splitters) > 0:
                newlines.extend(split_stanza(l1.split(splitters[0]), splitters[1:], maxwords))
            else:
                # The line is still too long but we have no more splitters
                # we will split the line by length
                tmp = l1.split()
                llen = len(tmp)
                m = 0
                while m + maxwords <= llen:
                    newlines.append(' '.join(tmp[m:m + maxwords]))
                    m += maxwords
                newlines.append(' '.join(tmp[m:llen]))  # grab any leftover chunk
        else:
            newlines.append(l1)

    return newlines


def buildchunks(veclist, chunksize):
    llen = len(veclist)
    m = 0
    chnks = []
    while m + chunksize <= llen:
        newchunk = veclist[m:m + chunksize]
        chnks.append(newchunk)
        m += chunksize

    if m < llen:
        chnks.append(veclist[m:llen])  # grab any leftover chunk
    return chnks


def get_key(key):
    try:
        return int(key)
    except ValueError:
        return key


def t1_method(transport_class, *args, **kwargs):
    print("In test target method for " + transport_class.__class__.__name__ + ", Data received is :")

    for i in xrange(len(args)):
        print(args[i])

    for key, value in kwargs.iteritems():
        print("%s = %s".format(key, value))

    transport_class.close()  # close each receiver after one receive.


class ChunkService(NewChunkPvecs):
    starttracking = False  # for debug
    message_sent = 0

    def __init__(self, name, veclist, level, payload=None, maxvecs=100, chunks=None, do_not_pad=True):
        super(ChunkService, self).__init__(name, veclist, level, payload, maxvecs, chunks, do_not_pad=do_not_pad)
        self.packed = np.packbits(self.myvec)
        self.in_port = -1
        self.out_port = -1
        self.state = 3
        self.next_state = 3
        self.match_tag = None
        self.match_id = None
        self.current_match = 0
        self.match_list = None
        self.cnt_me = 0

    def rx_method(self, transport_class, *args, **kwargs):
        if self.state == 3:
            self.waitingforacivation(transport_class, *args, **kwargs)
        elif self.state == 4:
            self.waitingforcompletion(transport_class, *args, **kwargs)

    def send(self, vec):
        adapter = Adapter(Transport.Multicast, Transport.PICKLE)
        ms1 = adapter.get_sender_instance("localhost", self.out_port, "224.1.2.3", 5353)
        ms1.send(np.packbits(vec))
        time.sleep(1)
        ms1.close()

    def waitingforacivation(self, transport_class, *args, **kwargs):
        vtab = "\t" * (6 - self.level)
        invec = np.unpackbits(args[0])
        hd = float(hamming(self.myvec, invec))

        if hd > ChunkService.trace_threshold:  # we have a match
            # Here we need to transmit the chunks 'myvec' vector which is a cleaned up version of that detected
            # We then listen for the sub-services to finish after which we 'shift' the recieved vector and retransmit
            # to complete the next pier service
            if self.chunklist is None:
                self.state = 3
                print(vtab, '{:04d}'.format(self.chunk_id), "WORK:", self.name, hd)
                newvec = XOR(invec, self.getPermutor(1))
                # return self.name, broadcast_to_all, newvec, hd
                self.send(newvec)
            else:
                # we save the recieved commandVec because we must shift and retransmit when our bit is complete
                self.state = 4  # wait for completion
                self.commandvec = invec
                print(vtab, '{:04d}'.format(self.chunk_id), "MATCH:", self.name, hd)
                # return self.name, broadcast_to_all, self.myvec, hd
                self.send(self.myvec)
        else:
            # print(vtab, '{:04d}'.format(self.chunk_id), "SKIP:", self.name, hd)
            # We send nothing here
            pass

    def waitingforcompletion(self, transport_class, *args, **kwargs):
        vtab = "\t" * (6 - self.level)
        invec = np.unpackbits(args[0])
        hd = hamming(self.stopvec, invec)
        if hd > ChunkService.trace_threshold:
            # found the stop vec which would be transmitted from below
            # We need to shift the RXvec and transmit it
            # we have then finished
            print(vtab, '{:04d}'.format(self.chunk_id), "STOP: shifting and resending", self.name, hd)

            shiftedvec = XOR(self.commandvec, self.getPermutor(0))
            self.state = 3
            # return self.name, broadcast_to_all, shiftedvec, hd
            self.send(shiftedvec)
        else:
            # print(vtab, '{:04d}'.format(self.chunk_id), "WAITING_STOP:", self.name, hd)
            # We send nothing here
            pass


    def setports(self, inp, out):
        self.in_port = inp
        self.out_port = out

    def sim_rx(self, dumy, *args):
        #  DEBUG
        if ChunkService.break_on_chunk_id == -1:
            ChunkService.break_on_chunk_id = 0
        if self.chunk_id == ChunkService.break_on_chunk_id:
            ChunkService.break_on_chunk_id = ChunkService.break_on_chunk_id

        if self.state == 3:
            return self.sim_waitingforacivation(dumy, *args)
        elif self.state == 4:
            return self.sim_waitingforcompletion(dumy, *args)
        elif self.state == 5:
            return self.sim_collect_matches(dumy, *args)
        elif self.state == 6:
            return self.sim_decide_matches(dumy, *args)
        elif self.state == 7:
            return self.sim_complete_level_zero(dumy, *args)
        elif self.state == 8:
            return self.sim_start_sub_level(dumy, *args)


    def sim_waitingforacivation_safe(self, transport_class, *args, **kwargs):
        vtab = "\t" * (6 - self.level)
        invec = args[0]

        hd, next_vec = self.check_for_activation(invec, self.myvec)
        if hd < ChunkService.trace_threshold:
            # still waitingforacivation
            return self.name, None, None, hd

        if 0 and ChunkService.starttracking:
            print("WaitingforActive:", self.name, hd)

        # Here we need to transmit the chunks 'myvec' vector which is a cleaned up version of that detected
        # We then listen for the sub-services to finish after which we 'shift' the recieved vector and retransmit
        # to complete the next pier service
        self.next_vec = next_vec
        if self.level == 0:
            self.state = 3
            # print(vtab, '{:04d}'.format(self.chunk_id), "WORK:", self.name, hd)
            playoutputcheck.append(self.name)
            return self.name, broadcast_to_all, self.next_vec, hd
        else:
            # we save the recieved commandVec because we must shift and retransmit when our bit is complete
            self.state = 5  # wait for completion
            self.commandvec = invec

            matchtag = XOR(ChunkService.role_match_message, invec)
            myid = XOR(ChunkService.role_id, getRandVec(self.veclen))
            matchval = XOR(ChunkService.role_matchval, make_number_vec(str(int(hd * 10000.0))))
            match_vec = normalize(matchtag + myid + matchval, 3)

            self.current_match = hd
            self.match_tag = matchtag
            self.match_id = myid
            self.match_list = []
            print(vtab, '{:04d}'.format(self.chunk_id), "MATCH:", self.name, hd)
            # return self.name, broadcast_to_all, startvec, hd
            return self.name, broadcast_to_all, match_vec, hd

    def sim_waitingforacivation(self, transport_class, *args, **kwargs):
        vtab = "\t" * (6 - self.level)
        invec = args[0]
        sender = args[1]  # For DEBUG

        hd, next_vec = self.check_for_activation(invec, self.myvec)
        if hd < ChunkService.trace_threshold:
            return self, None, None, hd  # still waitingforacivation

        if 0 and ChunkService.starttracking:  # For DEBUG
            print("WaitingforActive:", self.name, hd)

        # Here we need to transmit the chunks 'myvec' vector which is a cleaned up version of that detected
        # We then listen for the sub-services to finish after which we 'shift' the recieved vector and retransmit
        # to complete the next peer service
        self.next_vec = next_vec

        negotiate_matches = False  # For DEBUG
        if self.chunklist is None:  # This is usually level 0, there are no sub-vectors to start
            if negotiate_matches:
                self.next_state = 7
                self.state = 5  # collect matches
            else:
                # Override because we are resolving matches outside of the RX loop
                self.next_state = 3  # This is not used under override
                self.state = 3
                return self, broadcast_to_all, self.next_vec, hd
        else:
            if negotiate_matches:
                self.next_state = 8
                self.state = 5  # collect matches
            else:
                # Override because we are resolving matches outside of the RX loop
                self.next_state = 3   # This is not used under override
                self.state = 4
                startvec = self.get_start_vec()
                return self, broadcast_to_all, startvec, hd

        # This section is(can be) used to negotiate best match,
        # however for the simulation version we are resolving best match outside of the receive code
        # see '** RESOLVE MATCHES **'

        matchtag = XOR(ChunkService.role_match_message, invec)
        myid = XOR(ChunkService.role_id, getRandVec(self.veclen))
        matchval = XOR(ChunkService.role_matchval, make_number_vec(str(int(hd * 10000.0))))
        match_vec = normalize(matchtag + myid + matchval, 3)

        self.current_match = hd
        self.match_tag = matchtag
        self.match_id = myid
        self.match_list = []
        return self, broadcast_to_all, match_vec, hd

    def sim_complete_level_zero(self, transport_class, *args, **kwargs):
        vtab = "\t" * (6 - self.level)
        invec = args[0]
        sender = args[1]  # For DEBUG

        hd = hamming(invec, self.match_tag)
        if hd < ChunkService.trace_threshold:
            return self, None, None, hd
        else:
            self.next_state = 3
            self.state = 3
            print(vtab, '{:04d} WORK: {:0.4f}'.format(self.chunk_id, hd), self.name)
            playoutputcheck.append(self.name)
            return self, broadcast_to_all, self.next_vec, hd

    def sim_start_sub_level(self, transport_class, *args, **kwargs):
        vtab = "\t" * (6 - self.level)
        invec = args[0]
        sender = args[1]  # For DEBUG

        hd = hamming(invec, self.match_tag)
        if hd < ChunkService.trace_threshold:
            return self, None, None, hd
        else:
            self.next_state = 3
            self.state = 4
            startvec = self.get_start_vec()
            return self, broadcast_to_all, startvec, hd

    def sim_waitingforcompletion(self, transport_class, *args, **kwargs):
        vtab = "\t" * (6 - self.level)
        invec = args[0]
        sender = args[1]  # For DEBUG

        hd, dmy = self.check_for_activation(invec, self.stopvec)
        if hd < ChunkService.trace_threshold:
            # still waitingforcompletion
            return self, None, None, hd

        # if ChunkService.starttracking:
        #    print(vtab, '{:04d}'.format(self.chunk_id), "WAITING_STOP:", self.name, hd)

        # found the stopvec which would be transmitted from below
        # We need to shift the RXvec and transmit it
        # we have then finished
        # print(vtab, '{:04d}'.format(self.chunk_id), "STOP: shifting and resending", self.name, hd)
        # print(vtab, '{:04d}'.format(self.chunk_id), "GOT STOP:", self.level, "  :   ", self.name, hd)
        if self.level == 2:
            print()

        self.state = 3  # Waiting from command
        return self, broadcast_to_all, self.next_vec, hd

    def sim_collect_matches(self, transport_class, *args, **kwargs):
        vtab = "\t" * (6 - self.level)
        invec = args[0]
        sender = args[1]  # For DEBUG

        hd = hamming(invec, self.match_tag)
        if hd >= ChunkService.trace_threshold:
            matchval = XOR(ChunkService.role_matchval, invec)
            match_str = decode_numbervec(matchval)
            match = int(match_str)

            myidcheck = hamming(invec, self.match_id)
            if myidcheck >= ChunkService.trace_threshold:
                # This is my match value
                ChunkService.message_sent += 1
                #if mulltiple_answers:
                #    print(vtab, "Collecting matches, my match,", match, self.name)
                self.match_list.append(("me", match))
            else:
                #if mulltiple_answers:
                #    print(vtab, "Collecting matches, other match,", match)
                self.match_list.append(("other", match))

        # Temp for debug
        # This does not work because it is changing state after receiving only one message
        # so it can not build up a list to decide which is best
        self.state = 6
        return self, broadcast_to_all, invec, hd
        # return self, None, None, hd

    def sim_decide_matches(self, transport_class, *args, **kwargs):
        vtab = "\t" * (6 - self.level)
        invec = args[0]
        sender = args[1]  # For DEBUG

        hd = hamming(invec, self.match_tag)
        if hd < ChunkService.trace_threshold:
            return self, None, None, hd

        if mulltiple_answers:  # For DEBUG
            hd = hd

        mymatch = -1
        bestname = "other"
        bestmatch = 0
        cnt_me = 0
        for name, match in self.match_list:
            if match > bestmatch:
                bestmatch = match
                bestname = name

        if bestname in "me":
            mymatch = bestmatch
            cnt_me += 1

        if cnt_me == 0:
            # I was not the best match go back to waitingforactivation
            # print(vtab, "NOT-BEST_MATCH-->SLEEP", mymatch, self.name)
            self.state = 3
            return self, None, None, hd

        if cnt_me > 1:
            # Here we need to sleep for a probabilistic short interval and then send our reply
            # the delay need to be long enough to observe someone else replying first
            # We will simulate this by setting a shared variable so that the first of the best matches
            # will do the transmission
            #
            # In the real receive method we will enter state 'looking_for_matching_reply'
            # and set a timer, if we receive a matching message before our timer expires we will
            # cancel the timer and go to state 'waiting_for_activation' not sending our reply
            # if our timer expires and we have not seen a message we will send ours
            if ChunkService.message_sent == 0:
                ChunkService.message_sent = 0  # To stop further messages being sent
                self.state = self.next_state
                self.next_state = 3
                print(vtab, '{:04d} BEST  : {:0.4f}'.format(self.chunk_id, bestmatch), self.name)
                print(vtab, '{:04d} MyMATCH: {:0.4f}'.format(self.chunk_id, mymatch), self.name)
                return self, broadcast_to_all, invec, hd
            else:
                self.state = 3
                print(vtab, '{:04d} CAN_MyM: {:0.4f}'.format(self.chunk_id, mymatch), self.name)
                return self, None, None, hd

        '''
        # We can deal with the outcome in the real-listeners right here
        # but for the simulated loop I have installed another pass to allow the 
        # Similated broadcast loops to stay in sync
        # Temp for debug
        if self.next_state == 7:
            self.next_state = 3
            self.state = 3
            # print(vtab, '{:04d}'.format(self.chunk_id), "WORK:", self.name, hd)
            # print(vtab, "Deciding matches, my match,", match, self.name)
            playoutputcheck.append(self.name)
            return self, broadcast_to_all, self.next_vec, hd
        else:
            self.next_state = 3
            self.state = 4
            startvec = ROLL(XOR(NewChunkPvecs.permVecs[0][0], self.myvec), -1)
            return self, broadcast_to_all, startvec, hd
        '''

        self.state = self.next_state
        self.next_state = 3
        return self, broadcast_to_all, invec, hd



class Actor(object):
    def __init__(self, name, veclen):
        self.name = name
        self.myVec = getRandVec(veclen)
        self.packed = np.packbits(self.myVec)
        self.myLines = []


    def addVec(self, v1):
        self.myLines.append(v1)


def chunkWordVector(word):

    lettervecs = [symbol_dict[a] for a in word]

    cnk = ChunkService(word, lettervecs, 0, do_not_pad=True)
    linecheck.append(word)  # record the word for verification
    return cnk


def chunkSentenceVector(sentence):
    words = sentence.split()
    wordvecs = [createWordVector(word.strip()) for word in words]
    if len(wordvecs) == 0:
        pass
    if usechunksforWords:
        db_sentence = ChunkService.createchunkfromchunks(sentence, wordvecs, hierarchy_level[0], wordvecs)
    else:
        db_sentence = ChunkService(sentence, wordvecs, hierarchy_level[0])
        linecheck.append(sentence)
    return db_sentence


infile = open('hamlet_stanzas.json', 'r')
play = json.load(infile)

# Set up reporting options and what level of chunking we want, words or sentences
report_input_lines = False
report_end_of_subtask = False
show_multiple_matches = True
usechunksforWords = False
usechunksforWords_output_individual_words = True
usechunksforWords_show_word_matches = True
no_scenes_per_act = 100
no_acts = 100
repeat_test = False

print("Run config:")
if usechunksforWords:
    print("\n\t\tChunking at 'word' level:")
else:
    print("\n\t\tChunking at 'line' level:")
if show_multiple_matches:
    print("\n\t\tShowing multiple matches")
    if usechunksforWords_show_word_matches:
        print("\n\t\tShowing multiple match word break down (verbose)")
    else:
        print("\n\t\tNOT Showing word match break down")
    if usechunksforWords_output_individual_words:
        print("\n\t\tShow chosen word matches on separate lines (verbose)")
    else:
        print("\n\t\tDo NOT show chosen Word matches separately")
else:
    print("\n\t\tNOT Showing multiple matches")

if no_scenes_per_act > 7:
    no_scene_str = "all"
else:
    no_scene_str = str(no_scenes_per_act)

if no_acts > 7:
    no_acts_str = "all"
else:
    no_acts_str = str(no_acts)

print("\n\t\tProcessing", no_acts_str, "acts", no_scene_str, "scenes per act")
if repeat_test:
    repeat_str = "on"
else:
    repeat_str = "off"
print("\n\t\tLooping (to test with different randoms) is", repeat_str)


# see if we wanna change the run
inp = raw_input("\n\nDo you want to change the run setup, Y/N? (default='N'): ")
if 'y' in inp.lower():
    inp = raw_input("\n\nChunk to line or word level, L/W? (default='L'): ")
    if inp != "":
        usechunksforWords = 'w' in inp.lower()

    inp = raw_input("Report multiple matches Y/N? (default='Y'): ")
    if inp != "":
        show_multiple_matches = 'n' not in inp.lower()

    if show_multiple_matches:
        if usechunksforWords:
            inp = raw_input("Show multiple match word break down (verbose) Y/N? (default='Y'): ")
            if inp != "":
                usechunksforWords_show_word_matches = 'n' not in inp.lower()
            inp = raw_input("Show chosen word match on separate lines (verbose) Y/N? (default='Y'): ")
            if inp != "":
                usechunksforWords_output_individual_words = 'n' not in inp.lower()

    inp = raw_input("Show input lines Y/N? (default='N'): ")
    if inp != "":
        report_input_lines = 'y' in inp.lower()

    inp = raw_input("Show sub-task complete message Y/N? (recommended-default='N'): ")
    if inp != "":
        report_end_of_subtask = 'y' in inp.lower()

    inp = raw_input("Enter number of acts to process (default=''(all)): ")
    if inp != "":
        no_acts = int(inp)
    else:
        no_acts = 100

    inp = raw_input("Enter number of scenes per act to process (default=''(all)): ")
    if inp != "":
        no_scenes_per_act = int(inp)
    else:
        no_scenes_per_act = 100

    inp = raw_input("Loop, to test with different randoms Y/N? (default='N'): ")
    if inp != "":
        repeat_test = 'y' in inp.lower()

runs = 0
runspassed = 0
runsfailed = 0
first_pass_vecs = []
while runs < 1000:
    startTime = timeit.default_timer()

    my_random.seed()
    symbol_dict = createSymbolVectors(symbols, 10000)

    if 0:
        for _ in xrange(20):
            A = getRandVec(10000)
            B = getRandVec(10000)
            C = getRandVec(10000)

            AB = XOR(A, B)
            C_AB = XOR(C, AB)

            CA = XOR(C, A)
            CA_B = XOR(CA, B)

            print(hamming(CA_B, C_AB))
        quit()

        for _ in xrange(20):
            A = getRandVec(10000)
            B = getRandVec(10000)
            C = getRandVec(10000)

            Z1 = ROLL(normalize(A + B + C, 3), 1)
            Z2 = normalize(ROLL(A, 1) + ROLL(B, 1) + ROLL(C, 1), 3)

            print(hamming(Z1, Z2))

        quit()

        for _ in xrange(20):
            A = getRandVec(10000)
            P = getRandVec(10000)

            P1 = ROLL(P, 1)
            A1 = ROLL(A, 1)
            P1A1 = XOR(P1,A1)

            PA = XOR(P, A)
            PA1 = ROLL(PA, 1)

            print(hamming(PA1, P1A1))
        quit()

    runs += 1
    vtab = '\t'
    actorDict = {}
    linechunks = []
    subScenes = []
    scenes = []
    acts = []
    scene_cnt = no_scenes_per_act
    act_cnt = no_acts

    if usechunksforWords:
        createWordVector = chunkWordVector  # Using our own chunking scheme, allows individual words as services
    else:
        createWordVector = createWordVector_GB  # Graham's piBinding - faster

    linecheck = []
    lcnt = 1
    hierarchy_level = [0]  # This is used to maintain hierarchy level
    for act_name, act in sorted(play.iteritems()):
        this_act = get_act_number(act_name)
        act_name = act_name.replace("\n", "").strip()
        print("\n\n", act_name)
        # lcnt = 1
        if 1:
            scenes = []
            for scene_name, scene in sorted(act.iteritems()):
                this_scene = get_scene_number(scene_name)
                scene_name = scene_name.replace("\n", "").strip()
                print("\n\t", scene_name)
                # lcnt = 1
                subScenes = []
                lineVecs = []
                linechunks = []
                hierarchy_level = [0]  # Lines are at level 0, ATM we need this to get an 'action' service to terminate
                for sid, detail in sorted(scene.iteritems(), key=lambda xyz: get_key(xyz[0])):
                    lines = detail['line'].split('--')  # we don't want to keep '--' within the stanza

                    lines = split_stanza(lines, ['.', ';', ':', ','], NewChunkPvecs.maxchunksize)
                    # lines = split_stanza(lines, ['.', ';', ':', ','], 70)  # %%% Why does this not work when line above does
                    for l in lines:
                        if len(l) > 0:
                            # Make a vector for this sentence
                            # we will then store this sentence in the actor's vector bank

                            # l = str(lcnt) + '*' + str(sid) + '*' + detail['actor'] + '*' + l
                            #l = "{0:4d}".format(lcnt) + '*' + detail['actor'] + '*' + l
                            #l = detail['actor'] + '*' + l
                            if report_input_lines:
                                print("\t\t{:d} {:s} {:s}: {:s}".format(lcnt, sid, detail['actor'], l))

                            lcnt += 1
                            v = chunkSentenceVector(l)
                            lineVecs.append(v)

                            #if detail['actor'] in actorDict.keys():
                            #    actorDict[detail['actor']].addVec(v)
                            #else:
                            #    actorDict[detail['actor']] = Actor(detail['actor'], 10000)
                            #    actorDict[detail['actor']].addVec(v)

                thisscene = ChunkService.buildchunks(act_name + "_" + scene_name, lineVecs, hierarchy_level)
                scenes.append(thisscene)
                scene_cnt -= 1
                if scene_cnt == 0:
                    scene_cnt = no_scenes_per_act
                    break  # to test just one scene

        # scenes combine to make acts
        thisact = ChunkService.buildchunks(act_name, scenes, hierarchy_level)
        acts.append(thisact)
        act_cnt -= 1
        if act_cnt == 0:
            act_cnt = no_scenes_per_act
            break  # to test just one scene

    # Acts combine to make the full play
    hamlet = ChunkService.buildchunks("Hamlet", acts, hierarchy_level)
    print("\n\nTime taken to build representation:", timeit.default_timer() - startTime, "\n\n")
    # continue

    allchunks = []  # This is used to simulate a broadcast
    hamlet.flattenchunkheirachy(allchunks)
    chunkvecs = []
    hamlet.get_flat_list_of_vectors_from_chunkheirachy(chunkvecs)

    if 0:  # Verify that everything will decode correctly
        print("\n\n Verifying chunk structure will decode correctly\n\n ")
        errors = []
        linenumber = [0]
        minmatch = [1]
        maxmatch = [0]
        minstop = [1]
        maxstop = [0]
        # Start the recursion
        # startvec = ROLL(XOR(ChunkService.permVecs[0][0],hamlet.myvec))
        hamlet.verifychunkstructure(
            None, minmatch, maxmatch, minstop, maxstop, errors, linenumber, rpt_lines=2, rpt_stops=2)

        if len(errors) > 0:
            print("Verification FAILED with,", len(errors), "errors.\n")
            for s in errors:
                print(s)
        else:
            print("Verification PASSED")

        print("\t\tminmatch {:0.4f}".format(minmatch[0]))
        print("\t\tmaxmatch {:0.4f}".format(maxmatch[0]))
        print("\t\tminStop  {:0.4f}".format(minstop[0]))
        print("\t\tmaxStop  {:0.4f}".format(maxstop[0]))
        print()
        quit()

    '''
    ====================================================================
    Used debuging the build loop 
    ====================================================================
    if runs == 1:
        first_pass_vecs = chunkvecs[:]
    else:
        for i in xrange(len(first_pass_vecs)):
            if (1.0 - hamming(first_pass_vecs[i], chunkvecs[i]) > 0.001):
                print("Failed")

    ChunkService.myrandom = None
    print('==========================')
    continue
    '''
    # OLD DEBUG
    # hamlet.searchvec(chunkvecs)
    # bestchunk, name, bestmatch = hamlet.getbestchunk(allchunks, hamlet.myvec)
    # print(bestchunk.name)
    # print("\n")


    # simulate broadcast by calling each service's listener method with the vector
    # get back an action function and match  to be executed by each listener
    #
    # All listeners except, hopefully, the single matching listener's return function will simply be 'sleep-return'= None
    #
    # The func returned by the matching listner will be 'shift & broadcast' casuing a recusion
    # The matching listerner will execute its 'action' function which may well be another broadcast which will cause a
    # recusion

    def broadcast_to_all(*args):
        return broadcastvec(allchunks, *args)


    def broadcastvec(sendto, *args):
        actions = []
        for cs in sendto:  # for each ChunckService
            service_name, action, retargs, match = cs.sim_rx(None, *args)
            if action is not None:
                # add the action to the action list
                actions.append({"sname": service_name, "method": action, "args": retargs, "hd_match": match})
        return actions

    hamlet.state = 3
    hamlet.commandvec = None
    startvec = hamlet.get_start_vec()
    actions = [{"sname": hamlet, "method": broadcast_to_all, "args": startvec, "hd_match": 1.0}]
    playoutputcheck = []
    mulltiple_answers = False
    while len(actions) > 0:
        new_actions = []
        for a in actions:
            new_actions.extend(a['method'](a['args'], a['sname']))

        if len(new_actions) == 0:
            break

        if len(new_actions) > 1:
            if show_multiple_matches:
                mulltiple_answers = True
                if usechunksforWords:
                    print("\n", "\t" * 8, "mulitiple matches recieved choosing from:", len(new_actions))
                    if usechunksforWords_show_word_matches:
                        match_str = ""
                        la = [a['sname'].name for a in new_actions]
                        c = Counter(la)
                        for k, v in c.items():
                            match_str += "{:s} ({:d}) ; ".format(k, v)
                        print("\t" + match_str)
                else:
                    for a in new_actions:
                        print("mulitiple matches recieved", a['hd_match'], a['sname'].name)
        else:
            mulltiple_answers = False

        # DEBUG cheat ** RESOLVE MATCHES **
        # we are running synchronously so we will resolve matches here
        d = sorted(new_actions, key=itemgetter('hd_match'), reverse=True)
        for cs in d[1:]:
            # Change state back to listening for activation for all but the winner
            cs['sname'].state = 3

        cs = d[0]['sname']
        vtab = "\t" * (6 - cs.level)
        if cs.state == 3:
            if cs.chunklist is None:
                if usechunksforWords_output_individual_words:
                    vtab = "\t" * (8 - cs.level)
                else:
                    vtab = "\t" * (6 - cs.level)
                if not usechunksforWords or usechunksforWords_output_individual_words:
                    print(vtab, '{:04d} WORK: {:0.4f}'.format(cs.chunk_id, d[0]['hd_match']), cs.name)
                playoutputcheck.append(cs.name)
            else:
                if report_end_of_subtask:
                    print(vtab, '{:04d} DONE: {:0.4f}'.format(cs.chunk_id, d[0]['hd_match']), cs.name)

        elif cs.state == 4:
            if usechunksforWords:
                print("\n", vtab, '{:04d} MATCH: {:0.4f}'.format(cs.chunk_id, d[0]['hd_match']), cs.name)
            else:
                print(vtab, '{:04d} MATCH: {:0.4f}'.format(cs.chunk_id, d[0]['hd_match']), cs.name)

        actions = [d[0]]

    outputerrors = []
    maxlines = min(len(linecheck), len(playoutputcheck))
    resync_offset = 0
    verified = True
    for i in xrange(maxlines):
        if linecheck[i + resync_offset] != playoutputcheck[i]:
            verified = False
            outputerrors.append(i)
            # try to resync
            # tho I guess it is possible to get repeat lines, we assume we are a line missing
            # Will will assume we are a line missing in our output...
            # scan ahead thro linecheck to see if we can resync
            j = 0
            for j in xrange(maxlines-i):
                if linecheck[j + i] == playoutputcheck[i]:
                    break
            if linecheck[j + i] == playoutputcheck[i]:
                resync_offset = j
            else:
                print("Verify error found at line", i)
                print("Should be:", linecheck[i])
                print("Foundline:", playoutputcheck[i])
                break

    print("Tota lines from source:", len(linecheck))
    if verified:
        if len(linecheck) != len(playoutputcheck):
            runsfailed += 1
            print("FAILED: All lines MATCHED - but - vector processing quit early at line,", maxlines, "; Total Runs failed", runsfailed)
        else:
            runspassed += 1
            print("SUCCESS,", maxlines, "Checked and verified; Total Runs passed", runspassed)
    else:
        runsfailed += 1
        print("\n\nFailed on", len(outputerrors), "lines; Total Runs failed", runsfailed)
        for i in outputerrors:
            print(i, "Should be:", linecheck[i])
            print(i, "Foundline:", playoutputcheck[i])
            print()
    print("Total Runs passed", runspassed, "; Total Runs failed", runsfailed)

    NewChunkPvecs.init_class_vars(10000)
    NewChunkPvecs.myrandom = None
    if not repeat_test:
        quit()

quit()


def recurse_chuncktree(chunk, vtabs):
    if chunk.level == 2: return
    bestchunk = chunk
    # print("Entering chunk,", chunk.name, chunk.level)
    tracevec = chunk.myvec
    for p in ChunkService.permVecs[0]:
        bestchunk, name, bestmatch = bestchunk.getbestchunk(allchunks, tracevec)
        print(vtabs, name, "HD = ", bestmatch)
        if name == "stop":
            return
        else:
            recurse_chuncktree(bestchunk, vtabs + "\t")

        tracevec = XOR(tracevec, p)

    return

hamlet.recurse_chuncktree(allchunks, "")

quit()



#adapter = Adapter(Transport.Multicast, Transport.PICKLE)

# Here we must start the all recievers
# we are using multicast cause I don't know how to do broadcast

#ms = adapter.get_sender_instance("localhost", 4545, "224.1.2.3", 5353)

#recievers = []
#in_port_no = 4548
#for r in subScenes:
#    r.setports(in_port_no, in_port_no + 1)
#    recievers.append(adapter.get_receiver_instance(r.rx_method, "localhost", in_port_no, "224.1.2.3", 5353))
#    in_port_no += 2

#for r in scenes:
#    r.setports(in_port_no, in_port_no + 1)
#    recievers.append(adapter.get_receiver_instance(r.rx_method, "localhost", in_port_no, "224.1.2.3", 5353))
#    in_port_no += 2

#for r in acts:
#    r.setports(in_port_no, in_port_no + 1)
#    recievers.append(adapter.get_receiver_instance(r.rx_method, "localhost", in_port_no, "224.1.2.3", 5353))
#    in_port_no += 2

#for r in recievers:
#    r.start()

#time.sleep(10)

#ms.send(np.packbits(hamlet.myvec), "two", "three", "...", first_name="Ian", last_name="Taylor")
#time.sleep(30)
#ms.close()
