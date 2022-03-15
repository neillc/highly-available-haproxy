"""
Script to build the group vars needed by ansible. Expects json on stdin
"""
import json
import re
import sys
import yaml

import bpdb
import jinja2

def get_internal(servers, server_type):
    return [
        {
            "name":server["name"], 
            "address":server["networks"][-1]
        } for server in servers if server_type in server["groups"]
        ]


def main():
    bastion = [ 
        server["Networks"]['ha-proxy-internal'][-1]
         for server in json.loads("".join(sys.stdin.readlines())) if "bastion" in server["Name"] 
        ][0]

    print(f"ansible_ssh_common_args: '-J cloud-user@{bastion} -o \"StrictHostKeyChecking=no\"'")


if __name__ == '__main__':
    main()
