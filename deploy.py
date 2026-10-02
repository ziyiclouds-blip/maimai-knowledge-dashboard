# -*- coding: utf-8 -*-
"""一键部署 + 热重载到 NAS 上的 MaiBot（不重启主进程）。

用法: python deploy.py [--full]
  默认: 上传插件文件 -> 杀掉插件 Runner 进程 -> Host 自动拉起并重载插件（约 5 秒，bot 不掉线）
  --full: 改为重启整个 maim-bot-core 容器（慢，但最干净）
"""

from __future__ import annotations

import sys
import time

import paramiko

NAS_HOST = "192.168.124.12"
NAS_USER = "longxia"
NAS_PASS = "ziyi1234"
PLUGIN_DIR = "/vol2/maibot-data/data/MaiMBot/plugins/maimai_knowledge_dashboard/"
FILES = [
    "plugin.py",
    "renderer.py",
    "config.py",
    "config.toml",
    "llm_client.py",
    "_manifest.json",
    "README.md",
]

KILL_RUNNER_SH = (
    b"#!/bin/sh\n"
    b'for p in /proc/[0-9]*/cmdline; do\n'
    b'  pid=$(echo "$p" | sed "s|/proc/||; s|/cmdline||")\n'
    b'  line=$(tr "\\0" " " < "$p" 2>/dev/null)\n'
    b'  case "$line" in\n'
    b'    *runner_main*) kill -TERM "$pid"; echo "killed $pid";;\n'
    b'  esac\n'
    b"done\n"
)


def run_ssh(t: paramiko.Transport, cmd: str, label: str = "") -> str:
    ch = t.open_session()
    ch.exec_command(cmd)
    out = ch.recv(262144).decode(errors="replace")
    ch.recv_exit_status()
    if label:
        print(f"[{label}] {out.strip()[:400]}")
    return out


def main() -> int:
    full = "--full" in sys.argv
    t = paramiko.Transport((NAS_HOST, 22))
    t.connect(username=NAS_USER, password=NAS_PASS)
    sftp = paramiko.SFTPClient.from_transport(t)

    for f in FILES:
        try:
            sftp.put(f, PLUGIN_DIR + f)
            print("put", f)
        except FileNotFoundError:
            print("skip (not found)", f)
    sftp.close()

    run_ssh(t, f"echo {NAS_PASS} | sudo -S rm -rf {PLUGIN_DIR}__pycache__", "clean pycache")

    if full:
        run_ssh(t, f"echo {NAS_PASS} | sudo -S docker restart maim-bot-core", "docker restart")
        time.sleep(30)
    else:
        sftp = paramiko.SFTPClient.from_transport(t)
        fh = sftp.file("/vol2/maibot-data/_killrunner.sh", "w")
        fh.write(KILL_RUNNER_SH)
        fh.close()
        sftp.close()
        run_ssh(
            t,
            "echo {} | sudo -S docker cp /vol2/maibot-data/_killrunner.sh maim-bot-core:/tmp/_killrunner.sh "
            "&& echo {} | sudo -S docker exec maim-bot-core sh /tmp/_killrunner.sh".format(NAS_PASS, NAS_PASS),
            "kill runner",
        )
        time.sleep(15)

    i_log = run_ssh(
        t,
        "echo {} | sudo -S docker logs --since 60s maim-bot-core 2>&1 "
        "| grep -iE 'knowledge-dashboard|Runner|加载失败' | head -20".format(NAS_PASS),
    )
    sys.stdout.buffer.write(i_log.encode("utf-8", errors="replace"))
    t.close()
    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
