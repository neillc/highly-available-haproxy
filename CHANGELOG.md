# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0 - 2022-03-15]

Initial commit to GitHub. This version can create an OpenStack environment (
networks, floating ips, security groups, instances) to demonstrate a highly
available haproxy setup using keepalived.

This is an initial POC at this point and feedback is sought to turn it into a
useful product.

A combination of HEAT (to create VMs) and ansible (to configure the VMs) is
used.

The ansible is unaware of OpenStack and it should be simple to change it to 
configure bare metal machines, VMs or even containers.

The demonstration app is a very basic static ngnix website, plus a simple http
server based on the python http.server module on a non-standard port that runs
on three backend hosts. The app serves a page showing the hostname of the server
it is from. 

In front of that is a two node haproxy using keepalived and a virtual ip for 
failover. The virtual ip is implemented as a neutron port with a floating ip.

There is a bastion host that can act as an ssh proxy for direct access to all of
the instances on the private network. The bastion also runs an nginx reverse
proxy that allows direct access to the app servers and the two haproxy servers.
Setting up hostnames will allow for direct access via curl or similar for
testing.

Logs from the haproxy instances are sent to the bastion host via rsyslogd.
