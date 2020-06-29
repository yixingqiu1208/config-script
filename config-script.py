# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# Config Script:
#  step 1 - connect to router and run "show run"
#  step 2 - (Mode 1) open file with full config; (Mode 2) open file or/and manual input with added changes
#  step 3 - (Mode 1) send (scp) full config to router; (Mode 2) send config from "show run" + added changes
#  step 4 - load config that was sent
#  step 5 - commit replace
#  step 6 - run "show run" after changes
#  step 7 - display diff on console
#
# Revision 1.0 2020/06/23 yixqiu@cisco.com
#
# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

import os
import sys
import time
import re
import collections
import datetime
import argparse
from paramiko import SSHClient
from scp import SCPClient
import logging
import paramiko

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def tree(): return collections.defaultdict(tree)


class Session(object):
    """ Create a ssh session with a host using a given username and password.

    Keyword Arguments:
    host -- IP of the host you want to connect to via ssh (default None)
    username -- Username to be used in authentication with the host
                (default None)
    password -- Password to be used in authentication (default None)
    port     -- SSH Port (default 22)
    """

    def __init__(self, host=None, username=None, password=None, port=22):
        self._host = host
        self._username = username
        self._password = password
        self._port = port
        if host and username and password:
            self._session = self.connect()

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, username):
        self._username = username

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, port):
        self._port = port

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, password):
        self._password = password

    @property
    def host(self):
        return self._host

    @host.setter
    def host(self, host):
        self._host = host

    @property
    def session(self):
        return self._session

    @session.setter
    def session(self, session):
        self._session = session

    def connect(self):
        """ Connect to the host at the IP address specified."""
        session = paramiko.SSHClient()
        session.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        paramiko.util.log_to_file("filename.log")
        session.connect(self._host,
                        port=self._port,
                        username=self._username,
                        password=self._password,
                        allow_agent=False,
                        look_for_keys=False,
                        timeout=20)
        return session

    def new(self, rsession):
        lsession = Session(rsession.host(),
                           rsession.username(),
                           rsession.password(),
                           rsession.port())
        return lsession

    def close(self):
        """ Close the secure shell. """
        self._session.close()


class RemoteShell(Session):
    """
    RemoteShell is a Session which can execute multiple commands on the
    remote host using secure shell. It sleeps for.5 seconds after each
    execution.  The command output can be collected.
    """

    def __init__(self, host=None, username=None, password=None, port=22):
        super().__init__(host, username, password, port)
        self._rsh = self._session.invoke_shell()
        output = self._rsh.recv(65535)
        time.sleep(.5)

    def execute(self, command):
        self._rsh.send(command)
        time.sleep(.5)
        return self

    def output(self, timeout=100000):
        output = ""

        mytimeout = time.time() + timeout
        while not self._rsh.recv_ready():
            time.sleep(1)

            if self._rsh.recv_stderr_ready():
                o = self._rsh.recv_stderr(65535)
                _print("Error:\n")
                _print(o.decode("utf-8", errors='ignore'))
                break

            if mytimeout > 0 and time.time() > mytimeout:
                _print("Error: SSH revc_ready Timeout")
                return False

        o = self._rsh.recv(65535)
        try:
            output = o.decode("utf-8", errors='ignore')
        except UnicodeDecodeError as ex:
            _print("=====DecodeError:")
            _print(o)
            output = o
        return output


class RemoteExecute(Session):
    """
    RemoteExecute is a Session which can execute a single commands on the
    remote host using secure shell. No command output is returned.
    """

    def __init__(self, host=None, username=None, password=None, port=22):
        super().__init__(host, username, password, port)

    def execute(self, command):
        return self._session.exec_command(command)


def run_cmd(con, cmd, args=None):
    con.execute(cmd)
    buff = o = ""
    defaulttimeout = 100000
    timeout = time.time() + defaulttimeout

    while True:
        if o.find('yes/no') >= 0:
            con.execute("yes\n")
            o = con.output(30)
        elif o.find('y/n') >= 0:
            con.execute("y\n")
            o = con.output(30)
        elif o.find('Password:') >= 0 and args:
            con.execute(args['password'] + "\n")
            o = con.output(30)
        else:
            o = con.output()
        if o and not isinstance(o, (int, float)):
            line = o.splitlines()[-1]
            if line.find('~$') >= 0 or line.find('#') >= 0:
                buff += o
                break
        else:
            o = "\n======== cli: " + cmd + " was not exec completly======\n"
            buff += o
            break
        buff += o
        if time.time() > timeout:
            _print("Error: CLI Exec Timeout After " + str(defaulttimeout))
            con.execute("\003\003\003\003")
            break

    return buff


def connect_to_device(host, username, password, port=22):
    rshell = RemoteShell(host=host, username=username, password=password, port=port)
    _print("connected to the device")
    return rshell


def save_config(rshell_router, location, filename):
    cmd = "copy running-config "+location + filename + "\n\nyes"
