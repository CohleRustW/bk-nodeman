#!/opt/py36/bin/python
# -*- encoding:utf-8 -*-
# vim:ft=python sts=4 sw=4 expandtab nu

from __future__ import print_function

import argparse
import json
import os
import re
import socket
import sys
import time
import traceback
from io import StringIO
from pathlib import Path
from subprocess import Popen
from typing import Any, List

PRIVATE_KEY_MERGED_TEXT = """
%%PRIVATE_KEY_MERGED_TEXT%%
"""

CA_FILE_MERGED_TEXT = """
%%PRIVATE_KEY_MERGED_TEXT%%
"""

DEFAULT_HTTP_PROXY_SERVER_PORT = 17981
WIN_CURL_FILES = ("curl.exe", "curl-ca-bundle.crt", "libcurl-x64.dll")

RECV_BUFLEN = 32768  # SSH通道recv接收缓冲区大小
RECV_TIMEOUT = 90  # SSH通道recv超时 RECV_TIMEOUT秒
SSH_CON_TIMEOUT = 10  # SSH连接超时设置10s
MAX_WAIT_OUTPUT = 32  # 最大重试等待recv_ready次数
SLEEP_INTERVAL = 0.3  # recv等待间隔
# 去掉回车、空格、颜色码
CLEAR_CONSOLE_RE = re.compile(r"\\u001b\[\D|\[\d{1,2}\D?|\\u001b\[\d{1,2}\D?~?|\r|\n|\s+", re.I | re.U)
# 去掉其他杂项
CLEAR_MISC_RE = re.compile(r"\$.?\[\D", re.I | re.U)
# 换行转换
LINE_BREAK_RE = re.compile(r"\r\n|\r|\n", re.I | re.U)


def arg_parser() -> argparse.ArgumentParser:
    """Commandline argument parser"""
    parser = argparse.ArgumentParser(description="p-agent setup scripts")
    parser.add_argument("-R", "--remove", action="store_true", default=None, help="uninstall agent")

    parser.add_argument("-f", "--config", type=str, help="a file contain p-agent hosts info")

    parser.add_argument(
        "-j",
        "--json",
        type=str,
        help="a file contain p-agent hosts info in json format",
    )

    parser.add_argument("-I", "--lan-eth-ip", type=str, help="local ip address of proxy")

    parser.add_argument(
        "-l",
        "--download-url",
        type=str,
        help="a url for downloading gse agent packages (without filename)",
    )

    parser.add_argument("-s", "--task-id", type=str, help="task id generated by nodeman, optional")

    parser.add_argument("-r", "--callback-url", type=str, help="api for report step and task status")

    parser.add_argument("-c", "--token", type=str, help="token for request callback api")

    parser.add_argument("-p", "--install-path", type=str, help="install path for gse agent")

    parser.add_argument("-e", "--btfile-server-ip", type=str, help="comma seperated btfile server ip list")
    parser.add_argument("-a", "--data-server-ip", type=str, help="comma seperated data server ip list")
    parser.add_argument("-k", "--task-server-ip", type=str, help="comma seperated task server ip list")

    parser.add_argument("-P", "--parallel", type=int, help="max process in parallel")

    parser.add_argument(
        "-q",
        "--quite",
        action="store_true",
        dest="quiet_mode",
        default=False,
        help="discard remote output, run in silent and keep no persistent connections",
    )

    parser.add_argument(
        "-u",
        "--upgrade",
        action="store_true",
        default=False,
        help="upgrade agent version",
    )

    parser.add_argument(
        "-T",
        "--temp_dir",
        action="store_true",
        default=False,
        help="directory to save downloaded scripts and temporary files",
    )

    parser.add_argument(
        "-o",
        "--package_url",
        type=str,
        help="url for pagent to download package and dependency",
    )

    parser.add_argument(
        "-O",
        "--io-port",
        type=int,
        help="IO_PORT",
    )

    parser.add_argument(
        "-E",
        "--file-svr-port",
        type=int,
        help="FILE_SVR_PORT",
    )

    parser.add_argument(
        "-A",
        "--data-port",
        type=int,
        help="DATA_PORT",
    )

    parser.add_argument(
        "-V",
        "--btsvr-thrift-port",
        type=int,
        help="BTSVR_THRIFT_PORT",
    )

    parser.add_argument(
        "-B",
        "--bt-port",
        type=int,
        help="BT_PORT",
    )

    parser.add_argument(
        "-S",
        "--bt-port-start",
        type=int,
        help="BT_PORT_START",
    )

    parser.add_argument(
        "-Z",
        "--bt-port-end",
        type=int,
        help="BT_PORT_END",
    )

    parser.add_argument(
        "-K",
        "--tracker-port",
        type=int,
        help="TRACKER_PORT",
    )

    parser.add_argument(
        "-L",
        "--download-path",
        type=str,
        help="Tool kit storage path",
    )

    # 主机信息
    parser.add_argument("-HLIP", "--host-login-ip", type=str, help="Host Login IP")
    parser.add_argument("-HIIP", "--host-inner-ip", type=str, help="Host Inner IP")
    parser.add_argument("-HA", "--host-account", type=str, help="Host Account")
    parser.add_argument("-HP", "--host-port", type=str, help="Host Port")
    parser.add_argument("-HI", "--host-identity", type=str, help="Host Identity")
    parser.add_argument("-HC", "--host-cloud", type=str, help="Host Cloud")
    parser.add_argument("-HNT", "--host-node-type", type=str, help="Host Node Type")
    parser.add_argument("-HOT", "--host-os-type", type=str, help="Host Os Type")
    parser.add_argument("-HDD", "--host-dest-dir", type=str, help="Host Dest Dir")

    return parser


