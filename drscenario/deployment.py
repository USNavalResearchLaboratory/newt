"""
    This provides the endpoints for a local deployment of the DRS workflow.
"""

from newt.Workflow import Endpoint


class Localhost():

    input_seismic_sensor_address = Endpoint("localhost", 5348)
    input_radiation_sensor_address = Endpoint("localhost", 5349)
    input_thermal_sensor_address = Endpoint("localhost", 5350)

    output_seismic_sensor_address = Endpoint("localhost", 5351)
    output_radiation_sensor_address = Endpoint("localhost", 5352)
    output_thermal_sensor_address = Endpoint("localhost", 5353)

    input1_collector_address = Endpoint("localhost", 5354)
    input2_collector_address = Endpoint("localhost", 5355)
    input3_collector_address = Endpoint("localhost", 5356)

    output1_collector_address = Endpoint("localhost", 5357)
    output2_collector_address = Endpoint("localhost", 5358)
    output3_collector_address = Endpoint("localhost", 5359)

    output_collector_to_erc_address = Endpoint("localhost", 5360)
    input_erc_address = Endpoint("localhost", 5361)

    output_erc_responder1_address = Endpoint("localhost", 5362)
    output_erc_responder2_address = Endpoint("localhost", 5363)
    output_erc_responder3_address = Endpoint("localhost", 5364)
    output_erc_responder4_address = Endpoint("localhost", 5365)

    input_responder1_address = Endpoint("localhost", 5366)
    input_responder2_address = Endpoint("localhost", 5367)
    input_responder3_address = Endpoint("localhost", 5368)
    input_responder4_address = Endpoint("localhost", 5369)

    sensor1_multicast_address = Endpoint("224.1.2.3", 5470)
    sensor2_multicast_address = Endpoint("224.1.2.4", 5470)
    sensor3_multicast_address = Endpoint("224.1.2.5", 5470)

    responder_multicast_address = Endpoint("224.1.2.6", 5470)


class Core():
    # IN CORE, Nodes are on addresses 10.0.0.1 to 10.0.0.15

    input_seismic_sensor_address = Endpoint("10.0.0.1", 5348)
    input_radiation_sensor_address = Endpoint("10.0.0.2", 5349)
    input_thermal_sensor_address = Endpoint("10.0.0.3", 5350)

    output_seismic_sensor_address = Endpoint("10.0.0.1", 5351)
    output_radiation_sensor_address = Endpoint("10.0.0.2", 5352)
    output_thermal_sensor_address = Endpoint("10.0.0.3", 5353)

    input1_collector_address = Endpoint("10.0.0.4", 5354)
    input2_collector_address = Endpoint("10.0.0.4", 5355)
    input3_collector_address = Endpoint("10.0.0.4", 5356)

    output1_collector_address = Endpoint("10.0.0.4", 5357)
    output2_collector_address = Endpoint("10.0.0.4", 5358)
    output3_collector_address = Endpoint("10.0.0.4", 5359)

    output_collector_to_erc_address = Endpoint("10.0.0.4", 5360)
    input_erc_address = Endpoint("10.0.0.5", 5361)

    output_erc_responder1_address = Endpoint("10.0.0.5", 5362)
    output_erc_responder2_address = Endpoint("10.0.0.5", 5363)
    output_erc_responder3_address = Endpoint("10.0.0.5", 5364)
    output_erc_responder4_address = Endpoint("10.0.0.5", 5365)

    input_responder1_address = Endpoint("10.0.0.6", 5366)
    input_responder2_address = Endpoint("10.0.0.7", 5367)
    input_responder3_address = Endpoint("10.0.0.8", 5368)
    input_responder4_address = Endpoint("10.0.0.9", 5369)

    sensor1_multicast_address = Endpoint("224.1.2.3", 5470)
    sensor2_multicast_address = Endpoint("224.1.2.4", 5470)
    sensor3_multicast_address = Endpoint("224.1.2.5", 5470)

    responder_multicast_address = Endpoint("224.1.2.6", 5470)