#    _print(cmd)
    ret = run_cmd(rshell_router, cmd + "\n")
    _print(ret)
    time.sleep(10)


def diff_config(rshell_router, config1, config2, filename):

    cmd = "run\ndiff " + config1 + " " + config2 + "\nexit"
#    _print(cmd)
    ret = run_cmd(rshell_router, cmd + "\n")
    _print(ret)

    with open( filename, 'w') as f:
        f.write(ret)
    _print(filename +" saved!")


def scp_file(host, port, username, password, filename, destination):

    ssh = SSHClient()
    ssh.load_system_host_keys()
    ssh.connect(hostname=host,
                port=port,
                username=username,
                password=password,
                allow_agent=False,
                look_for_keys=False,
                timeout=20)

    # SCPCLient takes a paramiko transport as its only argument
    scp = SCPClient(ssh.get_transport())
    scp.put(filename, destination)
    scp.close()


def load_config(rshell_router, host, username, password, mode, filename, config, original_config):

    output = ""
    cmds = []

    if mode == "1":

#        scp_file(host, 22, username, password, filename, "/harddisk:/")

        scp = SCPClient(rshell_router.session.get_transport())
        scp.put(filename, "/harddisk:/")
        scp.close()

        cmds.append("configure terminal")
        cmds.append("load harddisk:/" + filename)
        for cmd in cmds:
#            _print(cmd)
            ret = run_cmd(rshell_router, cmd + "\n")
            output += ret
            _print(ret)

        if output.find("Couldn't open file") > 0:
            _print("Fail to load config!")
            cmd = ("abort")
#            _print(cmd)
            ret = run_cmd(rshell_router, cmd + "\n")
            _print(ret)
            sys.exit()

    else:
        cmds.append("configure terminal")
        cmds.append("load harddisk:/" + original_config)
        for cmd in cmds:
#            _print(cmd)
            ret = run_cmd(rshell_router, cmd + "\n")
            output += ret
            _print(ret)

        if output.find("Couldn't open file") > 0:
            _print("Fail to load config!")
            cmd = ("abort")
#            _print(cmd)
            ret = run_cmd(rshell_router, cmd + "\n")
            _print(ret)
            sys.exit()

        cmds.clear()
        if not filename == "":
            with open(filename, "r") as f:
                additional_configs = f.readlines()
                cmds.extend(additional_configs)

        cmds.extend(config)

        for cmd in cmds:
#            _print(cmd)
            ret = run_cmd(rshell_router, cmd + "\n")
            output += ret
            _print(ret)

    cmd = "commit replace\nyes"
#    _print(cmd)
    ret = run_cmd(rshell_router, cmd + "\n")
    _print(ret)

    if ret.find("fail") > 0:
        _print("Fail to commit config!")
        cmd = ("abort")
#        _print(cmd)
        ret = run_cmd(rshell_router, cmd + "\n")
        _print(ret)
        sys.exit()

    cmd = ("end")
#    _print(cmd)
    ret = run_cmd(rshell_router, cmd + "\n")
    _print(ret)

    _print("Sleep for 15 seconds!")
    time.sleep(15)


def _print(output):
    print(output)
    sys.stdout.flush()


if __name__ == "__main__":


    parser = argparse.ArgumentParser(description='Config script')
    parser.add_argument("-u", "--user", dest="username", default="root")
    parser.add_argument("-p", "--password", dest="password", default="lablab", help="password")
    parser.add_argument("-a", "--host", dest="host", help="Host IP address", required=True)
    parser.add_argument("-m", "--mode", dest="mode", help="1: Replace config; 2: Add config", default="1")
    parser.add_argument("-f", "--filename", dest="filename",
                        help="Path and name of the file which contains the configs.", default="")
    parser.add_argument("-i", "--input", dest="input", help="Enable manual additional config input. (Only for mode 2)", default="no")

    args = parser.parse_args()

    if args.mode == "1" and args.filename == "":
        _print("Error: Must specify a config file when using mode 1")
        sys.exit()

    # Manual input config
    additional_configs = []
    if args.input=="yes":
        _print("Please enter the additional configs. End the input with \"end\":")
        while True:
            line = input()
            if line == "end":
                _print("Config input finished")
                break
            additional_configs.append(line)

    # Create connection
    rshell_router = connect_to_device(args.host, args.username, args.password)

    # Save config_1
    config1 = args.host+"-before.config"
    save_config(rshell_router, "harddisk:/", config1)

    # Load config based on the specified mode
    load_config(rshell_router, args.host, args.username, args.password, args.mode, args.filename, additional_configs, config1)

    # Save config_2
    config2 = args.host + "-after.config"
    save_config(rshell_router, "harddisk:/", config2)

    # Diff config
    diff_config(rshell_router, "/harddisk:/"+config1, "/harddisk:/"+config2, args.host+"-diff.txt")

    rshell_router.close()


