import subprocess
import shlex

__author__ = 'jun'


class PingChecker:
    @staticmethod
    def is_pingable(from_ip, to_ip, user_acc):
        ping_str="ping "+to_ip
        tgt=user_acc+"@"+from_ip
        cmdstr=PingChecker.create_ssh_command(ping_str, tgt)
        (returncode, cmdout, cmderr)= PingChecker.execute_bash_command(cmdstr)

        if returncode == 0:
            return True
        else:
            return False

    @staticmethod
    def is_pingable_tunnel(box_ip, from_br, to_ip, user_acc):
        ping_str="ping -I "+from_br+" "+to_ip
        tgt = ""+user_acc+"@"+box_ip
        cmdstr = PingChecker.create_ssh_command(ping_str, tgt)
        (returncode, cmdout, cmderr)= PingChecker.execute_bash_command(cmdstr)

        if returncode == 0:
            return True
        else:
            return False

    @staticmethod
    def create_ssh_command(cmd, tgt):
        cmdstr='ssh '+cmd+' '+tgt
        return cmdstr

    @staticmethod
    def execute_bash_command(cmdstr):
        subproc=subprocess.Popen(shlex.split(cmdstr), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (cmdout, cmderr)=subproc.communicate()
        return subproc.returncode, cmdout, cmderr