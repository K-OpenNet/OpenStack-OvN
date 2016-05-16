FIND_FLOW_NAME_BASED_INOUT () {
        local CONTROLLER=$1
        local DPID=$2
        local IN_PORT=$3
        local OUT_PORT=$4

	echo "Enter FIND_FLOW_NAME_BASED_INOUT $CONTROLLER $DPID $IN_PORT $OUT_PORT"

        local ALL_FLOWS=`curl -u admin:admin -H "Content-Type: application/json" -X GET http://$CONTROLLER:8080/controller/nb/v2/flowprogrammer/default`
        local NUM_FLOWS=`echo $ALL_FLOWS | python -m json.tool | jq '.flowConfig | length'`

        for (( i=0 ; i<$NUM_FLOWS; i++ ))
        do
                local CHECK_DPID=`echo $ALL_FLOWS | python -m json.tool | jq -r '.flowConfig | .[$i] | .node | .id'`
#		echo "CHECK_DPID: $CHECK_DPID DPID: $DPID"
                if [ "${CHECK_DPID}" != "$DPID" ]; then
                        continue
                fi

                local CHECK_IN_PORT=`echo $ALL_FLOWS | python -m json.tool | jq -r '.flowConfig | .[$i] | .actions[0]' | awk -F= '{print $2}'`
#		echo "CHECK_IN_PORT $CHECK_IN_PORT IN_PORT $IN_PORT"
                if [ $CHECK_IN_PORT -eq  $IN_PORT ]; then
                        continue
                fi

                local CHECK_OUT_PORT=`echo $ALL_FLOWS | python -m json.tool | jq -r '.flowConfig | .[$i]' | .ingressPort`
#		echo "CHECK_OUT_PORT $CHECK_OUT_PORT OUT_PORT $OUT_PORT"
                if [ $CHECK_OUT_PORT -ne $OUT_PORT ]; then
                        FLOW_NAME=`echo $ALL_FLOWS | python -m json.tool | jq -r '.flowConfig | .[$i] | .name'`
                        break
                fi
        done
#        echo $FLOW_NAME
}

DELETE_FORWARD_RULE () {
        local CONTROLLER=$1
        local FLOW_NAME=$2
	echo "Enter DELETE_FORWARD_RULE() $CONTROLLER $FLOW_NAME"
#	echo "Delete Flow $FLOW_NAME from Controller $CONTROLLER"
        curl -X DELETE -d '{"name":"$FLOW_NAME"}' http://$CONTROLLER:8080/vm/staticflowentrypusher/json
}

CREATE_FORWARD_RULE () {
        local CONTROLLER=$1
        local FLOW_NAME=$2
        local IN_PORT=$3
        local OUT_PORT=$4
        local DPID=$5
	echo "Enter CREATE_FORWARD_RULE() $CONTROLLER $FLOW_NAME $IN_PORT $OUT_PORT $DPID"
#	echo "Call a API on Controller $CONTROLLER to create Flow $FLOW_NAME which from $IN_PORT to $OUT_PORT on bridge $5"
        curl -u admin:admin -H 'Content-type: application/json' -X PUT -d '{"installInHw":"true", "name":"$FLOW_NAME", "node": {"id":"$DPID", "type":"OF"}, "ingressPort": "$IN_PORT", "priority":"65535","actions":["OUTPUT=$OUT_PORT"]}' http://$CONTROLLER:8080/controller/nb/v2/flowprogrammer/default/node/OF/$DPID/staticFlow/$FLOW_NAME
}

