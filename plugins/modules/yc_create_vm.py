#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: my_test

short_description: This is my test module

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"

description: This is my longer description explaining my test module.

options:
    name:
        description: This is the message to send to the test module.
        required: true
        type: str
    new:
        description:
            - Control to demo if the result of this module is changed or not.
            - Parameter description can be a list as well.
        required: false
        type: bool
# Specify this value according to your collection
# in format of namespace.collection.doc_fragment_name
extends_documentation_fragment:
    - my_namespace.my_collection.my_doc_fragment_name

author:
    - Your Name (@yourGitHubHandle)
'''

EXAMPLES = r'''
# Pass in a message
- name: Test with a message
  my_namespace.my_collection.my_test:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  my_namespace.my_collection.my_test:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  my_namespace.my_collection.my_test:
    name: fail me
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
original_message:
    description: The original name param that was passed in.
    type: str
    returned: always
    sample: 'hello world'
message:
    description: The output message that the test module generates.
    type: str
    returned: always
    sample: 'goodbye'
'''

import os, subprocess, json
from ansible.module_utils.basic import AnsibleModule


def check_dependency(method):
    if method == "cli":
        try:
            res = subprocess.run(["yc", "-v"], stdout=subprocess.PIPE, text=True).stdout
            return res
        except FileNotFoundError:
            os.system("curl -sSL https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash")
            res = check_dependency("cli")
            return "Installed: " + res
    if method == "rest":
        return 1


def yc_auth(method, token):
    if method == "cli":
        res = subprocess.run(["yc", "config", "set", "token", token], stdout=subprocess.PIPE, text=True).stdout
        if res == "":
            return "token set"
        else:
            return res
    if method == "rest":
        return 1

def create_vpc_network(method, folder_id, networkname, netdesc):
    if method == "cli":
        res = subprocess.run(["yc", "vpc", "network", "create", "--name", networkname, "--description", netdesc,
                             "--folder-id", folder_id], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True).stdout
        return res
    if method == "rest":
        return 1

def get_fact(method, in_cmd, fname, ftype):
    if method == "cli":
        resout = subprocess.run(in_cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True).stdout
        for net in json.loads(resout):
            if net["name"] == fname:
                rid = net[ftype]
        return rid

def create_vpc_subnet(method, subnetname, subdesc, network_id, zone, cidr, folder_id):
    if method == "cli":
        res = subprocess.run(["yc", "vpc", "subnet", "create", "--name", subnetname, "--description", subdesc,
                              "--network-id", network_id, "--zone", zone, "--range", cidr, "--folder-id", folder_id], stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True).stdout
        return res
    if method == "rest":
        return 1

def create_vm_instance(method, vm_name, zone, subnetname, imgfamily, disksize, ram, cores, frac, pathkey, folder_id):
    if method == "cli":
        res = subprocess.run(["yc", "compute", "instance", "create", "--name", vm_name, "--zone", zone,
                              "--network-interface", "subnet-name={},nat-ip-version=ipv4".format(subnetname),
                              "--create-boot-disk", "image-folder-id=standard-images,image-family={},size={}".format(imgfamily, disksize),
                              "--memory", ram, "--cores", cores, "--core-fraction", frac,
                              "--ssh-key", pathkey, "--folder-id", folder_id], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True).stdout
        return res

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        step=dict(type='str', required=True),
        folder_id=dict(type='str', required=False, default=""),
        token=dict(type='str', required=False, default=""),
        cloud_id=dict(type='str', required=False, default=""),
        vm_name=dict(type='str', required=False, default="vm1"),
        method=dict(type='str', required=False, default="cli"),
        networkname=dict(type='str', required=False, default="learning"),
        subnetname=dict(type='str', required=False, default="learning-subnet"),
        subdesc=dict(type='str', required=False, default="learning subnetwork"),
        netdesc=dict(type='str', required=False, default="learning network"),
        zone=dict(type='str', required=False, default="ru-central1-a"),
        cidr=dict(type='str', required=False, default="10.0.1.0/24"),
        imgfamily=dict(type='str', required=False, default="centos-7"),
        disksize=dict(type='str', required=False, default="20GB"),
        ram=dict(type='str', required=False, default="2GB"),
        cores=dict(type='str', required=False, default="2"),
        frac=dict(type='str', required=False, default="20"),
        pathkey=dict(type='str', required=False, default="/home/vagrant/.ssh/id_rsa.pub")

    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # for python 3.9
    if  module.params['step'] == "auth":
            res = check_dependency(module.params['method'])
            auth = yc_auth(module.params['method'], module.params['token'])
            result['message'] = '['+res+', '+auth+']'
            if "Installed" in res:
                result['changed'] = True
    elif module.params['step'] == "network":
            netname = create_vpc_network(module.params['method'], module.params['folder_id'],
                                         module.params['networkname'],  module.params['netdesc'])
            result['message'] = netname
            if not "AlreadyExists" in netname:
                result['changed'] = True
    elif module.params['step'] == "subnetwork":
            network_id = get_fact(module.params['method'],
                                "yc vpc network list --folder-id {} --format json".format(module.params['folder_id']),
                                module.params['networkname'], "id")

            subnet = create_vpc_subnet(module.params['method'], module.params['subnetname'], module.params['subdesc'],
                                       network_id, module.params['zone'], module.params['cidr'], module.params['folder_id'])

            result['message'] = subnet
            if not "ERROR" in subnet:
                result['changed'] = True
    elif module.params['step'] == "vm":
            vm = create_vm_instance(module.params['method'], module.params['vm_name'], module.params['zone'],
                                    module.params['subnetname'], module.params['imgfamily'], module.params['disksize'],
                                    module.params['ram'], module.params['cores'], module.params['frac'],
                                    module.params['pathkey'], module.params['folder_id'])

            vm_ip = get_fact(module.params['method'],
                                  "yc compute instance list --folder-id {} --format json".format(module.params['folder_id']),
                                  module.params['vm_name'], "network_interfaces")

            result['message'] = vm_ip
            if not "AlreadyExists" in vm:
                result['changed'] = True

    # match module.params['step']:
    #     case "auth":
    #         res = check_dependency(module.params['method'])
    #         auth = yc_auth(module.params['method'], module.params['token'])
    #         result['message'] = '['+res+', '+auth+']'
    #         if "Installed" in res:
    #             result['changed'] = True
    #     case "network":
    #         netname = create_vpc_network(module.params['method'], module.params['folder_id'],
    #                                      module.params['networkname'],  module.params['netdesc'])
    #         result['message'] = netname
    #         if not "AlreadyExists" in netname:
    #             result['changed'] = True
    #     case "subnetwork":
    #         network_id = get_fact(module.params['method'],
    #                             "yc vpc network list --folder-id {} --format json".format(module.params['folder_id']),
    #                             module.params['networkname'], "id")
    #
    #         subnet = create_vpc_subnet(module.params['method'], module.params['subnetname'], module.params['subdesc'],
    #                                    network_id, module.params['zone'], module.params['cidr'], module.params['folder_id'])
    #
    #         result['message'] = subnet
    #         if not "ERROR" in subnet:
    #             result['changed'] = True
    #     case "vm":
    #         vm = create_vm_instance(module.params['method'], module.params['vm_name'], module.params['zone'],
    #                                 module.params['subnetname'], module.params['imgfamily'], module.params['disksize'],
    #                                 module.params['ram'], module.params['cores'], module.params['frac'],
    #                                 module.params['pathkey'], module.params['folder_id'])
    #
    #         vm_ip = get_fact(module.params['method'],
    #                               "yc compute instance list --folder-id {} --format json".format(module.params['folder_id']),
    #                               module.params['vm_name'], "network_interfaces")
    #
    #         result['message'] = vm_ip
    #         if not "AlreadyExists" in vm:
    #             result['changed'] = True


    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    # result['original_message'] = module.params['name']


    # use whatever logic you need to determine whether or not this module
    # made any modifications to your target
    # if module.params['new']:
    #     result['changed'] = True

    # during the execution of the module, if there is an exception or a
    # conditional state that effectively causes a failure, run
    # AnsibleModule.fail_json() to pass in the message and the result
    # if module.params['name'] == 'fail me':
    #     module.fail_json(msg='You requested this to fail', **result)

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()