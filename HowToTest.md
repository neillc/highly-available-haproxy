## Creating the test environment in OpenStack using HEAT

Assumes that you have an OpenStack project already available to run these tests
in. For preference this project should contain nothing. It will need access to
an external (provider) network to create floating ips on. The project needs two
floating ips, one for the bastion and one for the keepalived vip.

If the test environment has been created in openstack previously then delete the
HEAT stack

```bash
openstack stack create -t ha-proxy-env.yaml ha2-proxy --wait -e env.yaml 
```

Create an environment file along the lines of 

```yaml
parameters:
  ssh_password: apassword
  public_key: ssh-rsa AAAAxxxxyyyyzzzzaaaabbbb= user@laptop.example.com
  test_port: 3663
  nameserver_ip1: xx.xx.xx.xx
  nameserver_ip2: xx.xx.xx.xx
  external_network_name: public

```

Create the landscape using the HEAT template (assuming you named you env file
env.yaml):

```
openstack stack create -t ha-proxy-landscape.yaml ha2-proxy --wait -e env.yaml -v

...

2022-03-15 05:00:56Z [ha2-proxy]: CREATE_COMPLETE  Stack CREATE completed successfully
+---------------------+--------------------------------------------------------------------+
| Field               | Value                                                              |
+---------------------+--------------------------------------------------------------------+
| id                  | 09105bc7-6f80-4cd0-a15a-e7024f962495                               |
| stack_name          | ha2-proxy                                                          |
| description         | Standup infrastructure to test a highly available HA Proxy cluster |
| creation_time       | 2022-03-15T04:58:19Z                                               |
| updated_time        | None                                                               |
| stack_status        | CREATE_COMPLETE                                                    |
| stack_status_reason | Stack CREATE completed successfully                                |
+---------------------+--------------------------------------------------------------------+

```

Note the IP addresses for the keepalived vip and the bastion host.

```
openstack stack show  ha2-proxy -c outputs
+---------+-------------------------------------------------------+
| Field   | Value                                                 |
+---------+-------------------------------------------------------+
| outputs | - description: floating IP assigned to keepalived vip |
|         |   output_key: vip_ip                                  |
|         |   output_value: 99.999.999.999                        |
|         | - description: floating IP assigned to the bastion    |
|         |   output_key: bastion_ip                              |
|         |   output_value: 99.999.999.999                        |
|         |                                                       |
+---------+-------------------------------------------------------+

```

Add entries to your /etc/hosts for the hosts created by the HEAT stack.

```text
172.16.5.20 backend-01
172.16.5.21 backend-02
172.16.5.22 backend-03
172.16.5.11 ha-proxy-main
172.16.5.12 ha-proxy-spare
999.999.999.999 ha-proxy-vip

999.999.999.999 ha-bastion fe-backend-03 fe-backend-01 fe-ha-proxy-spare fe-backend-02 fe-ha-proxy-main fe-haproxy
```


Go to the ansible directory and add an inventory file. It should look something
like this:

```yaml
all:
  hosts:
    bastion:
      ansible_host: ha-bastion
  children:
    backend:
      hosts:
        backend-03:
          ansible_host: 172.16.5.22
        backend-01:
          ansible_host: 172.16.5.20
        backend-02:
          ansible_host: 172.16.5.21
    proxy:
      hosts:
        ha-proxy-spare:
          ansible_host: 172.16.5.12
        ha-proxy-main:
          ansible_host: 172.16.5.11
    internal:
      children:
        backend:
        proxy:
  vars:
    ansible_user: cloud-user
```

Test that you can access all of the VMs with ansible:

