This directory contains bootstrapping tools for the CORE EMU environment:

- the imn directory contains the CORE IMN scenarios that can be used by a number of different emulations
- the resources directory contains images and candy for the scenarios (which is copied into /tmp) by the scripts
- tools contains the bootstrapping tools used to interact with core and do things like layouts, initialise the hosts file and so on.

Dependencies

python 2.7
netifaces - for getting the local host address reliably
    easy_install netifaces
wmctrl - for resizing the CORE window
    sudo apt-get install wmctrl