CHECK_AND_RECOVER_FLOWS_FOR_PATCH_PORTS () {
        local SITE_CTRL_IP=$1
        local SITE=$2
	local BRIDGE=$3
        local CONTROLLER=$4

	echo "Enter CHECK_AND_RECOVER_FLOWS_FOR_PATCH_PORTS() $SITE_CTRL_IP $SITE $BRIDGE $CONTROLLER"
        OFCTL_SHOW_FILE=${OFCTL_SHOW_DIR}/root@${SITE_CTRL_IP}_${BRIDGE}
        OFCTL_FLOWS_FILE=${OFCTL_FLOWS_DIR}/root@${SITE_CTRL_IP}_${BRIDGE}

        local i=0
        for (( i=0 ; i<${#BR_PATCH_FROM[@]}; i++ ))
        do
                local IN_PORT=`cat $OFCTL_SHOW_FILE | grep ${BR_PATCH_FROM[$i]} | sed "s/(/ /g" | sed "s/)/ /g" | awk '{print $1}'`
                local OUT_PORT=`cat $OFCTL_SHOW_FILE | grep ${BR_PATCH_FROM[$i]} | sed "s/(/ /g" |sed "s/)/ /g" | awk '{print $1}'`
                local WRONG_RULE=`cat $OFCTL_FLOWS_FILE | grep "in_port=$IN_PORT" | grep "output:" | sed "/output:$OUT_PORT/d"`
                local CORRECT_RULE=`cat $OFCTL_FLOWS_FILE | grep "in_port=$IN_PORT" | grep "output:$OUT_PORT"`
                if [ "${WRONG_RULE:-null}" != null ]; then
                        WRONG_OUT_PORT=`echo $WRONG_RULE | grep "output:$OUT_PORT" | sed "s/,/ /g" | awk '{print $9}' | awk -F: '{print $2}'`
                        local FLOW_NAME=`FIND_FLOW_NAME_BASED_INOUT $CONTROLLER $DPID $IN_PORT $WRONG_OUT_PORT`
                        DELETE_FORWARD_RULE $CONTROLLER $FLOW_NAME
                fi

                if [ "${CORRECT_RULE:-null}" == null ]; then
			local FLOW_NAME="flow_${BR_PATCH_FROM[$i]}"
                        CREATE_FORWARD_RULE $CONTROLLER $FLOW_NAME $IN_PORT $OUT_PORT
                fi
        done
}

CHECK_AND_RECOVER_FLOW (){
	local SITE_NAME=$1
	local BRIDGE=$2
	local PATCH_FROM_NAME=$3
	local PATCH_TO_NAME=$4

	local SITE_CTRL_IP=`GET_SITE_CTRL_IP $SITE_NAME`
	local OFCTL_SHOW_FILE=${OFCTL_SHOW_DIR}/root@${SITE_CTRL_IP}_${BRIDGE}
	local OFCTL_FLOWS_FILE=${OFCTL_FLOWS_DIR}/root@${SITE_CTRL_IP}_${BRIDGE}
	local CONTROLLER=`GET_BR_CONTROLLER_IP $BRIDGE`

	echo "Enter CHECK_AND_RECOVER_FLOW() $SITE_NAME $BRIDGE $PATCH_FROM_NAME $PATCH_TO_NAME"
	
	local IN_PORT=`cat $OFCTL_SHOW_FILE | grep $PATCH_FROM_NAME | sed "s/(/ /g" |sed "s/)/ /g" | awk '{print $1}'`
	local OUT_PORT=`cat $OFCTL_SHOW_FILE | grep $PATCH_TO_NAME |sed "s/(/ /g" |sed "s/)/ /g" | awk '{print $1}'`
	local WRONG_RULE=`cat $OFCTL_FLOWS_FILE | grep "in_port=$IN_PORT" | grep "output:" | sed "/output:$OUT_PORT/d"`
	local CORRECT_RULE=`cat $OFCTL_FLOWS_FILE | grep "in_port=$IN_PORT" | grep "output:$OUT_PORT"`
	echo "IN_PORT $IN_PORT OUT_PORT $OUT_PORT WRONG_RULE $WRONG_RULE CORRECT_RULE $CORRECT_RULE"
	 if [ "${WRONG_RULE:-null}" != null ]; then
		WRONG_OUT_PORT=`echo $WRONG_RULE | grep "output:$OUT_PORT" | sed "s/,/ /g" | awk '{print $9}' | awk -F: '{print $2}'`
                local FLOW_NAME=`FIND_FLOW_NAME_BASED_INOUT $CONTROLLER $DPID $IN_PORT $WRONG_OUT_PORT`
                DELETE_FORWARD_RULE $CONTROLLER $FLOW_NAME
         fi

         if [ "${CORRECT_RULE:-null}" == null ]; then
		local DPID=`GET_BR_DPID $SITE_NAME $BRIDGE`
		if [ $BRIDGE == "brcap" ]; then
			FLOW_NAME="flow_$PATCH_TO_NAME"
		else
                	FLOW_NAME="flow_$PATCH_FROM_NAME"
		fi
                CREATE_FORWARD_RULE $CONTROLLER $FLOW_NAME $IN_PORT $OUT_PORT
         fi
}

MANAGE_FLOWS_FOR_PATCH_PORTS () {
	local SITE_NAME=$1
	local VSCTL_SHOW_FILE=$2

	echo "Enter MANAGED_FLOWS_FOR_PATCH_PORTS() $SITE_NAME $VSCTL_SHOW_FILE"

	local BRIDGE_LOC=`cat -n $VSCTL_SHOW_FILE | grep Bridge | awk '{print $1}'`
	for BRIDGE_START_LINE in $BRIDGE_LOC
	do
		local BRIDGE_NAME=`cat $VSCTL_SHOW_FILE | sed -n ${BRIDGE_START_LINE}p | grep Bridge |sed "s/\"//g" | awk '{print $2}'`
		local CHECK=`echo $BRIDGE_NAME | grep xen`

		if [ "${CHECK:-null}" != null ]; then
			continue
		fi

		local CONTROLLER=`GET_BR_CONTROLLER_IP $BRIDGE`
		MANAGE_SITE_CONNECTIVITY $CONTROLLER "CONTROLLER"
		if [ $? == "1" ]; then
			echo "Controller is down"
		#	continue;
		fi

		FIND_BRIDGE_PART_FROM_LIST $BRIDGE_NAME $VSCTL_SHOW_FILE
		local PORTS_LOC=`cat -n $VSCTL_SHOW_FILE | sed -n ${BRIDGE_START_LINE},${LINE_CNT}p | grep "type: patch" -B 2 -A 1 | grep Port | awk '{print $1}'`

		for PORT_LOC in $PORTS_LOC
		do
			echo "PORT_LOC ${PORT_LOC}"
			PORT_FROM_NAME=`cat $VSCTL_SHOW_FILE | sed -n ${PORT_LOC}p | sed "s/\"//g" | awk '{print $2}'`
			
#			PORT_TO_NAME=`cat $VSCTL_SHOW_FILE | sed -n ${PORT_LOC},+3p | grep peer | sed "s/\"/ /g" | sed "s/\}//g" | awk '{print $3}'`

			echo "PORT_FROM_NAME $PORT_FROM_NAME PORT_TO_NAME $PORT_TO_NAME"
			CHECK_AND_RECOVER_FLOW $SITE_NAME $BRIDGE_NAME $PORT_FROM_NAME $PORT_TO_NAME
		done
	done
}

MANAGE_FLOWS_FOR_TUNNELS () {
	local SITE_NAME=$1
	local VSCTL_SHOW_FILE=$2

	echo "Enter MANAGE_FLOWS_FOR_TUNNELS() $SITE_NAME $VSCTL_SHOW_FILE"

	local TUNNELS=`cat $VSCTL_SHOW_FILE | grep "type: gre" -A 1 -B 2 | grep Port | sed "s/\"//g" | awk '{print $2}'`
	
	for TUNNEL in $TUNNELS
	do
		local CHECK=`cat $TUNNEL_LIST | grep $TUNNEL`
		if [ "${CHECK:-null}" != null ]
		then
			local SRC_SITE=`echo $CHECK | awk '{print $1}' | sed "s/CAP[0-9][0-9]//g"`
			local DEST_SITE=`echo $CHECK | awk '{print $2}' | sed "s/CAP[0-9][0-9]//g"`
			local SRC_CTRL_IP=`GET_SITE_CTRL_IP $SRC_SITE`
			local SRC_DATA_IP=`GET_SITE_DATA_IP $SRC_SITE`
			local DEST_CTRL_IP=`GET_SITE_CTRL_IP $DEST_SITE`
			local DEST_DATA_IP=`GET_SITE_DATA_IP $DEST_SITE`
			local KEY1=`GET_NEW_TUNNEL_KEY $SRC_CTRL_IP $DEST_DATA_IP`
			local KEY2=`GET_NEW_TUNNEL_KEY $DEST_CTRL_IP $SRC_DATA_IP`
			local SRC_TO_DEST_TUNNEL="ovs_gre_"${SRC_SITE}${DEST_SITE}
			local DEST_TO_SRC_TUNNEL="ovs_gre_"${DEST_SITE}${SRC_SIT}

			CHECK_AND_RECOVER_FLOW $SRC_SITE brcap "C_${DEST_SITE}" ${SRC_TO_DEST_TUNNEL}
			CHECK_AND_RECOVER_FLOW $DEST_SITE brcap "C_${SRC_SITE}" ${DEST_TO_SRC_TUNNEL}
		fi
	done
}

MANAGE_FLOWS () {
	local PSSH_SITE_LIST=${MANAGER_CFG_DIR}/sites.list
	local MANAGED_SITES=${MANAGER_CFG_DIR}/managed_sites.list

	echo "Enter MANAGE_FLOWS() $MANAGED_SITES"
	while read TARGET
	do
		local SITE_NAME=$TARGET
		local SITE_IP=`GET_SITE_CTRL_IP $SITE_NAME`
		local VSCTL_SHOW_FILE=${BRIDGE_LIST_DIR}/${SITE_NAME}_br.list
	
		echo "SITE_IP $SITE_IP SITE_NAME $SITE_NAME VSCTL_SHOW_FILE $VSCTL_SHOW_FILE"	
		MANAGE_FLOWS_FOR_PATCH_PORTS $SITE_NAME $VSCTL_SHOW_FILE
	done < $MANAGED_SITES

	while read TARGET
	do
		local SITE_NAME=$TARGET
		local SITE_IP=`GET_SITE_CTRL_IP $SITE_NAME`
		local VSCTL_SHOW_FILE=${BRIDGE_LIST_DIR}/${SITE_NAME}_br.list

		MANAGE_FLOWS_FOR_TUNNELS $SITE_NAME $VSCTL_SHOW_FILE
		
	done < $MANAGED_SITES
}
