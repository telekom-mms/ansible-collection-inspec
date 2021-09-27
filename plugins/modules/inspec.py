#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
import os
from json import JSONDecodeError

def run_module():
    module_args = dict(
        src = dict(type = 'str', required = True),

        backend = dict(type = 'str', required = False, default = 'ssh', choices = ['ssh', 'winrm']),
        host = dict(type = 'str', required = False),
        username = dict(type = 'str', required = False),
        password = dict(type = 'str', required = False, no_log = True),
        privkey = dict(type = 'str', required = False),
        binary_path = dict(type = 'str', required = False)
    )

    result = dict(
        changed = False,
        tests = []
    )

    module = AnsibleModule(
        argument_spec = module_args,
        supports_check_mode = True
    )

    if module.check_mode:
        module.exit_json(**result)

    src = module.params['src']
    backend = module.params['backend']
    host = module.params['host']
    username = module.params['username']
    password = module.params['password']
    privkey = module.params['privkey']
    bin_path = module.params.get('binary_path')

    if bin_path is not None:
        run_command = bin_path
    else:
        run_command = module.get_bin_path('inspec', required=True)


    try:
        if not os.path.exists(src):
            module.fail_json(msg = f'Could not find file or directory at: {src}')

        if not host:
            command = f'{run_command} exec {src} --reporter json-min'
        else:
            if not username:
                module.fail_json(msg = 'username must be defined to run on a remote target!')
            if not os.environ.get('SSH_AUTH_SOCK') and not password and not privkey:
                module.fail_json(msg = 'password or privkey must be defined to run on a remote target! Alternatively, you can use SSH_AUTH_SOCK.')

            if os.environ.get('SSH_AUTH_SOCK'):
                command = '{} exec {} -b {} --host {} --user {} --reporter json-min'.format(
                    run_command,
                    src,
                    backend,
                    host,
                    username,
                )
            elif privkey:
                command = '{} exec {} -b {} --host {} --user {} -i {} --reporter json-min'.format(
                    run_command,
                    src,
                    backend,
                    host,
                    username,
                    privkey
                )
            else:
                command = '{} exec {} -b {} --host {} --user {} --password {} --reporter json-min'.format(
                    run_command,
                    src,
                    backend,
                    host,
                    username,
                    password
                )


        rc, stdout, stderr = module.run_command(command)

        if stderr:
            # if 'cannot execute without accepting the license' in inspec_result.stderr:
            if 'cannot execute without accepting the license' in stderr:
                module.fail_json(msg = 'This module requires the Inspec license to be accepted.')
            # elif "Don't understand inspec profile" in inspec_result.stderr:
            elif "Don't understand inspec profile" in stderr:
                module.fail_json(msg = 'Inspec was unable to read the profile structure.')
            # elif 'Could not fetch inspec profile' in inspec_result.stderr:
        elif 'Could not fetch inspec profile' in stderr:
                module.fail_json(msg = 'Inspec was unable to read that profile or test.')

        # result['tests'] = module.from_json(inspec_result.stdout)['controls']
        result['tests'] = module.from_json(stdout)['controls']

        failed = False
        for test in result['tests']:
            if test['status'] == 'failed':
                failed = True
                break

        if failed:
            module.fail_json(msg = 'Some tests failed!', **result)
        else:
            module.exit_json(msg = 'All tests passed.', **result)
    except JSONDecodeError:
        # module.fail_json(msg = f'Inspec did not return correctly. The error was: {inspec_result.stderr}')
        module.fail_json(msg = f'Inspec did not return correctly. The error was: {stderr}')
    except FileNotFoundError:
        module.fail_json(msg = f'This module requires inspec to be installed on the host machine. Searched here: {run_command}')
    except Exception as error:
        module.fail_json(msg = f'Encountered an error: {error}', cmd = command)


def main():
    run_module()


if __name__ == '__main__':
    main()
