GET_MANAGED_SITE_LIST () {
        MANAGED_SITES=`cat $MANAGER_CFG_DIR/managed_sites.list`
}

PREPARE_REQUIRED_FILES (){
        local PSSH_SITE_LIST=${MANAGER_CFG_DIR}/sites.list

        echo "Enter PREPARE_REQUIRED_FILES() $PSSH_SITE_LIST"

	MANAGED_SITES=`cat ${MANAGER_CFG_DIR}/managed_sites.list`
        for SITE in $MANAGED_SITES
        do
                MAKE_PSSH_SITE_LIST $SITE $PSSH_SITE_LIST

		local OPPOSITE_TUNNEL_ENDS=`cat $TUNNEL_LIST | sed "s/CAP[0-9][0-9]//g" | grep -w ^$SITE | awk '{print $2}'`
		echo "OPPOSITE_TUNNEL_ENDS $OPPOSITE_TUNNEL_ENDS"
		for OPPOSITE_END in $OPPOSITE_TUNNEL_ENDS
		do
			MAKE_PSSH_SITE_LIST $OPPOSITE_END $PSSH_SITE_LIST
		done
	done

        for BRIDGE in brcap br1 br2
        do
                GET_SITES_OFCTL_SHOW $PSSH_SITE_LIST $BRIDGE ${OFCTL_SHOW_DIR}
                GET_SITES_OFCTL_DUMP_FLOWS $PSSH_SITE_LIST $BRIDGE ${OFCTL_FLOWS_DIR}
        done
}

MANAGE_SITE_CONNECTIVITY () {
        local SITE_CTRL_IP=$1
        local SITE=$2

        check_site $SITE_CTRL_IP $SITE

        if [ $? == "1" ]
        then
                echo "Connectivity Recovery Procedure"
		return 1
        fi
	return 0
}

GET_SITE_CTRL_IP () {
        local SITE=$1
        cat $NETWORK_CFG_DIR/sites.list | grep ${SITE}CAP00 | grep CT | sed "s/=/ /g" |  awk '{print $2}'
}

GET_SITE_DATA_IP () {
        local SITE=$1
        cat $NETWORK_CFG_DIR/sites.list | grep ${SITE}CAP00 | grep DT | sed "s/=/ /g" | awk '{print $2}'
}

GET_SITE_NAME_FROM_IP (){
	local SITE_IP=$1
	cat ${NETWORK_CFG_DIR}/sites.list | grep $SITE_IP | sed "s/=/ /g" | sed "s/_/ /g" | sed "s/CAP[0-9][0-9]//g" | awk '{print $1}'
}

GET_BRIDGE_LIST () {
        local SITE_CTRL_IP=$1
        local SITE=$2
        show $SITE_CTRL_IP > $BRIDGE_LIST_DIR/${SITE}_br.list
}

GET_BR_DPID () {
        local SITE=$1
        local BRIDGE=$2

        if [ "${BRIDGE}" == "brcap" ]; then
                SW_CODE="CAP00"
        elif [ "${BRIDGE}" == "br1" ]; then
                SW_CODE="SW00"
        elif [ "${BRIDGE}" == "br2" ]; then
                SW_CODE="SW01"
        fi
        local DPID_NAME=${SITE}${SW_CODE}_DPID

        cat $NETWORK_CFG_DIR/DPIDs.list | grep $DPID_NAME | sed "s/\"//g" | sed "s/=/ /g" | awk '{print $2}'
}

GET_BR_CONTROLLER_IP () {
        local BRIDGE=$1

        if [ "$BRIDGE" == "br1" -o "$BRIDGE" == "br2" ]; then
                echo "103.22.221.52"
        elif [ "$BRIDGE" == "brcap" ]; then
                echo "103.22.221.151"
        fi
}

ADD_SITE_TO_LIST () {
        SITE=$1
        SITE_FILE=$2

        local CHECK=`cat $SITE_FILE | grep ^${SITE} | awk '{print $1}'`
        if [ "${CHECK:-null}" == null -o "${CHECK}" != "${SITE}" ]; then
                echo "CHECK $CHECK SITE $SITE"
                local SITE_IP=`GET_SITE_CTRL_IP $SITE`
                echo "$SITE $SITE_IP" >> $SITE_FILE
        fi
}

MAKE_PSSH_SITE_LIST () {
        SITE=$1
        SITE_FILE=$2

        local SITE_IP=`GET_SITE_CTRL_IP $SITE`

        local CHECK=`cat $SITE_FILE | grep $SITE_IP | sed "s/@/ /g" |  awk '{print $2}'`
        if [ "${CHECK:-null}" == null -o "${CHECK}" != "${SITE_IP}" ]; then
                echo "CHECK $CHECK SITE $SITE"
                echo "root@${SITE_IP}" >> $SITE_FILE
        fi
}

GET_SITE_OFCTL_SHOW () {
        local SITE_CTRL_IP=$1
        local BRIDGE=$2

        ssh root@$SITE_CTRL_IP ovs-ofctl show $BRIDGE > ${OFCTL_SHOW_DIR}/root@${SITE_CTRL_IP}_${BRIDGE}
}

GET_SITES_OFCTL_SHOW () {
        local SITES_FILE=$1
        local BRIDGE=$2
        local OUTPUT_DIR=$3

	echo "$SITES_FILE $BRIDGE $OUTPUT_DIR"
        pssh --hosts $SITES_FILE -o $OUTPUT_DIR ovs-ofctl show $BRIDGE
	sleep 3
	while read FILE_NAME
	do
		mv ${OUTPUT_DIR}/${FILE_NAME} ${OUTPUT_DIR}/${FILE_NAME}_${BRIDGE}
	done < $SITES_FILE
}

GET_SITE_OFCTL_DUMP_FLOWS (){
        local SITE_CTRL_IP=$1
        local BRIDGE=$2

        ssh root@$SITE_CTRL_IP ovs-ofctl dump-flows $BRIDGE > ${OFCTL_FLOW_DIR}/root@${SITE_CTRL_IP}_${BRIDGE}
}

GET_SITES_OFCTL_DUMP_FLOWS (){
        local SITES_FILE=$1
        local BRIDGE=$2
        local OUTPUT_DIR=$3

	echo "$SITES_FILE $BRIDGE $OUTPUT_DIR"
        pssh --hosts $SITES_FILE -o $OUTPUT_DIR ovs-ofctl dump-flows $BRIDGE

	sleep 3
	while read FILE_NAME
	do
		mv ${OUTPUT_DIR}/${FILE_NAME} ${OUTPUT_DIR}/${FILE_NAME}_${BRIDGE}
	done < $SITES_FILE
}

REMOVE_BR_AND_FLOW_FILES () {
	local BR_DIR=$1
	local FLOW_DIR=$2
	rm $BR_DIR/*
	rm $FLOW_DIR/*
}

ERROR_REPORT () {
	local ERROR_LOG=$1
	local ADMIN_MAIL_ADDRESS=$2

	echo "Enter ERROR_REPORT() $ERROR_LOG $ADMIN_MAIL_ADDRESS"
	if [ -e $ERROR_LOG ]; then
		local LOG_NAME=`echo $ERROR_LOG | sed "s/\// /g" | awk '{print $3}'`
		mail -a "From:Overlay_vNet_Manager" -s "$LOG_NAME" $ADMIN_MAIL_ADDRESS < $ERROR_LOG
	fi
}
