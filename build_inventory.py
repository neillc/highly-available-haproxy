"""
Python script to build the inventory for the ansible playbook.
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
            "networks":server["Networks"]["ha-proxy-internal"], 
            "groups":server["Properties"]["groups"].split(";")
        } for server in json.loads("".join(sys.stdin.readlines())) 
        ]

    env = jinja2.Environment(
        loader = jinja2.FileSystemLoader("files/templates")
        )
    template = env.get_template("inventory.j2")
    bastion = get_internal(servers, "bastion")[0]
    backend_hosts = get_internal(servers, "backend")
    proxy_hosts = get_internal(servers, "proxy")
    print(template.render(bastion=bastion, proxy_hosts=proxy_hosts, backend_hosts=backend_hosts))


if __name__ == '__main__':
    main()