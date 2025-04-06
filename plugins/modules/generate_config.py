#!/usr/bin/env python3

from ansible.module_utils.basic import AnsibleModule

from nebula_confgen import NetStack, Host, AuthorizedUser
from pathlib import Path



def main():
    module_args = dict(
        target_host=dict(type='str', required=True),
        listen_port=dict(type='int', required=True),
        hosts_info=dict(type='dict', required=True),
        ca=dict(type='list', required=True),
        authorized_users=dict(
            type='list',  # List of dictionaries
            elements='dict',  # Each item is a dictionary
            required=False,
            default=list(),
            options=dict(
                user=dict(type='str', required=True),  # 'user' is a string
                keys=dict(
                    type='list',  # 'keys' is a list
                    elements='str',  # List contains strings
                    required=True
                )
            )
        ),
        default_inbound_rules=dict(
            type='list',
            elements='dict',
            required=False,
            default=list(),
        )
    )

    result = dict(
        changed=False,
        config={}
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    try:
        netstack = NetStack(
            listen_port=module.params['listen_port'],
            ca=[Path(i) for i in module.params['ca']],
            authorized_users=tuple(AuthorizedUser(**d) for d in module.params['authorized_users']),
            hosts=[],
            default_inbound_rules=tuple(module.params['default_inbound_rules'])
        )

        target_host = None
        for inventory_name, props in module.params['hosts_info'].items():
            host = Host(
                name=inventory_name,
                am_relay=module.boolean(props.get('am_relay', False)),
                am_lighthouse=module.boolean(props.get('am_lighthouse', False)),
                public_addresses=(props['ansible_host'],),
                addr=props['nebula_addr'],
                subnet=props['nebula_subnet'],
                inbound_rules=tuple(props.get('inbound_rules', tuple())),
                merge_stack_inbound_rules=bool(props.get('merge_stack_inbound_rules', True))
            )
            if host.name == module.params['target_host']:
                target_host = host

            netstack.add_host(host)

        if target_host is None:
            module.fail_json(msg=f"Failed to find target host ({module.params['target_host']}) among hostvars ({ module.params['hosts_info'].keys()})")

        result['config'] = netstack.get_config(target_host)
        result['msg'] = "Config generated successfully"

        module.exit_json(**result)

    except Exception as e:
        module.fail_json(msg="Something went wrong", exception=e)


if __name__ == '__main__':
    main()