CHECK_TUNNEL () {
        local SRC_NAME=$1
        local DEST_NAME=$2
        local TUNNEL_NAME=$3

        local SRC_CTRL_IP=`GET_SITE_CTRL_IP $SRC_NAME`
        local SRC_DATA_IP=`GET_SITE_DATA_IP $SRC_NAME`
        local DEST_CTRL_IP=`GET_SITE_CTRL_IP $DEST_NAME`
        local DEST_DATA_IP=`GET_SITE_DATA_IP $DEST_NAME`

        GET_BRIDGE_LIST $SRC_IP $SRC_NAME

}

GET_NEW_TUNNEL_KEY() {
	local SRC_CTRL_IP=$1
	local DEST_DATA_IP=$2

        local key=$(ovs-vsctl --timeout=$OVSTIMEOUT --db=tcp:$SRC_CTRL_IP:$PPORT  show|grep $DEST_DATA_IP|awk '{print $2}'|sed "s/[^0-9]//g;"|sort -n|tail -n 1)
	if [ "${key:-null}" == null ];then
		key=1
	else
		key=$((key+1))
	fi
	echo $key
}

MAKE_TUNNEL () {
        SRC_NAME=$1
        DEST_NAME=$2
        SRC_CTRL_IP=$3
        DEST_DATA_IP=$4
	
	echo "Enter MAKE_TUNNEL() $SRC_NAME $DEST_NAME $SRC_CTRL_IP $DEST_DATA_IP"

        if [ "$SRC_NAME" == "GJ" ]; then
                p_num=$(awk -f ../return_Pnum.awk $TUNNEL_LIST|awk '{print $1}')
        elif [ "$SRC_NAME" == "GJ2" ]; then
                p_num=$(awk -f ../return_Pnum.awk $TUNNEL_LIST|awk '{print $2}')
        elif [ "$SRC_NAME" == "PH" ]; then
                p_num=$(awk -f ../return_Pnum.awk $TUNNEL_LIST|awk '{print $3}')
        elif [ "$SRC_NAME" == "MY" ]; then
                p_num=$(awk -f ../return_Pnum.awk $TUNNEL_LIST|awk '{print $4}')
        elif [ "$SRC_NAME" == "TH" ]; then
                p_num=$(awk -f ../return_Pnum.awk $TUNNEL_LIST|awk '{print $6}')
        elif [ "$SRC_NAME" == "ID" ]; then
                p_num=$(awk -f ../return_Pnum.awk $TUNNEL_LIST|awk '{print $5}')
        elif [ "$SRC_NAME" == "VT" ]; then
                p_num=$(awk -f ../return_Pnum.awk $TUNNEL_LIST|awk '{print $7}')
        elif [ "$SRC_NAME" == "MY2" ]; then
                p_num=$(awk -f ../return_Pnum.awk $TUNNEL_LIST|awk '{print $8}')
        elif [ "$SRC_NAME" == "GIST" ]; then
                p_num=$(awk -f ../return_Pnum.awk $TUNNEL_LIST|awk '{print $9}')
        elif [ "$SRC_NAME" == "PK" ]; then
                p_num=$(awk -f ../return_Pnum.awk $TUNNEL_LIST|awk '{print $10}')
        fi

	key=`GET_NEW_TUNNEL_KEY $SRC_CTRL_IP $DEST_DATA_IP`       
	echo "Key Value=$key"
        echo "make a tunnel $1-$2,p#: $p_num"
        add_nvgre3 $SRC_CTRL_IP brcap ovs_gre_${SRC_NAME}${DEST_NAME}${key} $DEST_DATA_IP ${SRC_NAME}CAP00 ${DEST_NAME}CAP00 $p_num
}