```bash
ansible all -i inventory -m ping
bastion | SUCCESS => {
    "ansible_facts": {
        "discovered_interpreter_python": "/usr/libexec/platform-python"
    },
    "changed": false,
    "ping": "pong"
}
backend-02 | SUCCESS => {
    "ansible_facts": {
        "discovered_interpreter_python": "/usr/libexec/platform-python"
    },
    "changed": false,
    "ping": "pong"
}
backend-03 | SUCCESS => {
    "ansible_facts": {
        "discovered_interpreter_python": "/usr/libexec/platform-python"
    },
    "changed": false,
    "ping": "pong"
}
ha-proxy-spare | SUCCESS => {
    "ansible_facts": {
        "discovered_interpreter_python": "/usr/libexec/platform-python"
    },
    "changed": false,
    "ping": "pong"
}
backend-01 | SUCCESS => {
    "ansible_facts": {
        "discovered_interpreter_python": "/usr/libexec/platform-python"
    },
    "changed": false,
    "ping": "pong"
}
ha-proxy-main | SUCCESS => {
    "ansible_facts": {
        "discovered_interpreter_python": "/usr/libexec/platform-python"
    },
    "changed": false,
    "ping": "pong"
}
```

If any of them cannot be reached fix the problem and try again.

You might also want to setup your ssh config to allow easy access to the VMs:

```text
host ha-bastion
	StrictHostKeyChecking no
	UserKnownHostsFile=/dev/null
	User cloud-user

host 172.16.5.*
	StrictHostKeyChecking no
	UserKnownHostsFile=/dev/null
	ProxyJump ha-bastion
	User cloud-user

host ha-proxy-main
	StrictHostKeyChecking no
	UserKnownHostsFile=/dev/null
	ProxyJump ha-bastion
	User cloud-user

host ha-proxy-spare
	StrictHostKeyChecking no
	UserKnownHostsFile=/dev/null
	ProxyJump ha-bastion
	User cloud-user

host backend-01
	StrictHostKeyChecking no
	UserKnownHostsFile=/dev/null
	ProxyJump ha-bastion
	User cloud-user

host backend-02
	StrictHostKeyChecking no
	UserKnownHostsFile=/dev/null
	ProxyJump ha-bastion
	User cloud-user

host backend-03
	StrictHostKeyChecking no
	UserKnownHostsFile=/dev/null
	ProxyJump ha-bastion
	User cloud-user
```

You will want to specify an ssh public key if you're not using your default
identity.

Run the ansible playbook (this may take a long time because it involves a dnf
update for six VMs)

```bash
ansible-playbook -i inventory playbook.yaml -v -e @env.yaml
```

Once the playbook successfully completes you can start testing  connectivity.

You can use anything that can talk http to test, assuming you have an entry for 
the ha-proxy-vip in your /etc/hosts (or DNS).

For example with curl:

```
curl http://ha-proxy-vip 
<html>
    <head>
        <title>Index</title>
    </head>
    <body>
        <h1>backend-01.vm.example.com</h1>
    </body>
```

The roundrobin parameter in the haproxy configuration means you should see the
responses cycle through the three backend servers.

You can also use httpie, elinks or even a gui browser like chrome or firefox.

To test logging ssh to the bastion host and ```tail -f /var/log/haproxy```. Each
time you connect to the ha-proxy-vip you should see a log entry added.

If you have two terminal windows you can watch this in real time.

To test the non-standard port connect to that port on the ha-proxy-vip with your
client.

I like to use watch with httpie/curl for the next stage. With four terminal 
windows (thanks terminator) you can run watch in two of them, tail the haproxy
in the third and use the forth to ssh into the ha-proxy machines.

Find the haproxy that has the internal vip address (I used 172.16.5.5) by sshing
into the two ha-proxy machines (ha-proxy-main and ha-proxy-spare) and using ip a
too see whic has the vip.

Once you find it stop the haproxy service on that machine. If you are running a
client under watch (e.g. ```watch http ha-proxy-vip```) you should see a 
momentary connection error and then things should start working again as the vip
transfers. Restart haproxy on the current machine and stop it on the other one
and you should see the same beahviour.

Throughout this the logging should continue but the source address of the 
messages should change as the vip moves.

You should also be able to see the vip being added and removed by running `ip a`
on the ha-proxy servers.