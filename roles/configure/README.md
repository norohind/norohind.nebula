Nebula role
=========

A role to install and manage [nebula vpn](https://nebula.defined.net/) nodes. It automatically detects and eliminates drift between 
what groups, host name, ip address set in inventory and what actually is present in
host's cert. When it reissues a cert due to drift, the role will show you what exactly have drifted away.
The role generates nebula and embedded sshd private keys on remote hosts and never copies them off hosts.

It doesn't support password encrypted CAs.

It does not generate configs for you, you are expected to create hosts configs before running the role. It expects
to find config for every host in `configs/{{ inventory_hostname }}.yaml`.

It does use provided by a distro nebula package. Tested on Fedora 40, Debian 12 and Void Linux. On Void
nebula package was manually installed prior to running the role.

Requirements
------------

You have to manually generate CA before using this role. One of options is
```shell
nebula-cert ca -name "My CA for nebula"
```

It will place files ca.crt and ca.key in the current directory.

Role Variables
--------------

| Parameter name      | Default value | Description                                                                                                                                                                                                                                                                                                                                                                                                                                  |
|---------------------|---------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ca_fingerprint      |               | You must provide a value. It is used to conditionally reissue certificate for a host during CA rotation. You can get fingerprint for your CA using `nebula-cert print -path ca.crt -json \| jq .fingerprint -r`                                                                                                                                                                                                                              |
| days_left_threshold | 30            | Amount of days before host cert expires the role will attempt to reissue cert for the host. It doesn't make much sense if you don't limit duration of host certs, because then nebula issues certificates with the same expiration time as CA.                                                                                                                                                                                               |
| config_prefix       | /etc/nebula   | Directory where on the host configuration for nebula should be located                                                                                                                                                                                                                                                                                                                                                                       |
| ca_crt              | ca.crt        | Location of ca.crt on localhost                                                                                                                                                                                                                                                                                                                                                                                                              |
| ca_key              | ca.key        | Location of ca.key on localhost                                                                                                                                                                                                                                                                                                                                                                                                              |
| ct_log_file         | ct.log        | Location of file where the role will write information about all issued certificates. It can be helpful if you would need to blacklist a host certificate before it expires. Then you can just look into this look, find line of appropriate certificates, extract its fingerprint and put it into `pki.blocklist`                                                                                                                           |
| nebula_service_name | nebula        | On some systems you might want to adjust service name. On fedora by default it's `nebula`. On debian it would be `nebula@config`                                                                                                                                                                                                                                                                                                             |
| duration            |               | Value for argument `-duration`, directly passed to `nebula-cert`. If no value is supplied, it gets omitted from `nebula-cert` command, and `nebula-cert` defaults to CA expiration time.                                                                                                                                                                                                                                                     |
| pub_dir             | pubkeys       | Directory where role will copy nebula public keys from remote hosts to issue certificates, it doesn't remove these pub keys, so you could put some automation around it to track changes of keypairs on existing hosts                                                                                                                                                                                                                       |
| configs_dir         | configs       | Directory where role will get configs for hosts. I.e. for host "server-a" it will grab `"{{ configs_dir }}/server-a.yaml` file as config.                                                                                                                                                                                                                                                                                                    |
| do_reissue          | false         | It's mostly internal variable, you can override it with value `true` if you need unconditionally reissue certificate. It is defined in vars/main.yaml, meaning it has higher position in precedence order, thus you can't overwrite it as easy as other variables. Please reference [variable precedence](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_variables.html#variable-precedence-where-should-i-put-a-variable) |
| nebula_addr         |               | You must provide a value. It's a host level var, you should set this in inventory. Example: `10.1.0.1/24`                                                                                                                                                                                                                                                                                                                                    |
| nebula_groups       |               | It's a host level var, you should set this in inventory. Example: `servers,vps`. You might leave it empty                                                                                                                                                                                                                                                                                                                                    |


Dependencies
------------

`community.general.runit` is used for service reload on runit systems.

Example Playbook
----------------

    ---
    - name: Setup nodes
      hosts: linux
      strategy: free
      gather_facts: false  # The role don't need facts
      roles:
        - role: nebula
          ca_fingerprint: abaecbeac8e8fa98bde42a2c4ccff1dcc9a07b7c3392396aaa4039fb6ed570ee  # Acquired with `nebula-cert print -path ca.crt -json | jq`
          # ct_log_file: /dev/null  # If you don't need ct.log
          # do_reissue: true  # If you need to unconditionally reissue certificate
          # nebula_service_name: nebula@config  # For debian systems name of the service might actually be nebula@config

Inventory example, sorry, only JSON.

```json5
{
  "linux": {
    "hosts": {
      "myserver-1.internal": {  // inventory_hostname is used as name in nebula certificates and to locate configs
        "ansible_host": "my-server-1-ssh",  // You might have this host configured under another name in your ssh config
        "nebula_addr": "10.1.0.1/24",
        "nebula_groups": "server,vps,region:eu"
      },
      "laptop": {
        "nebula_addr": "10.1.0.2/24",
        "nebula_groups": "laptop",
      },
    }
  }
}
```

CA Rotation
-----------

There are [official guide](https://nebula.defined.net/docs/guides/rotating-certificate-authority/) about this. Please read it first. 

1. Generate new CA.
2. Append new CA cert to trust bundle in configs, as described in official guide. Configs generation is out of scope for this project.
3. Apply role with new configs.
4. Update variable `ca_crt` and `ca_key` to reference new CA.
5. Apply role. It will detect mismatch in CA fingerprint and reissue certificates. You might want to start by applying role on one host first to check it works as expected.
6. Remove old CA cert from trust bundle in configs.
7. Apply role with new configs.

License
-------

BSD-3-Clause

Author Information
------------------

60548839+norohind@users.noreply.github.com