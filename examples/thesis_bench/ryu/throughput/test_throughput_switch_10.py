#  Copyright @2018
#
#  GERCOM - Federal University of Pará - Brazil
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
#  GERCOM - Federal University of Pará - Brazil
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
#  GERCOM - Federal University of Pará - Brazil
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
#  GERCOM - Federal University of Pará - Brazil
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
#  GERCOM - Federal University of Pará - Brazil
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import csv
import logging
import os
import subprocess
import threading
import time

from vsdnemul.cli import Cli
from vsdnemul.dataplane import Dataplane
from vsdnemul.lib.log import get_logger
from vsdnemul.models.node.controller.ryuctl import Ryuctl
from vsdnemul.models.node.hypervisor.flowvisor import FlowVisor
from vsdnemul.models.node.switch.whitebox import Whitebox
from vsdnemul.node import NodeType

log = logging.getLogger(__name__)

signal = threading.Event()


def add_slice(node, name, ctl):
    cmd = "/usr/bin/fvctl -f /root/pass add-slice -p flowvisor {n} {c} admin@admin.com"
    ret = node.run_command(cmd=cmd.format(n=name, c=ctl))
    log.info(str(ret[1], encoding="utf-8"))


def add_flowspace(node, name, dpid, prio, match, slice, perm=7):
    cmd = "/usr/bin/fvctl -f /root/pass add-flowspace {n} {d} {p} {m} {s}={r}"
    ret = node.run_command(cmd=cmd.format(n=name, d=dpid, p=prio, m=match, s=slice, r=perm))
    log.info(str(ret[1], encoding="utf-8"))


def gen_dpid(i):
    t = "0000000000000000"
    off_set = len(i)
    o = t[:-off_set] + i
    return o


def run_throughput(node, name, loop, macs, output):
    cmd = "python3 /root/benchtraffic/trafficgen.py -l {l} -c {m} -m 1 -n {n} -d {t}"
    ret = node.run_command(cmd=cmd.format(l=loop, m=macs, n=name, t=output))
    log.info("throughput test has finished on {}".format(node.getName()))
    log.info(str(ret[1], encoding="utf-8"))


def run_latency(node, name, loop, macs, output):
    cmd = "python3 /root/benchtraffic/trafficgen.py -l {l} -c {m} -m 0 -n {n} -d {t}"
    ret = node.run_command(cmd=cmd.format(l=loop, m=macs, n=name, t=output))
    log.info("latency test has finished on {}".format(node.getName()))
    log.info(str(ret[1], encoding="utf-8"))


def run_throughput_test(ths, dp, loop, macs, output):
    for a in dp.getNodes().values():
        if a.__type__.name == NodeType.SWITCH.name:
            log.info("initializing throughput test on node {}".format(a.getName()))
            t = threading.Thread(target=run_throughput, args=(a, a.getName(), loop, macs, output))
            t.setName(a.getName())
            t.start()
            ths.append(t)
        else:
            log.info("Node is not switch")


def run_latency_test(ths, dp, loop, macs, output):
    for a in dp.getNodes().values():
        if a.__type__.name == NodeType.SWITCH.name:
            log.info("initializing latency test on node {}".format(a.getName()))
            t = threading.Thread(target=run_latency, args=(a, a.getName(), loop, macs, output))
            t.setName(a.getName())
            t.start()
            ths.append(t)
        else:
            log.info("Node is not switch")


def get_statistic_container(statis, name):
    while signal.is_set():
        cmd = 'docker stats --no-stream --format "{{.CPUPerc}}:{{.MemUsage}}:{{.MemPerc}}" ' + name
        out = subprocess.check_output(cmd, shell=True)
        o = str(out, encoding='utf8').strip()
        statis.append(o.split(":"))