args = arg_parser().parse_args(sys.argv[1:])

try:
    # import 3rd party libraries here, in case the python interpreter does not have them
    import paramiko  # noqa
    import requests  # noqa
    import impacket  # noqa

    # import psutil

except ImportError as err:
    from urllib import request

    data = json.dumps(
        {
            "task_id": args.task_id,
            "token": args.token,
            "logs": [
                {
                    "timestamp": round(time.time()),
                    "level": "ERROR",
                    "step": "import_3rd_libs",
                    "log": str(err),
                    "status": "FAILED",
                    "prefix": "[proxy]",
                }
            ],
        }
    ).encode()

    req = request.Request(
        f"{args.callback_url}/report_log/",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    request.urlopen(req)
    exit()


def windows_cmd(
    login_ip: str,
    commands: List[str],
    user: str,
    port: int,
    identity: str,
    download_url: str,
    tmp_dir: str = "",
) -> Any:
    if os.path.isfile(identity):
        report_log(
            "check_auth_type",
            "identity seems like a key file, which is not supported by windows authentication",
            "FAILED",
        )
        return False

    push_win_curl_cmds = ["put {} {}".format(str(Path(args.download_path) / name), tmp_dir) for name in WIN_CURL_FILES]
    execute_win_commands(["mkdir {}".format(tmp_dir)], login_ip, user, identity, download_url)
    try:
        execute_win_commands(push_win_curl_cmds, login_ip, user, identity, download_url)
    except Exception as e:
        report_log("push_curl_exe", f"not found in proxy's miniweb, download from nginx, {e}")
        for name in WIN_CURL_FILES + ("wmiexec.py",):
            report_log("download_file", download_url + f"/{name}")
            download_file(download_url + f"/{name}")
        push_win_curl_cmds = ["put {} {}".format(str(Path(__file__).parent / name), tmp_dir) for name in WIN_CURL_FILES]
        commands = push_win_curl_cmds + commands
    execute_win_commands(commands, login_ip, user, identity, download_url)


def execute_win_commands(commands, login_ip, user, identity, download_url):
    try:
        for cmd in commands:
            noOutput = True if "setup_agent.bat -T" in cmd else False
            report_log("send_install_cmd" if noOutput else "send_cmd", cmd)
            res = execute_cmd(cmd, login_ip, user, identity, download_url, noOutput=noOutput)
            print(res)
    except KeyboardInterrupt as e:
        print("execute {} failed. {}".format(cmd, e))


def rcmd(
    login_ip: str,
    command: List[str],
    account: str,
    port: int,
    identity: str,
    download_url: str,
    tmp_dir: str = "",
    os_type: str = "linux",
):
    ssh_man = SshMan(login_ip, port, account, identity)
    ssh_man.get_and_set_prompt()
    if os_type == "aix":
        cmd = "ksh"
    else:
        cmd = "bash"
    ssh_man.send_cmd("{} -c 'exec 2>&1 && {} '\n".format(cmd, " && ".join(command)), wait_console_ready=False)

    time.sleep(5)
    ssh_man.safe_close(ssh_man.ssh)


def rcmd_aix(login_ip: str, command: List[str], account: str, port: int, identity: str, download_url: str):
    rcmd(login_ip, command, account, port, identity, download_url, os_type="aix")


def is_port_listen(ip: str, port: int) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    r = s.connect_ex((ip, port))

    if r == 0:
        return True
    else:
        return False


def start_http_proxy(ip: str, port: int) -> Any:
    if is_port_listen(ip, port):
        report_log("start_http_proxy", "http proxy exists")
    else:
        Popen("/opt/nginx-portable/nginx-portable restart", shell=True)

        time.sleep(5)
        if is_port_listen(ip, port):
            report_log("start_http_proxy", "http proxy started")
        else:
            report_log("start_http_proxy", "http proxy start failed", "FAILED")
            raise Exception("http proxy start failed.")


def check_and_start_nginx():
    report_log("start_nginx", "starting nginx")
    Popen(
        "if ! [ -f /opt/nginx-portable/logs/nginx.pid ];then /opt/nginx-portable/nginx-portable start; fi",
        shell=True,
    )


def config_parser(conf_file: str) -> List:
    """Resolve formatted lines to object from config file"""

    configs = []

    with open(conf_file, "r", encoding="utf-8") as f:
        for line in f.readlines():
            configs.append(tuple(line.split()))
    return configs


def json_parser(json_file: str) -> List:
    """Resolve formatted lines to object from config file"""

    configs = []

    with open(json_file, "r", encoding="utf-8") as f:
        hosts = json.loads(f.read())
        for host in hosts:
            configs.append(tuple(host))
    return configs


def download_file(url: str) -> str:
    """get files via http"""
    try:
        local_filename = url.split("/")[-1]
        # NOTE the stream=True parameter below
        local_file = Path(__file__).parent / local_filename
        if local_file.is_file():
            report_log("download_file", f"{str(local_file)} already exist")
            return local_filename

        r = requests.get(url, stream=True)
        r.raise_for_status()

        with open(str(local_file), "wb") as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
                    # f.flush()
    except Exception as err:
        report_log("download_file", str(err))
    return local_filename


def execute_cmd(
    cmd_str,
    ipaddr,
    username,
    password,
    download_url,
    domain="",
    share="ADMIN$",
    noOutput=False,
):
    """execute command"""
    try:
        from wmiexec import WMIEXEC
    except ImportError:
        download_file(download_url + "/wmiexec.py")
        from wmiexec import WMIEXEC

    executor = WMIEXEC(cmd_str, username, password, domain, share=share, noOutput=noOutput)
    result_data = executor.run(ipaddr)
    return {"result": True, "data": result_data}


def report_log(step, text, status="-"):
    if not args.callback_url:
        return None
    data = {
        "task_id": args.task_id,
        "token": args.token,
        "logs": [
            {
                "timestamp": round(time.time()),
                "level": "INFO",
                "step": step,
                "log": text,
                "status": status,
                "prefix": "[proxy]",
            }
        ],
    }
    r = requests.post(f"{args.callback_url}/report_log/", json=data)
    return r


def main() -> None:
    REMOVE = "-R" if args.remove else ""

    login_ip = args.host_login_ip
    lan_eth_ip = args.host_inner_ip
    user = args.host_account
    port = args.host_port
    identity = args.host_identity
    cloud_id = args.host_cloud
    _os = args.host_os_type
    tmp_dir = args.host_dest_dir

    # 启动proxy
    start_http_proxy(args.lan_eth_ip, DEFAULT_HTTP_PROXY_SERVER_PORT)

    construct_cmd = {
        "aix": [
            f"rm -f {tmp_dir}setup_agent.ksh",
            "curl {}/setup_agent.ksh -o {}setup_agent.ksh -sSf -x {}".format(
                args.download_url,
                tmp_dir,
                "http://{}:{}".format(args.lan_eth_ip, DEFAULT_HTTP_PROXY_SERVER_PORT),
            ),
            "nohup ksh {dest_dir}setup_agent.ksh -T {dest_dir} -i {} -I {} -s {} -c {} -l {} -r {} -p {} -e {} "
            "-a {} -k {} -x {} -N PROXY {} -O {} -E {} -A {} -V {} -B {} -S {} -Z {} -K {} 2>&1 &".format(
                cloud_id,
                lan_eth_ip,
                args.task_id,
                args.token,
                args.package_url,
                args.callback_url,
                args.install_path,
                args.btfile_server_ip,
                args.data_server_ip,
                args.task_server_ip,
                "http://{}:{}".format(args.lan_eth_ip, DEFAULT_HTTP_PROXY_SERVER_PORT),
                REMOVE,
                args.io_port,
                args.file_svr_port,
                args.data_port,
                args.btsvr_thrift_port,
                args.bt_port,
                args.bt_port_start,
                args.bt_port_end,
                args.tracker_port,
                dest_dir=tmp_dir,
            ),
        ],
        "linux": [
            f"rm -f {tmp_dir}setup_agent.sh",
            "curl {}/setup_agent.sh -o {}setup_agent.sh -sSf -x {}".format(
                args.download_url,
                tmp_dir,
                "http://{}:{}".format(args.lan_eth_ip, DEFAULT_HTTP_PROXY_SERVER_PORT),
            ),
            "nohup bash {dest_dir}setup_agent.sh -T {dest_dir} -i {} -I {} -s {} -c {} -l {} -r {} -p {} -e {} "
            "-a {} -k {} -x {} -N PROXY {} -O {} -E {} -A {} -V {} -B {} -S {} -Z {} -K {} 2>&1 &".format(
                cloud_id,
                lan_eth_ip,
                args.task_id,
                args.token,
                args.package_url,
                args.callback_url,
                args.install_path,
                args.btfile_server_ip,
                args.data_server_ip,
                args.task_server_ip,
                "http://{}:{}".format(args.lan_eth_ip, DEFAULT_HTTP_PROXY_SERVER_PORT),
                REMOVE,
                args.io_port,
                args.file_svr_port,
                args.data_port,
                args.btsvr_thrift_port,
                args.bt_port,
                args.bt_port_start,
                args.bt_port_end,
                args.tracker_port,
                dest_dir=tmp_dir,
            ),
        ],
        "windows": [
            f"del /q /s /f {tmp_dir}setup_agent.bat {tmp_dir}gsectl.bat",
            f"{tmp_dir}curl.exe {args.download_url}/setup_agent.bat -o {tmp_dir}setup_agent.bat "
            f"-x http://{args.lan_eth_ip}:{DEFAULT_HTTP_PROXY_SERVER_PORT} -sSf",
            f"{tmp_dir}curl.exe {args.download_url}/gsectl.bat -o {tmp_dir}gsectl.bat "
            f"-x http://{args.lan_eth_ip}:{DEFAULT_HTTP_PROXY_SERVER_PORT} -sSf",
            "{dest_dir}setup_agent.bat -T {dest_dir} -i {} -I {} -s {} -c {} -l {} -r {} -p {} "
            '-e "{}" -a "{}" -k "{}" -x {} -N PROXY {} -O {} -E {} -A {} -V {} -B {} -S {} -Z {} -K {}'.format(
                cloud_id,
                lan_eth_ip,
                args.task_id,
                args.token,
                args.package_url,
                args.callback_url,
                args.install_path,
                args.btfile_server_ip,
                args.data_server_ip,
                args.task_server_ip,
                "http://{}:{}".format(args.lan_eth_ip, DEFAULT_HTTP_PROXY_SERVER_PORT),
                REMOVE,
                args.io_port,
                args.file_svr_port,
                args.data_port,
                args.btsvr_thrift_port,
                args.bt_port,
                args.bt_port_start,
                args.bt_port_end,
                args.tracker_port,
                dest_dir=tmp_dir,
            ),
        ],
    }

    _function = {"aix": rcmd_aix, "linux": rcmd, "windows": windows_cmd}

    # # 当CPU或内存消耗较高时，
    # cpu_percent = psutil.cpu_percent()
    # memory_percent = psutil.virtual_memory().percent
    # if cpu_percent > 90 or memory_percent > 90:
    #     sleep_time = random.randint(5, 60)
    #     report_log(
    #         "check_performance",
    #         f"Current performance is not enough. cpu_percent: {cpu_percent}, "
    #         f"memory_percent: {memory_percent}. The task will be retry {sleep_time}s later.",
    #     )
    #     # 先把两个\替换成一个，再把一个统一换成两个，每次Popen都会做一次转义，如果只有一个\就会把\转没，所以每次popen前windows路径统一格式化成两个\
    #     Popen(
    #         f"sleep {sleep_time} && echo '{json.dumps(hosts)}' > {args.json} && "
    #         + " ".join(sys.argv).replace("\\\\", "\\").replace("\\", "\\\\"),
    #         shell=True,
    #     )
    #     sys.exit(0)

    _function[_os](
        login_ip,
        construct_cmd[_os],
        user,
        int(port),
        identity,
        args.download_url,
        tmp_dir,
    )


def ssh_login(login_ip, port, account, identity):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        if identity.startswith("-----BEGIN RSA"):
            try:
                pkey = paramiko.RSAKey.from_private_key(StringIO(identity))
            except paramiko.PasswordRequiredException:
                report_log("login_pagent", "RSAKey need password!", status="FAILED")
            else:
                ssh.connect(
                    hostname=login_ip,
                    username=account,
                    port=port,
                    pkey=pkey,
                    timeout=SSH_CON_TIMEOUT,
                )
        elif identity.startswith("-----BEGIN DSA"):
            # 尝试dsa登录
            try:
                pkey = paramiko.DSSKey.from_private_key(StringIO(identity))
            except paramiko.PasswordRequiredException:
                report_log("login_pagent", "DSAKey need password!", status="FAILED")
            else:
                ssh.connect(
                    hostname=login_ip,
                    username=account,
                    port=port,
                    pkey=pkey,
                    timeout=SSH_CON_TIMEOUT,
                )
        else:
            ssh.connect(login_ip, port, account, identity)
    except paramiko.BadAuthenticationType:
        try:
            #  SSH AUTH WITH PAM
            def handler(title, instructions, fields):
                resp = []

                if len(fields) > 1:
                    raise paramiko.SSHException("Fallback authentication failed.")

                if len(fields) == 0:
                    # for some reason, at least on os x, a 2nd request will
                    # be made with zero fields requested.  maybe it's just
                    # to try to fake out automated scripting of the exact
                    # type we're doing here.  *shrug* :)
                    return resp

                for pr in fields:
                    if pr[0].strip() == "Username:":
                        resp.append(account)
                    elif pr[0].strip() == "Password:":
                        resp.append(identity)

                report_log("login_pagent", f"SSH auth with interactive: {resp}")

                return resp

            ssh_transport = ssh.get_transport()
            if ssh_transport is None:
                report_log("login_pagent", "get_transport is None")
                ssh_transport = paramiko.Transport((login_ip, port))
            try:
                ssh_transport = paramiko.Transport((login_ip, port))
                ssh._transport = ssh_transport
                ssh_transport.start_client()
            except Exception as e:
                report_log("login_pagent", str(e))

            ssh_transport.auth_interactive(account, handler)

            return ssh

        except paramiko.BadAuthenticationType as e:
            SshMan.safe_close(ssh)
            msg = "{}, {}".format(e, "认证方式错误或不支持，请确认。")
            report_log("login_pagent", msg, status="FAILED")
            raise e  # 认证类型错误或不支持

        except paramiko.SSHException as e:
            report_log(
                "login_pagent",
                "attempt failed; just raise the original exception",
                status="FAILED",
            )
            raise e

    except paramiko.BadHostKeyException as e:
        SshMan.safe_close(ssh)
        msg = "SSH authentication key could not be verified.- {}@{}:{} - exception: {}".format(
            account, login_ip, port, e
        )
        msg = "{}, {}".format(msg, "请尝试删除 /root/.ssh/known_hosts 再重试")
        report_log("login_pagent", msg, status="FAILED")
        raise e  # Host Key 验证错误
    except paramiko.AuthenticationException as e:
        SshMan.safe_close(ssh)
        msg = "SSH authentication failed.- {}@{}:{} - exception: {}".format(account, login_ip, port, e)
        msg = "{}, {}".format(msg, "登录认证失败，请确认账号，密码，密钥或IP是否正确。")
        report_log("login_pagent", msg, status="FAILED")
        raise e  # 密码错或者用户错(Authentication failed)
    except paramiko.SSHException as e:
        SshMan.safe_close(ssh)
        msg = "SSH connect failed.- {}@{}:{} - exception: {}".format(account, login_ip, port, e)
        msg = "{}, {}".format(msg, "ssh登录，请确认IP是否正确或目标机器是否可被正常登录。")
        report_log("login_pagent", msg, status="FAILED")
        raise e  # 登录失败，原因可能有not a valid RSA private key file
    except socket.error as e:
        SshMan.safe_close(ssh)
        msg = "TCP connect failed, timeout({}) - {}@{}:{}".format(e, account, login_ip, port)
        msg = "{}, {}".format(msg, "ssh登录连接超时，请确认IP是否正确或ssh端口号是否正确或网络策略是否正确开通。")
        report_log("login_pagent", msg, status="FAILED")
        raise e  # 超时
    else:
        return ssh


class Inspector(object):
    @staticmethod
    def clear(s):
        try:
            # 尝试clear，出现异常（编码错误）则返回原始字符串
            _s = CLEAR_CONSOLE_RE.sub("", s)
            _s = CLEAR_MISC_RE.sub("$", _s)
        except Exception:
            _s = s
        if type(_s) is bytes:
            _s = str(_s, encoding="utf-8")
        return _s

    @staticmethod
    def clear_yes_or_no(s):
        return s.replace("yes/no", "").replace("'yes'or'no':", "")

    def is_wait_password_input(self, buff):
        buff = self.clear(buff)
        return buff.endswith("assword:") or buff.endswith("Password:")

    def is_too_open(self, buff):
        buff = self.clear(buff)
        return buff.find("tooopen") != -1 or buff.find("ignorekey") != -1

    def is_permission_denied(self, buff):
        buff = self.clear(buff)
        return buff.find("Permissiondenied") != -1

    def is_public_key_denied(self, buff):
        buff = self.clear(buff)
        return buff.find("Permissiondenied(publickey") != -1

    def is_invalid_key(self, buff):
        buff = self.clear(buff)
        return buff.find("passphraseforkey") != -1

    def is_timeout(self, buff):
        buff = self.clear(buff)
        return (
            buff.find("lostconnectinfo") != -1
            or buff.find("Noroutetohost") != -1
            or buff.find("Connectiontimedout") != -1
            or buff.find("Connectiontimeout") != -1
        )

    def is_key_login_required(self, buff):
        buff = self.clear(buff)
        return not buff.find("publickey,gssapi-keyex,gssapi-with-mic") == -1

    def is_refused(self, buff):
        buff = self.clear(buff)
        return not buff.find("Connectionrefused") == -1

    def is_fingerprint(self, buff):
        buff = self.clear(buff)
        return not buff.find("fingerprint:") == -1

    def is_wait_known_hosts_add(self, buff):
        buff = self.clear(buff)
        return not buff.find("tothelistofknownhosts") == -1

    def is_yes_input(self, buff):
        buff = self.clear(buff)
        return not buff.find("yes/no") == -1 or not buff.find("'yes'or'no':") == -1

    def is_console_ready(self, buff):
        buff = self.clear(buff)
        return buff.endswith("#") or buff.endswith("$") or buff.endswith(">")

    def has_lastlogin(self, buff):
        buff = self.clear(buff)
        return buff.find("Lastlogin") != -1

    def is_no_such_file(self, buff):
        buff = self.clear(buff)
        return not buff.find("Nosuchfileordirectory") == -1

    def is_cmd_not_found(self, buff):
        buff = self.clear(buff)
        return not buff.find("Commandnotfound") == -1

    def is_transported_ok(self, buff):
        buff = self.clear(buff)
        return buff.find("100%") != -1

    def is_curl_failed(self, buff):
        _buff = buff.lower()
        return (
            _buff.find("failedconnectto") != -1
            or _buff.find("connectiontimedout") != -1
            or _buff.find("couldnotreso") != -1
            or _buff.find("connectionrefused") != -1
            or _buff.find("couldn'tconnect") != -1
            or _buff.find("sockettimeout") != -1
            or _buff.find("notinstalled") != -1
            or _buff.find("error") != -1
            or _buff.find("resolvehost") != -1
        )

    # 脚本输出解析方式
    def is_setup_done(self, buff):
        return buff.find("setup done") != -1 and buff.find("install_success") != -1

    def is_setup_failed(self, buff):
        return buff.find("setup failed") != -1

    def parse_err_msg(self, buff):
        return re.split(":|--", buff)[1]

    def is_cmd_started_on_aix(self, cmd, output):
        """
        :param cmd:
        :param output:
        :return:
        """
        cmd_chars = "".join(c for c in cmd if c.isalpha())
        output_chars = "".join(c for c in output if c.isalpha())
        is_common_substring = re.search(r"\w*".join(list(cmd_chars)), output_chars)
        return is_common_substring or (cmd_chars in output_chars) or (cmd_chars.startswith(output_chars))


class SshMan(object):
    def __init__(self, ip, port, account, identity):
        self.set_proxy_prompt = r'export PS1="[\u@\h_BKproxy \W]\$"'

        # 初始化ssh会话
        self.ssh = ssh_login(ip, port, account, identity)
        self.account = account
        self.password = identity
        self.chan = self.ssh.invoke_shell()
        self.setup_channel()

    def setup_channel(self, blocking=0, timeout=-1):
        """
        # settimeout(0) -> setblocking(0)
        # settimeout(None) -> setblocking(1)
        """
        # set socket read time out
        self.chan.setblocking(blocking=blocking)
        timeout = RECV_TIMEOUT if timeout < 0 else timeout
        self.chan.settimeout(timeout=timeout)

    def wait_for_output(self):
        """
        等待通道标准输出可读，重试32次
        """

        cnt = 0
        while not self.chan.recv_ready():
            time.sleep(SLEEP_INTERVAL)
            cnt += 1
            if cnt > MAX_WAIT_OUTPUT:  # 32
                break

    def send_cmd(self, cmd, wait_console_ready=True, check_output=True):
        """
        用指定账户user发送命令cmd
        check_output: 是否需要从output中分析异常
        """
        # 根据用户名判断是否采用sudo
        if self.account not in ["root", "Administrator"]:
            cmd = "sudo %s" % cmd

        # 增加回车符
        cmd = cmd if cmd.endswith("\n") else "%s\n" % cmd

        # 发送命令并等待结束
        cmd_cleared = inspector.clear(cmd)
        self.chan.sendall(cmd)
        self.wait_for_output()
        report_log(
            "send_install_cmd" if ("setup_agent.sh -T" in cmd) else "send_cmd",
            "start cmd: %s" % cmd,
        )

        cmd_sent = False
        while True:
            time.sleep(SLEEP_INTERVAL)
            try:
                try:
                    output = str(self.chan.recv(RECV_BUFLEN), encoding="utf-8")
                except UnicodeDecodeError:
                    output = str(self.chan.recv(RECV_BUFLEN))
                # 剔除空格、回车和换行
                _output = inspector.clear(output)

            except socket.timeout:
                raise Exception(f"recv socket timeout after %s seconds: {RECV_TIMEOUT}")
            except Exception as e:
                raise Exception(f"recv exception: {e}")

            if _output.find("sudo:notfound") != 1:
                cmd = cmd[len("sudo ") :]
                self.chan.sendall(cmd)

            # [sudo] password for vagrant:
            if check_output and _output.endswith(f"passwordfor{self.account}:"):
                if not cmd_sent:
                    cmd_sent = True
                    self.chan.sendall(self.password + "\n")
                    time.sleep(SLEEP_INTERVAL)
                else:
                    raise Exception(f"password error，sudo failed: {output}")
            elif check_output and (_output.find("tryagain") != -1 or _output.find("incorrectpassword") != -1):
                if cmd_sent:
                    raise Exception(f"password error，sudo failed: {output}")
            elif not wait_console_ready:
                return output
            elif check_output and inspector.is_curl_failed(_output):
                raise Exception(f"curl failed: {output}")
            elif check_output and inspector.is_no_such_file(_output):
                raise Exception(f"no such file: {output}")
            elif inspector.is_console_ready(_output):
                return output.replace(cmd_cleared, "").replace(inspector.clear(self.get_prompt()), "")
            elif _output.find(cmd_cleared) != -1 or cmd_cleared.startswith(_output):
                continue
            elif inspector.is_cmd_started_on_aix(cmd_cleared, _output):
                continue

    def get_and_set_prompt(self):

        prompt = ""
        try:
            self.set_prompt(self.set_proxy_prompt)

            prompt = self.get_prompt()
            is_prompt_set = True
        except Exception:
            is_prompt_set = False

        return is_prompt_set, prompt

    def get_prompt(self):
        """
        尝试获取终端提示符
        """

        self.chan.sendall("\n")

        while True:
            time.sleep(SLEEP_INTERVAL)
            res = self.chan.recv(RECV_BUFLEN)
            buff = inspector.clear(res)
            if inspector.is_console_ready(buff):
                prompt = LINE_BREAK_RE.split(buff)[-1]
                break
        return prompt

    def set_prompt(self, cmd=None):
        """
        尝试设置新的终端提示符
        """
        if cmd is None:
            cmd = self.set_proxy_prompt

        self.chan.sendall(cmd + "\n")
        while True:
            time.sleep(0.3)
            res = self.chan.recv(RECV_BUFLEN)
            buff = inspector.clear(res)
            if buff.find("BKproxy") != -1:
                break

    @staticmethod
    def safe_close(ssh_or_chan):
        """
        安全关闭ssh连接或会话
        """

        try:
            if ssh_or_chan:
                ssh_or_chan.close()
        except Exception:
            pass


# 状态检测
inspector = Inspector()
if __name__ == "__main__":
    try:
        main()
    except Exception:
        report_log("proxy_fail", traceback.format_exc(), status="FAILED")
