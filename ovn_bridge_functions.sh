PARSING_BRIDGE_INFO_FROM_CFG () {
        lines=$1
        local PORTS_CNT=0
        local PATCH_FROM_CNT=0
        local PATCH_TO_CNT=0

	echo "Enter PARSING_BRIDGE_INFO_FROM_CFG()"
        for line in ${lines[*]}
        do
                TAG=`echo $line | sed "s/</ /g" | sed "s/>/ /g" | awk '{print $1}'`
#                echo $TAG
                if [ $TAG == "NAME" ]
                then
                        CFG_BR_NAME=`echo $line | sed "s/</ /g" | sed "s/>/ /g" | awk '{print $2}'`
                        continue;

		elif [ $TAG == "CONTROLLER" ]
		then
			CONTROLLER=`echo $line | sed "s/</ /g" | sed "s/>/ /g" | awk '{print $2}'`
			continue;

                elif [ $TAG == "DPID" ]
                then
                        CFG_BR_DPID=`echo $line | sed "s/</ /g" | sed "s/>/ /g" | awk '{print $2}'`
                        continue;

                elif [ $TAG == "PORT" ]
                then
                        CFG_BR_PORTS[$((PORTS_CNT++))]=`echo $line | sed "s/</ /g" | sed "s/>/ /g" | awk '{print $2}'`

                elif [ $TAG == "PATCH_PORT" ]
                then
                        PREV_TAG="PATCH_PORT"

                elif [ $TAG == "FROM" ]
                then
                        if [ $PREV_TAG != "PATCH_PORT" ]; then
                                echo "Format is not valid"
                                exit
                        fi

                        CFG_BR_PATCH_FROM[$((PATCH_FROM_CNT++))]=`echo $line | sed "s/</ /g" | sed "s/>/ /g" | awk '{print $2}'`

                elif [ $TAG == "TO" ]
                then
                        if [ $PREV_TAG != "PATCH_PORT" ]; then
                                echo "Format is not valid"
                                exit
                        fi
                        CFG_BR_PATCH_TO[$((PATCH_TO_CNT++))]=`echo $line | sed "s/</ /g" | sed "s/>/ /g" | awk '{print $2}'`

                elif [ $TAG == "/PATCH_PORT" ]
                then
                        unset PREV_TAG

                elif [ $TAG == "CFG_SECURE_MODE" ]
                then
                        CFG_SECURE_MODE=1

                elif [ $TAG == "/BRIDGE" ]
                then
                       break
                else
                        continue
                fi
        done
}

FIND_BRIDGE_PART_FROM_LIST () {
        local CFG_BR_NAME=$1
        local SITE_BR_LIST_FILE=$2

	echo "Enter FIND_BRIDGE_PART_FROM_LIST() / $CFG_BR_NAME / $SITE_BR_LIST_FILE"

	BRIDGE_START_LINE=`cat -n $SITE_BR_LIST_FILE | grep Bridge | sed "s/\"//g" | awk -v CFG_BR_NAME=$CFG_BR_NAME '{ if ($3 == CFG_BR_NAME) print $1}'`

	local TEMP=`cat -n $SITE_BR_LIST_FILE | grep Bridge | sed "s/\"//g" | awk -v LOC=$BRIDGE_START_LINE '{ if ($1 > LOC) print $1}'`
        local BRIDGE_END_LINE=`echo $TEMP | awk '{print $1}'`

	if [ -z $BRIDGE_END_LINE ]; then
		BRIDGE_END_LINE=`wc -l $SITE_BR_LIST_FILE | awk '{print $1}'`
	else
		BRIDGE_END_LINE=$((BRIDGE_END_LINE-1))
	fi
        LINE_CNT=$((BRIDGE_END_LINE-BRIDGE_START_LINE))
}

