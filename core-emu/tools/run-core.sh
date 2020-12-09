#!/bin/bash

# Shell script to run a CORE demo and resize the various components to fit the screen
# You need to pass the min file for the demo and optionally, the tomboy instructions to this script  
#
# Usage: sudo ./run.sh file.imn browser resize
# e.g. sudo ./run.sh mobile.imn browser resize
# would run mobile.imn file with a browser and it will resize and reposition all the windows.
# and sudo ./run.sh mobile.imn
# would run mobile.imn file and not start a browser nor will it resize and reposition windows.

core_root=$1
imnfile=$2
script_dir=$3
python_file=$4
args=${@:5} # Need to grab rest of args ...

resize="resize" # resize to enable

echo "Called with $imnfile $python_file $args $browser $resize"

NEWTROOT="$core_root"
TOOLS_DIR="$NEWTROOT/tools"
echo $TOOLS_DIR

echo "The SCRIPT DIRECTORY WAS DEFINED AS $script_dir"

PYTHON_FILE_NAME="$script_dir/$python_file"

root=$NEWTROOT
echo "Root Core Directory is $root"

resources=$root/resources
tools=$root/tools
scripts=$root/scripts

if [[ ! -n "$imnfile" && ! -n "$python_file" ]] ; then
    echo "Usage: ./run-core.sh file.imn python_class_name [args] [browser] [resize]"
    exit 1
fi

cp $resources/*.png /tmp/
cp $resources/*.jpg /tmp/

imnfilepath=$root/imn/$imnfile
echo "IMN file is $imnfilepath"

if ! [ $(id -u) = 0 ]; then
   echo "I am not root! give me more power :)"
   exit 1
fi


#First generate the new imn file by applying a find/replace on the resources directory to generate content

echo $resources

# watch out here. if there are slashes in the variable sed get's completely confused so hence the odd @ chars instead.
sed -e "s@RESOURCES_DIR@$resources@g" $imnfilepath > /tmp/$imnfile

#sysctl !!! Turn off the reverse path filtering

sudo sysctl -w net.ipv4.conf.all.rp_filter=0
sudo sysctl -w net.ipv4.conf.lo0.rp_filter=0
sudo sysctl -w net.ipv4.conf.eth0.rp_filter=0
sudo sysctl -w net.ipv4.conf.default.rp_filter=0

#and redirects

sudo sysctl -w net.ipv4.conf.all.accept_redirects=0
sudo sysctl -w net.ipv4.conf.all.send_redirects=0
sudo sysctl -w net.ipv4.conf.default.accept_redirects=0
sudo sysctl -w net.ipv4.conf.default.send_redirects=0
sudo sysctl -w net.ipv4.conf.lo.accept_redirects=0
sudo sysctl -w net.ipv4.conf.lo.send_redirects=0
sudo sysctl -w net.ipv4.conf.eth0.accept_redirects=0
sudo sysctl -w net.ipv4.conf.eth0.send_redirects=0
sudo sysctl -w net.ipv6.conf.all.accept_redirects=0
sudo sysctl -w net.ipv6.conf.default.accept_redirects=0
sudo sysctl -w net.ipv6.conf.lo.accept_redirects=0
sudo sysctl -w net.ipv6.conf.eth0.accept_redirects=0

#Generate the /etc/hosts file for the given imn file

echo "Generating hosts file from IMN file: $imnfile"

cd $tools
./genhosts.sh $imnfilepath

#turn on shell monitoring mode so that fg works ...
set -m


/etc/init.d/core-daemon start

#start CORE with the replaced version of this imn file which is stored in /tmp/$imnfile

core-gui --start /tmp/$imnfile &

sleep 2

wlans=`cat $imnfilepath | grep "wlan"| wc -l`

if [ $wlans -gt 0 ]
then
    delay=20
    echo "This is a wireless network and we have $wlans wireless LANs, setting the delay to $delay"
else
    delay=20
    echo "This is a fixed network, setting the initialisation delay to $delay"
fi

cd $tools

if [ "$resize" = "resize" ]
then
echo "Resizing the widgets to fit nicely onto thew screen, as requested ..."
./change-geometry.sh .imn 65 0 35 75
fi


echo "Sleeping for $delay seconds"
sleep $delay

nodes=`cat /etc/hosts | grep " \+n[0-9]" | wc -l`

cat /etc/hosts | grep " \+n[0-9]" | awk '{ print $2 }' > /tmp/nodes.txt

echo "Number of nodes is --$nodes--"

pyname=`ls /tmp | grep py. | tr -d ' '`
echo "running on Core instance in $pyname"

cd $script_dir

while read node
do
    node_dir=/tmp/$pyname/$node
    echo "Running VCMD for Node: $node"
    vcmd -c $node_dir -- $root/bin/core.sh $PYTHON_FILE_NAME $args &
done < "/tmp/nodes.txt"


