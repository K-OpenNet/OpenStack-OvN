import subprocess
import shlex

ovstout="5"

def ovs_vsctl_show (remoteip, remotept):
    cmdstr=create_ovsdb_command(remoteip, remotept, "show")
    (returncode, cmdout, cmderr)=execute_bash_command(cmdstr)
    return cmdout

#
#    Bridge Management Functions
#

def ovs_vsctl_add_br (remoteip, remotept, brname):
    cmdstr="add-br "+brname
    cmdstr=create_ovsdb_command(remoteip, remotept, cmdstr)
    (returncode, cmdout, cmderr)=execute_bash_command(cmdstr)

    if returncode == 0:
        print "Bridge "+brname+" was created in Host "+remoteip
    else:
        print cmderr

def ovs_vsctl_del_br (remoteip, remotept, brname):
    cmdstr="del-br "+brname
    cmdstr=create_ovsdb_command(remoteip, remotept, cmdstr)
    (returncode, cmdout, cmderr)=execute_bash_command(cmdstr)

    if returncode == 0:
        print "Bridge "+brname+" was deleted in Host "+remoteip
    else:
        print cmderr

def ovs_vsctl_set_dpid (remoteip, remotept, brname, dpid):
    cmdstr="set bridge "+brname+" other-config:datapath-id="+dpid
    cmdstr=create_ovsdb_command(remoteip, remotept, cmdstr)
    (returncode, cmdout, cmderr)=execute_bash_command(cmdstr)

def ovs_vsctl_set_controller (remoteip, remotept, brname, controllerip):
    cmdstr="set-controller "+brname+" "+controllerip
    cmdstr = create_ovsdb_command(remoteip,remotept,cmdstr)
    (returncode, cmdout, cmderr)=execute_bash_command(cmdstr)

def ovs_vsctl_del_controller (remoteip, remotept, brname):
    cmdstr="del-controller "+brname
    cmdstr = create_ovsdb_command(remoteip, remotept, cmdstr)
    (returncode, cmdout, cmderr) = execute_bash_command(cmdstr)

#
#    Port Management Functions
#
def ovs_vsctl_add_port (remoteip, remotept, brname, ptname):
    cmdstr="add-port "+brname+" "+ptname
    cmdstr=create_ovsdb_command(remoteip, remotept, cmdstr)
    (returncode, cmdout, cmderr)=execute_bash_command(cmdstr)

    if returncode == 0:
        print "Port "+ptname+" was created on Bridge "+brname+" in Host "+remoteip
    else:
        print cmderr

def ovs_vsctl_del_port (remoteip, remotept, brname, ptname):
    cmdstr="del-remotept "+brname+" "+ptname
    cmdstr=create_ovsdb_command(remoteip, remotept, cmdstr)
    (returncode, cmdout, cmderr)=execute_bash_command(cmdstr)

    if returncode==0:
        print "Port "+ptname+" was deleted on Bridge "+brname+" in Host "+remoteip
    else:
        print cmderr

def ovs_vsctl_add_patch_port(remoteip, remotept, brname, ptname, peerptname=None):

    ovs_vsctl_add_port(remoteip, remotept, brname, ptname)

    if peerptname:
        cmdstr="set interface "+ptname+" type=patch "+ "options:peer="+peerptname
        cmdstr=create_ovsdb_command(remoteip, remotept, cmdstr)
    else:
        cmdstr="set interface "+ptname+" type=patch"
        cmdstr=create_ovsdb_command(remoteip, remotept, cmdstr)

    (returncode, cmdout, cmderr)=execute_bash_command(cmdstr)

def ovs_vsctl_add_nvgre_port(remoteip, remotept, brname, ptname, peerip, key):
    ovs_vsctl_add_port (remoteip, remotept, brname, ptname)
    cmdstr = "set interface "+ptname+" type=gre options:remote_ip="+peerip+" options:key="+key
    cmdstr=create_ovsdb_command(remoteip, remotept, cmdstr)
    (returncode, cmdout, cmderr)=execute_bash_command(cmdstr)

def ovs_vsctl_add_vxlan_port(remoteip, remotept, brname, ptname, peerip, key):
    ovs_vsctl_add_port (remoteip, remotept, brname, ptname)
    cmdstr = "type=vxlan options:df_default=true options:in_key=flow options:local_ip="+remoteip+" options:out_key=flow options:remote_ip="+peerip
    ovs_vsctl_set_interface(remoteip, remotept, ptname, cmdstr)


def ovs_vsctl_set_interface(remoteip, remotept, tgtname, opts):
    cmdstr = "set interface "+tgtname+" "+opts
    cmdstr = create_ovsdb_command(remoteip, remotept, cmdstr)
    (returncode, cmdout, cmderr)=execute_bash_command(cmdstr)
#
#   Basic Utility Functions for OVSDB Communications
#
def create_ovsdb_command(remoteip, remotept, cmd):
    cmdstr="sudo ovs-vsctl "+"--timeout="+ovstout+" --db=tcp:"+remoteip+":"+remotept+" "+cmd
    return cmdstr

def execute_bash_command(cmdstr):
    subproc=subprocess.Popen(shlex.split(cmdstr), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (cmdout, cmderr)=subproc.communicate()
    return subproc.returncode, cmdout, cmderr

#
#    Test Code for each functions
#    Below codes are only executed when you execute this module directly
#

if __name__ == '__main__':
    ovs_vsctl_show("10.0.200.8", "4456")
    ovs_vsctl_add_br("10.0.200.8", "4455", "testbr")
    ovs_vsctl_add_port("10.0.200.8", "4455", "testbr", "testremotept")
