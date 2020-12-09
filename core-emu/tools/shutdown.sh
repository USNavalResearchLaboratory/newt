#!/bin/bash

# You need to configure FireFox to not restore session:
#    a. Type about:config into the location bar and press enter
#    b. Accept the warning message that appears, you will be taken to a list of preferences
#    c. In the filter box type resume to bring up a small number of preferences
#    d. Double-click on the preference browser.sessionstore.resume_from_crash to change its value to false 

echo "Cleaning and Killing things :)";

psid=`ps -aef | grep firefox | grep -v grep | awk '{ print $2 }'`;
corepsid=`ps -aef | grep core.tcl | grep -v grep | awk '{ print $2 }'`;
tomboy=`ps -aef | grep tomboy | grep -v grep | awk '{ print $2 }'`;

echo "Core PSID = $corepsid";

if [ ! -z "$psid" ]; then
echo "Killing Firefox = $psid";
kill $psid;
fi

if [ ! -z "$corepsid" ]; then
echo "Killing Core = $corepsid";
kill $corepsid;
fi

if [ ! -z "$tomboy" ]; then
echo "Killing tomboy = $tomboy";
kill $tomboy;
fi 

