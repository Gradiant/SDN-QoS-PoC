#!/bin/bash
if [ "$#" -ne 3 ]; then
    echo "Illegal number of parameters"
    echo "usage set_priority.sh IP_SRC IP_DST [hi|lo]"
    exit 1
fi

flow="table=0,ip,ip_src=$1,ip_dst=$2"

if [ "$3" == "hi" ]; then
    echo "sudo ovs-ofctl -OOpenFlow13 add-flow core2 priority=10,idle_timeout=60,$flow,actions=set_queue:1,output:2"
    sudo ovs-ofctl -OOpenFlow13 add-flow core2 priority=10,idle_timeout=60,$flow,actions=set_queue:1,output:2
elif [ "$3" == "lo" ]; then
    echo "sudo ovs-ofctl -OOpenFlow13 del-flows core2 $flow"
    sudo ovs-ofctl -OOpenFlow13 del-flows core2 $flow

fi