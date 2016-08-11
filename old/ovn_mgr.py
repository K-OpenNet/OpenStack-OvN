import bridge_mgr, tunnel_mgr, flow_mgr
import os
import time

__author__ = 'jun'

tgt_box_list = []


def prepare_ovn_manager():
    global tgt_box_list
    tgt_box_list = []

    filepath = os.path.abspath(os.getcwd()) + "box_list"
    f = open(filepath, 'r')
    for tgt_box in f.readline():
        tgt_box_list.append(tgt_box)

    return


def do_work():
    bridgemanager = bridge_mgr.BridgeManager()
    tunnelmanager = tunnel_mgr.TunnelManager()
    flowmanager = flow_mgr.FlowManager()

    while True:
        prepare_ovn_manager()

        bridgemanager.do_work(tgt_box_list)
        tunnelmanager.do_work(tgt_box_list)
        flowmanager.do_work(tgt_box_list)

        time.sleep(30)


if __file__ == "__main__":
    prepare_ovn_manager()
