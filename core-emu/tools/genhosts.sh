#!/bin/bash
# A shell script that parses a IMN file and extracts the host names and addresses and 
# appends these to the hosts file if they are not there already 
# USAGE: genhosts.sh myemulation.imn

imnfile=$1

if [ "$imnfile" == "" ]; then
    echo "USAGE: genhosts file.imn"
    exit 1
fi

if [[ $EUID -ne 0 ]]; then
   echo "This tool must be run as root in order to change the contents of the /etc/hosts file - exiting ..." 1>&2
   exit 1
fi

cat $imnfile | grep 'ip address' | grep -v wlan > /tmp/addr.txt

sed -e 's/ip address//g' /tmp/addr.txt | tr -d ' ' > /tmp/addr1.txt
sed -e 's/\/24//g' /tmp/addr1.txt | tr -d ' ' > /tmp/addr2.txt
sed -e 's/\/32//g' /tmp/addr2.txt | tr -d ' ' > /tmp/addr.txt

rm /tmp/addr1.txt
rm /tmp/addr2.txt

cat $imnfile | grep hostname > /tmp/allhosts.txt

sed -e 's/hostname//g' /tmp/allhosts.txt > /tmp/hostnames.txt

# Get the types for each node

cat $imnfile | grep type > /tmp/types.txt
sed -e 's/type//g' /tmp/types.txt | tr -d ' ' > /tmp/typelist.txt

#get number of lines

linecount=`wc /tmp/addr.txt | awk '{ print $1 }'`
echo "Number of Emulation Nodes to process" $linecount

count=0

while read line
do
hostnames[$count]=$line;
count=`expr $count + 1`;
done < "/tmp/hostnames.txt"

count=0

while read line
do
hostfile[$count]=$line"	"${hostnames[$count]};
ipAddress[$count]=$line;
count=`expr $count + 1`;
done < "/tmp/addr.txt"

# find the WLAN file and record the name
 
if [ -e $wlansyncfile ]; then
rm $wlansyncfile
fi

#  The script must be named e.g. /tmp/mobility-n3-start.sh if the WLAN is n3. 

count=0

while read line
do
if [ $line == "wlan" ]
then
mobileexec="/tmp/mobility-${hostnames[$count]}-start.sh";
echo "#!/bin/bash\n" > $mobileexec
echo "touch $wlansyncfile" >> $mobileexec
fi
count=`expr $count + 1`;
done < "/tmp/typelist.txt"

rm $wlansyncfile;

rm /tmp/allhosts.txt
rm /tmp/hostnames.txt
rm /tmp/typelist.txt
rm /tmp/types.txt

# OK, now parse the xhosts file and add if not present.

if [ -f /etc/hosts.proto ]
then
# start with the original hosts file and add
#cp /etc/hosts.proto /etc/hosts
echo ""
else
# make backup of hosts file
#cp /etc/hosts /etc/hosts.proto
echo  ""
fi

for ((  i = 0 ;  i < $linecount;  i++  ))
do
echo "checking for Node ${hostnames[$i]}"
exists=`cat /etc/hosts | grep "\+${hostnames[$i]}\+"`
echo $exists
if [ "$exists" == "" ] && [[ ${hostnames[$i]} != *"wlan"* ]]
then
echo "Ok, not already in file - will add: ${hostfile[$i]}"
#echo "#Proto Generated !" >> /etc/hosts
#echo ${hostfile[$i]} >> /etc/hosts
else
echo "Already in file - skipping"
fi
done

rm /tmp/addr.txt