def gen_statis(dir, stats):
    with open('{}/statis.csv'.format(dir), mode='w') as csv_file:
        header = ["CPU_USAGE(%)", "MEMORY(MiB)", "MEMORY_TOTAL(GiB)", "MEMORY_USAGE(%)"]
        writer = csv.DictWriter(csv_file, fieldnames=header, delimiter=' ')
        writer.writeheader()
        for i in stats:
            writer.writerow(
                {"CPU_USAGE(%)": i[0][:-1], "MEMORY(MiB)": i[1].split("/")[0].strip()[:-3],
                 "MEMORY_TOTAL(GiB)": i[1].split("/")[1].strip()[:-3],
                 "MEMORY_USAGE(%)": i[2][:-1]})


def create_switches(dp, n):
    for i in range(0, n):
        dp.addNode(
            Whitebox("sw{}".format(i + 1), bridge_oper="tswitch0", dpid=gen_dpid(i=str(i + 1)), ofversion="OpenFlow13"))


def config_switches(dp, ctl):
    def config_dut_port(n, b):
        cmd_veth = "/sbin/ip link add {p1} type veth peer name {p2}"
        cmd_up = "/sbin/ip link set {p1} up"
        o1 = n.run_command(cmd=cmd_veth.format(p1="dut1", p2="veth0"))
        log.info(o1)
        o2 = n.run_command(cmd=cmd_veth.format(p1="dut2", p2="veth1"))
        log.info(o2)
        n.run_command(cmd=cmd_up.format(p1="dut1"))
        n.run_command(cmd=cmd_up.format(p1="dut2"))
        n.run_command(cmd=cmd_up.format(p1="veth0"))
        n.run_command(cmd=cmd_up.format(p1="veth1"))
        n.set_port(bridge=b, port="veth0", portnum="1")
        n.set_port(bridge=b, port="veth1", portnum="2")
        log.info("dut ports configured")

    for n in dp.getNodes().values():
        if n.__type__.name == NodeType.SWITCH.name:
            config_dut_port(n, b="tswitch0")
            n.setController(target=ctl, bridge="tswitch0")
        else:
            log.info("Node is not switch")


def config_slice(dp, hyp, ctl):
    slice = "slice1"
    add_slice(node=hyp, name=slice, ctl=ctl)

    for n in dp.getNodes().values():
        if n.__type__.name == NodeType.SWITCH.name:
            log.info("{}:{}".format(n.getName(), n.getDpid(bridge="tswitch0")[0][0]))
            add_flowspace(hyp, name=n.getName(), dpid=n.getDpid("tswitch0")[0][0], prio=10, slice=slice,
                          match="dl_vlan=20", perm=7)


if __name__ == '__main__':
    logger = get_logger(__name__)

    output = "/root/results/ryu/throughput/switches-10"
    try:
        os.makedirs(output, exist_ok=True)
    except Exception as ex:
        log.error(str(ex))

    dp = Dataplane()
    ctl = dp.addNode(Ryuctl("ctl1"))
    #hyp = dp.addNode(FlowVisor("hyp1"))
    time.sleep(2)
    ctl_addr = "tcp:{ip}:6653".format(ip=ctl.getControlIp())
    #hyp_addr = "tcp:{ip}:6633".format(ip=hyp.getControlIp())
    threads = []
    stats = []
    create_switches(dp, 10)
    config_switches(dp, ctl=ctl_addr)
    #config_slice(dp, hyp=hyp, ctl=ctl_addr)
    signal.set()
    #statis = threading.Thread(target=get_statistic_container, args=(stats, 'hyp1'))
    #statis.start()
    run_throughput_test(ths=threads, dp=dp, loop="15", macs="10000", output=output)

    test_on = True

    while test_on:
        count = len(threads)
        for th in threads:
            if not th.isAlive():
                count = count - 1
        log.info("threads actives:{}".format(count))
        if count == 0:
            test_on = False
            signal.clear()
            #statis.join()

        time.sleep(1)

    gen_statis(output, stats)
    """
    cli = Cli(dp) 
    cli.cmdloop()
    """
    dp.stop()
