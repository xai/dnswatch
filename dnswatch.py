#!/usr/bin/python3
#
# The MIT License (MIT)
# 
# Copyright (c) 2015 Olaf Lessenich
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import argparse
import os
import socket
from ipaddress import IPv4Network
from os.path import expanduser, sep

settings_dir = expanduser("~") + sep + ".dnswatch"
ok_message = "OK: %s (%s)"
mismatch_message = "MISMATCH: %s (STORED: %s, NOW: %s)"


def lookup(ip, mapping):
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        if hostname != None and not hostname.endswith(".local"):
            mapping[ip] = hostname
        return hostname
    except socket.herror:
        pass


def store(filename, mapping):
    try:
        out_file = open(filename, 'w')
        for ip, hostname in mapping.items():
            if hostname != None and not hostname.endswith(".local"):
                out_file.write("%s,%s\n" % (ip, hostname))
    finally:
        out_file.close()


def load(filename, mapping):
    try:
        in_file = open(filename, 'r')
        for line in in_file.readlines():
            entry = line.strip().split(',')
            mapping[entry[0]] = entry[1]
    finally:
        in_file.close()


def watch(subnet, prepare, verbose):
    current = dict()
    stored = dict()

    if not os.path.exists(settings_dir):
        os.mkdir(settings_dir)

    filename = settings_dir + sep + subnet.replace('/', '_')
    if not os.path.exists(filename):
        prepare = True

    for addr in map(str, IPv4Network(subnet)):
        hostname = lookup(addr, current)
        if prepare and verbose and hostname != None \
                and not hostname.endswith(".local"):
            print("%s: %s" % (addr, hostname))

    if prepare:
        store(filename, current)
    else:
        load(filename, stored)
        for ip, hostname in sorted(current.items()):
            stored_hostname = stored.pop(ip, None)
            if stored_hostname != hostname:
                print(mismatch_message % (ip, stored_hostname, hostname))
            elif verbose:
                print(ok_message % (ip, hostname))
        for ip, hostname in stored.items():
            print(mismatch_message % (ip, hostname))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--prepare",
                        action="store_true",
                        dest="prepare",
                        default=False,
                        help="update stored hostnames")
    parser.add_argument("-q", "--quiet",
                        action="store_false",
                        dest="verbose",
                        default=True,
                        help="quiet output")
    parser.add_argument("subnets", nargs='+')
    args = parser.parse_args()

    for subnet in args.subnets:
        watch(subnet, args.prepare, args.verbose)


if __name__ == "__main__":
    main()
