#!/bin/bash
# Resizes and positions the application called APP with geometry x-percent,y-percent, width, height
# usage changeGeometry APP x y width height


xrand=`xrandr -q | grep Screen`
#echo "xrandLine = ${xrand}"
WIDTH=`echo ${xrand} | awk '{ print $8 }'`
HEIGHT=`echo ${xrand} | awk '{ print $10 }' |  awk -F"," '{ print $1 }'`

if [ "$WIDTH" == "" ]; then
echo "Default screen detection not working, assume NX connectivity"
xrand=`xrandr -q | grep '*'`
#echo "xrandLine = ${xrand}"
WIDTH=`echo ${xrand} | awk '{ print $2 }'`
HEIGHT=`echo ${xrand} | awk '{ print $4 }' |  awk -F"," '{ print $1 }'`
fi

echo "Width = ${WIDTH}"
echo "Height = ${HEIGHT}"


line=`wmctrl -l -G | grep $1`

#echo "line=$line"

machinename=`echo "$line" | awk '{print $7}'`

echo "Machine=$machinename"

tagchar="^"

taggedString=${line/$machinename/$tagchar}

#echo "Tagged line=$taggedString"

pos=`expr index "$taggedString" $tagchar`

len=1

#echo "Locate Position=$pos"
#echo "Length=$len"

splitpos=`echo "$pos $len" | awk '{printf("%i",$1+$2)}'` 

#echo "Position=$splitpos"

wmctrlName="${taggedString:$splitpos}"

echo "WMCTRL NAME=$wmctrlName"

x=`echo "$2 $WIDTH" | awk '{printf("%i",($2/100)*$1)}'` 
y=`echo "$3 $HEIGHT" | awk '{printf("%i",($2/100)*$1)}'` 
wd=`echo "$4 $WIDTH" | awk '{printf("%i",($2/100)*$1)}'` 
ht=`echo "$5 $HEIGHT" | awk '{printf("%i",($2/100)*$1)}'` 

# gravity, x, y, width, heigth

if [ -n "$wmctrlName" ]; then 	# -n tests to see if the argument is non empty
wmctrl -r "$wmctrlName" -e 1,$x,$y,$wd,$ht
fi