CHECK_AND_RECOVER_TUNNEL () {
        local END1_NAME=$1
        local END2_NAME=$2


        local END1_CTRL_IP=`GET_SITE_CTRL_IP $END1_NAME`
        local END2_CTRL_IP=`GET_SITE_CTRL_IP $END2_NAME`
        local END1_DATA_IP=`GET_SITE_DATA_IP $END1_NAME`
        local END2_DATA_IP=`GET_SITE_DATA_IP $END2_NAME`

	echo "Enter CHECK_AND_RECOVER_TUNNEL() $END1_NAME $END2_NAME"

	MANAGE_SITE_CONNECTIVITY $END1_CTRL_IP $END1_NAME
	if [ $? == "1" ]; then
		echo "Site $END1_NAME is not reachable" >> $ERROR_LOG
		return 1
	fi
	MANAGE_SITE_CONNECTIVITY $END2_CTRL_IP $END2_NAME
	if [ $? == "1" ]; then
		echo "Site $END2_NAME is not reachable" >> $ERROR_LOG
		return 1
	fi

        local TUNNEL_1_TO_2_NAME=`cat $TUNNEL_LIST | grep ^${END1_NAME}CAP | grep ${END2_NAME}CAP | awk '{print $5}'`
        local TUNNEL_2_TO_1_NAME=`cat $TUNNEL_LIST | grep ^${END2_NAME}CAP | grep ${END1_NAME}CAP | awk '{print $5}'`

#        echo "END1_CTRL_IP $END1_CTRL_IP END2_CTRL_IP $END2_CTRL_IP END1_DATA_IP $END1_DATA_IP END2_DATA_IP $END2_DATA_IP"

        GET_BRIDGE_LIST $END1_CTRL_IP $END1_NAME

        local CHECK1=`cat ${BRIDGE_LIST_DIR}/${END1_NAME}_br.list | grep -n $TUNNEL_1_TO_2_NAME | grep Port | awk -F: '{print $1}'`
        local CHECK2=`cat ${BRIDGE_LIST_DIR}/${END1_NAME}_br.list | sed -n ${CHECK1},+3p | grep $END2_DATA_IP`

        if [ "${CHECK1:-null}" == null -o "${CHECK2:-null}" == null ]; then
		echo "Tunnel $TUNNEL_1_TO_2_NAME on SITE $END1_NAME was not existed" >> $ERROR_LOG
                echo "Tunnel $TUNNEL_1_TO_2_NAME will be created" >> $ERROR_LOG
               del_tunnel $END1_CTRL_IP $TUNNEL_1_TO_2_NAME
               MAKE_TUNNEL $END1_NAME $END2_NAME $END1_CTRL_IP $END2_DATA_IP
        fi


        GET_BRIDGE_LIST $END2_CTRL_IP $END2_NAME

        local CHECK3=`cat ${BRIDGE_LIST_DIR}/${END2_NAME}_br.list | grep -n $TUNNEL_2_TO_1_NAME | grep Port | awk -F: '{print $1}'`
        local CHECK4=`cat ${BRIDGE_LIST_DIR}/${END2_NAME}_br.list | sed -n ${CHECK3},+4p | grep $END1_DATA_IP`

#       echo "CHECK3 $CHECK3 CHECK4 $CHECK4"

	echo "CHECK1 $CHECK1 CHECK2 $CHECK2 CHECK3 $CHECK3 CHECK4 $CHECK4"
        if [ "${CHECK3:-null}" == null -o "${CHECK4:-null}" == null ]; then
		echo "Tunnel $TUNNEL_2_TO_1_NAME on SITE $END2_NAME was not existed" >> $ERROR_LOG
                echo "Tunnel $TUNNEL_2_TO_1_NAME will be created" >> $ERROR_LOG
               del_tunnel $END2_CTRL_IP $TUNNEL_2_TO_1_NAME
               MAKE_TUNNEL $END2_NAME $END1_NAME $END2_CTRL_IP $END1_DATA_IP
        fi
}

MANAGE_TUNNEL_STATUS () {
        local PSSH_SITE_LIST=${MANAGER_CFG_DIR}/sites.list

	echo "Enter MANAGE_TUNNEL_STATUS()"

        while read TUNNEL
        do
                local SRC_NAME=`echo $TUNNEL | awk '{print $1}' | sed "s/CAP[0-9][0-9]//g"`
                local DEST_NAME=`echo $TUNNEL | awk '{print $2}' | sed "s/CAP[0-9][0-9]//g"`

                local CHECK1=`cat $MANAGER_CFG_DIR/managed_sites.list | grep $SRC_NAME`
                #local CHECK2=`cat $MANAGER_CFG_DIR/managed_sites.list | grep $DEST_NAME`
#                echo "CHECK1 $CHECK1 CHECK2 $CHECK2"
                if [ "${CHECK1:-null}" == null -o "${DEST_NAME:-null}" == null ];  then
                       continue
                fi

               	echo "SRC_NAME $SRC_NAME DEST_NAME $DEST_NAME Tunnel $TUNNEL"

                CHECK_AND_RECOVER_TUNNEL $SRC_NAME $DEST_NAME
                #CHECK_AND_RECOVER_TUNNEL $DEST_NAME $SRC_NAME

#                MAKE_PSSH_SITE_LIST $SRC_NAME $PSSH_SITE_LIST
#                MAKE_PSSH_SITE_LIST $DEST_NAME $PSSH_SITE_LIST

        done < $TUNNEL_LIST

        #GET_SITES_OFCTL_SHOW $PSSH_SITE_LIST brcap ${OFCTL_SHOW_DIR}
        #GET_SITES_OFCTL_DUMP_FLOWS $PSSH_SITE_LIST brcap ${OFCTL_FLOWS_DIR}
	#CHECK_AND_RECOVER_FLOWS_FOR_TUNNEL
	#REMOVE_BR_AND_FLOW_FILES ${OFCTL_SHOW_DIR} ${OFCTL_FLOWS_DIR}
}
