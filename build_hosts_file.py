"""
A script to build entries for /etc/hosts to make local testing easier. Expects
json on STDIN.
"""
import json
import re
import sys
import yaml

import jinja2

def get_internal(servers, server_type):
    return [
        {
            "name":server["name"], 
            "address":server["networks"][-1]
        } for server in servers if server_type in server["groups"]
        ]


def main():
    servers = [ 
        {
            "name":server["Name"], 
            "address":server["Networks"]["ha-proxy-internal"][-1], 
        } for server in json.loads("".join(sys.stdin.readlines())) 
        ]

    fe_address = [ server["address"] for server in servers if server["name"] == "ha-bastion"][0]

    for server in servers:
        if server["name"] == "ha-bastion":
            continue

        print(f"{server['address']} {server['name']}")

    names = ([ "fe-" + server['name'] for server in servers if server["name"] != "ha-bastion"])
    names = ["ha-bastion"] + names

    print(fe_address + " " + " ".join(names))


if __name__ == '__main__':
    main()