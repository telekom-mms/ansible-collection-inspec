#!/usr/bin/python

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: inspec
<<<<<<< HEAD
short_description: Execute Inspec profiles from Ansible
description:
   - Add or remove a command to Icinga2 through the director API.
author: Zaeem Parker (@zp4rker)
=======
short_description: Execute Inspec-profiles
description:
   - Execute Inspec-profiles
author: zp4rker (@zp4rker)
>>>>>>> origin/github_test_workflow
notes:
  - This module supports check mode.
options:
  src:
    description:
<<<<<<< HEAD
      - The path to the Inspec profile or test file.
    required: True
    type: str
  backend:
    description:
      - The backend transport to use for remote targets.
    choices: ['ssh', 'winrm']
    default: ssh
    type: str
  host:
    description:
      - The host to use for remote targets.
    type: str
  username:
    description:
      - The username to use for remote targets.
    type: str
  password:
    description:
      - The password to use for remote targets.
    type: str
  privkey:
    description:
      - The path to the private key to use for remote targets (SSH).
    type: str
  binary_path:
    description:
      - The optional path to inspec or cinc-auditor binary.
    type: str
  controls:
    description:
      - A list of strings or regexes that define which controls will be run.
    type: list
    elements: str
=======
      - The path to the Inspec profile or test file
    required: true
    type: str
  backend:
    description:
      - The backend transport to use for remote targets
    required: false
    type: str
    choices: ["ssh", "winrm"]
    default: "ssh"
  host:
    description:
      - The host to use for remote targets
    type: str
  username:
    description:
      - The username to use for remote targets
    type: str
  password:
    description:
      - The password to use for remote targets
    type: str
  privkey:
    description:
      - The path to the private key to use for remote targets (SSH)
    type: str
  binary_path:
    description:
      - The optional path to inspec or cinc-auditor binary
    type: str
>>>>>>> origin/github_test_workflow
"""

EXAMPLES = """
- name: Run inspec tests
  inspec:
    src: /path/to/profile

- name: Run inspec tests on remote target
  delegate_to: localhost
  inspec:
    src: /local/path/to/profile
    backend: ssh
    host: some.host.com
    username: root
    privkey: /path/to/privatekey
"""

from ansible.module_utils.basic import AnsibleModule
import os
from json import JSONDecodeError


def run_module():
    module_args = dict(
        src=dict(type="str", required=True),
        backend=dict(
            type="str", required=False, default="ssh", choices=["ssh", "winrm"]
        ),
        host=dict(type="str", required=False),
        username=dict(type="str", required=False),
        password=dict(type="str", required=False, no_log=True),
        privkey=dict(type="str", required=False, no_log=True),
        binary_path=dict(type="str", required=False),
        controls=dict(type="list", required=False, elements="str"),
    )

    result = dict(changed=False, tests=[])

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    if module.check_mode:
        module.exit_json(**result)

    src = module.params["src"]
    backend = module.params["backend"]
    host = module.params["host"]
    username = module.params["username"]
    password = module.params["password"]
    privkey = module.params["privkey"]
    bin_path = module.params.get("binary_path")

    if bin_path is not None:
        run_command = bin_path
    else:
        run_command = module.get_bin_path("inspec", required=True)

    controls = module.params.get("controls")

    # if no controls are defined, use a regex to match all controls
    if not controls:
        controls = "/.*/"
    else:
        controls = " ".join(map(str, controls))

    try:
        if not os.path.exists(src):
            module.fail_json(msg=f"Could not find file or directory at: {src}")

        if not host:
            command = (
                f"{run_command} exec {src} --controls {controls} --reporter json-min"
            )
        else:
            if not username:
                module.fail_json(
                    msg="username must be defined to run on a remote target!"
                )
            if not os.environ.get("SSH_AUTH_SOCK") and not password and not privkey:
                module.fail_json(
                    msg="password or privkey must be defined to run on a remote target! Alternatively, you can use SSH_AUTH_SOCK."
                )

            if os.environ.get("SSH_AUTH_SOCK"):
                command = "{run_command} exec {src} -b {backend} --host {host} --user {username} --controls {controls} --reporter json-min"
            elif privkey:
                command = "{run_command} exec {src} -b {backend} --host {host} --user {username} -i {privkey} --reporter json-min"
            else:
                command = "{run_command} exec {src} -b {backend} --host {host} --user {username} --password {password} --controls {controls} --reporter json-min"

        rc, stdout, stderr = module.run_command(command)

        if stderr:
            # if 'cannot execute without accepting the license' in inspec_result.stderr:
            if "cannot execute without accepting the license" in stderr:
                module.fail_json(
                    msg="This module requires the Inspec license to be accepted."
                )
            # elif "Don't understand inspec profile" in inspec_result.stderr:
            elif "Don't understand inspec profile" in stderr:
                module.fail_json(msg="Inspec was unable to read the profile structure.")
            # elif 'Could not fetch inspec profile' in inspec_result.stderr:
        elif "Could not fetch inspec profile" in stderr:
            module.fail_json(msg="Inspec was unable to read that profile or test.")

        # result['tests'] = module.from_json(inspec_result.stdout)['controls']
        result["tests"] = module.from_json(stdout)["controls"]

        failed = False
        for test in result["tests"]:
            if test["status"] == "failed":
                failed = True
                break

        if failed:
            module.fail_json(msg="Some tests failed!", **result)
        else:
            module.exit_json(msg="All tests passed.", **result)
    except JSONDecodeError:
        # module.fail_json(msg = f'Inspec did not return correctly. The error was: {inspec_result.stderr}')
        module.fail_json(
            msg=f"Inspec did not return correctly. The error was: {stderr}"
        )
    except FileNotFoundError:
        module.fail_json(
            msg=f"This module requires inspec to be installed on the host machine. Searched here: {run_command}"
        )
    except Exception as error:
        module.fail_json(msg=f"Encountered an error: {error}", cmd=command)


def main():
    run_module()


if __name__ == "__main__":
    main()
