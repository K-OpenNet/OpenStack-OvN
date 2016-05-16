source ../script/functions.sh

source ./ovn_util_functions.sh
source ./ovn_tunnel_functions.sh
source ./ovn_flow_functions.sh
source ./ovn_bridge_functions.sh

NETWORK_CFG_DIR="./Define"
TUNNEL_LIST="./Define/tunnel.list"
MANAGER_CFG_DIR="./config"
BRIDGE_LIST_DIR=${MANAGER_CFG_DIR}/br_lists
BRIDGE_CFG_DIR=${MANAGER_CFG_DIR}/br_configs
OFCTL_SHOW_DIR=${MANAGER_CFG_DIR}/of_show
OFCTL_FLOWS_DIR=${MANAGER_CFG_DIR}/of_flows
ERROR_LOG_DIR=./log_dir