CHECK_AND_RECOVER_BRIDGE () {
        local SITE_CTRL_IP=$1
        local SITE=$2
        local SITE_BR_LIST_FILE=$3

	echo "Enter CHECK_AND_RECOVER_BRIDGE() / $SITE_CTRL_IP / $SITE / $SITE_BR_LIST_FILE"
#	echo "BRIDGE_START_LINE $BRIDGE_START_LINE LINE_CNT $LINE_CNT"
        CHECK=`cat $SITE_BR_LIST_FILE | grep $CFG_BR_NAME`
        if [ "${CHECK:-null}" == null ]; then
                echo "Bridge $CFG_BR_NAME doesn't exist" >> $ERROR_LOG
                add_br $SITE_CTRL_IP $CFG_BR_NAME
        fi


	if [ "${CONTROLLER:-null}" != null ]; then
		CHECK=`cat $SITE_BR_LIST_FILE | sed -n ${BRIDGE_START_LINE},+${LINE_CNT}p | grep Controller | sed "s/\"//g" | sed "s/:/ /g" | awk '{print $3}'`
#		echo "CHECK == $CHECK"
		if [ "${CHECK:-null}" == null -o "${CHECK}" != "${CONTROLLER}" ]; then
			echo "Bridge $CFG_BR_NAME wasn't connected to Controller $CONTROLLER" >> $ERROR_LOG
			set_controller $SITE_CTRL_IP $CFG_BR_NAME $CONTROLLER
		fi
	fi


        if [ "${DPID:-null}" != null ]; then
                DPID=$(echo $DPID | sed "s/[^a-z|0-9]//g;")
                CHECK=`get_dpid $SITE_CTRL_IP $CFG_BR_NAME`
                if [ "${CHECK}" == "${DPID}" ]; then
                        echo "DPID on Bridge $CFG_BR_NAME is not correct" >> $ERROR_LOG
                        set_dpid $SITE_CTRL_IP $CFG_BR_NAME $DPID
                fi
        fi


        if [ "${CFG_BR_PORTS:-null}" != null ]; then
                for i in ${CFG_BR_PORTS[*]}; do
                        CHECK=`cat $SITE_BR_LIST_FILE | sed -n ${BRIDGE_START_LINE},+${LINE_CNT}p | grep $i`
                        if [ "${CHECK:-null}" == null ]; then
                                echo "Port $i on Bridge $CFG_BR_NAME doesn't exist" >> $ERROR_LOG
                                add_port $SITE_CTRL_IP $CFG_BR_NAME $i
                        fi
                done
        fi


        if [ "${CFG_BR_PATCH_FROM:-null}" != null ]; then
                for (( i=0 ; i<${#CFG_BR_PATCH_FROM[@]}; i++ ));do
                        PATCH_FROM=${CFG_BR_PATCH_FROM[i]}
                        PATCH_TO=${CFG_BR_PATCH_TO[i]}
                        CHECK1=`cat $SITE_BR_LIST_FILE | sed -n ${BRIDGE_START_LINE},+${LINE_CNT}p | grep -n "Port" |  grep ${PATCH_FROM}  | sed "s/\"//g" | awk -F: '{print $1}'`
                        CHECK2=`cat $SITE_BR_LIST_FILE | sed -n ${BRIDGE_START_LINE},+${LINE_CNT}p |  sed -n $CHECK1,+4p | sed "s/\"//g" |  grep peer | grep ${PATCH_TO}`
#			echo "PATCH_FROM $PATCH_FROM PATCH_TO $PATCH_TO"
                        if [ "${CHECK1:-null}" == null -o "${CHECK2:-null}" == null ]; then
				if [ "${CHECK2:-null}" == null ]; then
					echo "Wrong Patch Port $PATCH_FROM was created. It will be deleted" >> $ERROR_LOG
					del_port $SITE_CTRL_IP $CFG_BR_NAME $PATCH_FROM
				fi

                                echo "Patch Port between $PATCH_FROM and $PATCH_TO has not been made" >> $ERROR_LOG
                                add_patch_port $SITE_CTRL_IP $CFG_BR_NAME $PATCH_FROM $PATCH_TO
                        fi
                done
        fi

        if [ $((CFG_SECURE_MODE)) == 1 ]; then
                CHECK=`cat $SITE_BR_LIST_FILE | sed -n ${BRIDGE_START_LINE},+${LINE_CNT}p | grep 'fail_mode: secure'`
                if [ "${CHECK:-null}" == null ]; then
                        echo "Set secure mode on $CFG_BR_NAME at site $SITE_CTRL_IP" >> $ERROR_LOG
                       set_secure $SITE_CTRL_IP $CFG_BR_NAME
                fi
        fi
}


INITIALIZE_BRIDGE_PARAMETERS () {
        unset CFG_BR_NAME
	unset CONTROLLER
        unset CFG_BR_DPID
        unset CFG_SECURE_MODE
        unset CFG_BR_PORTS
        unset CFG_BR_PATCH_FROM
        unset CFG_BR_PATCH_TO
	unset BRIDGE_START_LINE LINE_CNT
}

MANAGE_SITE_BRIDGE () {
	SITE_CTRL_IP=$1
	SITE=$2
        local SITE_BR_CFG_FILE=${BRIDGE_CFG_DIR}/${SITE}_br.cfg
	local SITE_BR_LIST_FILE=${BRIDGE_LIST_DIR}/${SITE}_br.list

	echo "Enter MANAGE_SITE_BRIDGE() / $SITE_CTRL_IP $SITE"
	show $SITE_CTRL_IP > $SITE_BR_LIST_FILE

        while read line
        do
                local TEMP=`echo $line`
                if [ "${TEMP:-null}" == null ]; then
                        continue
                fi

                lines[$((i++))]=$line

#                echo $line
                if [ $line == "</BRIDGE>" ]
                then
                        PARSING_BRIDGE_INFO_FROM_CFG $lines
                        echo "NAME $CFG_BR_NAME DPID $CFG_BR_DPID PORT $CFG_BR_PORTS CFG_BR_PATCH_FROM $CFG_BR_PATCH_FROM SECURE $CFG_SECURE_MODE"
			FIND_BRIDGE_PART_FROM_LIST $CFG_BR_NAME "${BRIDGE_LIST_DIR}/${SITE}_br.list"
                        CHECK_AND_RECOVER_BRIDGE $SITE_CTRL_IP $SITE ${BRIDGE_LIST_DIR}/${SITE}_br.list
                        INITIALIZE_BRIDGE_PARAMETERS
                        unset lines
                        i=0
                fi
        done < $SITE_BR_CFG_FILE
}
