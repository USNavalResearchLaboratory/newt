__author__ = 'scmijt'

import random
import numpy as np
import time

NORMAL_STAGE = 1
SEISMIC_STAGE = 2
EMERGENCY_STAGE = 3
RECOVERY_STAGE = 4

ERC_PORT = 3
info_detail = True


def def_sensor(transport, dataset="seismic", mean=2.0, dev=0.5, s_secs=10):
    data=[]

    if info_detail:
        print "Sensor: (" + str(def_collect.big_bang_counter) + \
          ") "+ dataset +", Mean:" + str(float(mean)) + ", STDev: " + str(float(dev))

    for j in range(int(s_secs)):
        data.append(round(random.gauss(float(mean), float(dev)), 2))

    if info_detail:
        print "Sensor: (" + str(def_collect.big_bang_counter) + \
          ") " + dataset +", Data:" + str(data)

    return {dataset: data}


def def_collect(transport, *args, **kwargs):
    ports = transport.workflow.get_my_output_ports(transport)
    dataset = None
    port_index = None

    time.sleep(1)

    if "seismic" in kwargs:
        dataset = "seismic"
        port_index = 0
        def_collect.big_bang_counter +=1

        if def_collect.big_bang_counter <= def_collect.big_bang:
            # print "Disaster countdown is " + str(def_collect.big_bang_counter) + " Disaster at " + str(def_collect.big_bang)
            pass
        else:
            print "*** Stage " + str(def_collect.stage) + " ***"

        seismic_data = kwargs["seismic"]
        if info_detail is True:
            print "Collector (" + str(def_collect.big_bang_counter) + ") Seismic data:" + str(seismic_data)
        data = np.array(seismic_data)
        new_mean = float(np.mean(data))
        new_dev = float(np.std(data))

        if def_collect.big_bang_counter == def_collect.big_bang:
            new_mean = 4.5
            new_dev = 3.0
            print "(" + str(def_collect.big_bang_counter) + ") Seismic Leak Detected !!!!!!!!!!!!!!!!!!!!!!!! "
            def_collect.stage = SEISMIC_STAGE # enter new stage

    elif "rads" in kwargs:
        dataset = "rads"
        port_index = 1
        radiation_data = kwargs["rads"]
        if info_detail is True:
            print "Collector (" + str(def_collect.big_bang_counter) + ") Radiation data: " + str(radiation_data)
        data = np.array(radiation_data)
        new_mean = float(np.mean(data))
        new_dev = float(np.std(data))

        if def_collect.big_bang_counter > def_collect.big_bang and def_collect.stage != RECOVERY_STAGE:
            new_mean += 2.0

        if new_mean > 60 and def_collect.stage < EMERGENCY_STAGE:
            print "*** Collector: Radiation Leak Detected !  ***"
            def_collect.stage = EMERGENCY_STAGE # enter new stage

    elif "thermal" in kwargs:
        dataset = "thermal"
        port_index = 2
        radiation_data = kwargs["thermal"]
        data = np.array(radiation_data)
        new_mean = float(np.mean(data))
        new_dev = float(np.std(data))

        if def_collect.big_bang_counter > def_collect.big_bang and def_collect.stage != RECOVERY_STAGE:
            new_mean += 1.0

        if new_mean > 100 and def_collect.stage  < EMERGENCY_STAGE:
            print "*** Collector: Thermal Leak Detected ! ***"
            def_collect.stage = EMERGENCY_STAGE # enter new stage

        if new_mean > 110 and def_collect.stage  < RECOVERY_STAGE:
            print "*** Collector: Seismic Leak Under control ! ***"
            print "*** Collector: Time to finish up now ! ***"
            def_collect.stage = RECOVERY_STAGE # enter new stage
            def_collect.finish_up = True
    else:
        raise Exception("No valid dataset found !")

    # wire outputs correctly

    if def_collect.finish_up is True:
        print "*** Collector: disabling output ports ! ***"
        for port in ports:
            port.enabled = False # finish feeding back
    else:
        index = 0
        for port in ports:
            if index == port_index:
                port.enabled = True
            else:
                port.enabled = False
            index += 1

    if dataset == "thermal":
        ports[ERC_PORT].enabled = True
    else:
        ports[ERC_PORT].enabled = False # only output data to ERC when Thermal values are received

 #   print "Collector (" + str(def_collect.big_bang_counter) + ") " \
  #            + dataset + " Mean:" + str(new_mean) + ", Dev is " + str(new_dev)

    return {"new_dev": new_dev, "new_mean": new_mean}

def_collect.big_bang=20
def_collect.big_bang_counter=0
def_collect.stage=1
def_collect.finish_up = False

PORT_RESPONDER_1 = 0
PORT_RESPONDER_2 = 1


def def_erc(transport, mean=0, dev=0):
    ports = transport.workflow.get_my_output_ports(transport)

    print "Emergency Response Control: Thermal Mean " + str(mean)

    if mean > 108 or mean < 100:
        if mean > 108:
            print "*** ERC: FINISHING !! ***"
        for port in ports:
            port.enabled = False # finish feeding back
    elif mean > 105:
        print "*** ERC: STAGE 2 REACHED !! ***"
        ports[PORT_RESPONDER_1].enabled = False
        ports[PORT_RESPONDER_2].enabled = True
    elif mean > 100:
        print "*** ERC: STAGE 1 REACHED !! ***"
        ports[PORT_RESPONDER_1].enabled = True
        ports[PORT_RESPONDER_2].enabled = False


def def_responder1(transport):
        print "********** Responder 1: BEING DEPLOYED !! **********"


def def_responder2(transport):
        print "********** Responder 2: BEING DEPLOYED !! **********"

