#!/usr/bin/env python3
#
# Copyright (C) 2021 VyOS maintainers and contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 or later as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import re

from sys import exit

from vyos.config import Config
from vyos.configdict import dict_merge
from vyos.firewall import find_nftables_rule
from vyos.firewall import remove_nftables_rule
from vyos.util import cmd
from vyos.util import run
from vyos.util import process_named_running
from vyos.util import dict_search
from vyos.template import render
from vyos.xml import defaults
from vyos import ConfigError
from vyos import airbag
airbag.enable()

conntrack_config = r'/etc/modprobe.d/vyatta_nf_conntrack.conf'
sysctl_file = r'/run/sysctl/10-vyos-conntrack.conf'

# Every ALG (Application Layer Gateway) consists of either a Kernel Object
# also called a Kernel Module/Driver or some rules present in iptables
module_map = {
    'ftp' : {
        'ko' : ['nf_nat_ftp', 'nf_conntrack_ftp'],
    },
    'h323' : {
        'ko' : ['nf_nat_h323', 'nf_conntrack_h323'],
    },
    'nfs' : {
        'nftables' : ['ct helper set "rpc_tcp" tcp dport "{111}" return',
                      'ct helper set "rpc_udp" udp dport "{111}" return']
    },
    'pptp' : {
        'ko' : ['nf_nat_pptp', 'nf_conntrack_pptp'],
     },
    'sip' : {
        'ko' : ['nf_nat_sip', 'nf_conntrack_sip'],
     },
    'sqlnet' : {
        'nftables' : ['ct helper set "tns_tcp" tcp dport "{1521,1525,1536}" return']
    },
    'tftp' : {
        'ko' : ['nf_nat_tftp', 'nf_conntrack_tftp'],
     },
}

def resync_conntrackd():
    tmp = run('/usr/libexec/vyos/conf_mode/conntrack_sync.py')
    if tmp > 0:
        print('ERROR: error restarting conntrackd!')

def get_config(config=None):
    if config:
        conf = config
    else:
        conf = Config()
    base = ['system', 'conntrack']

    conntrack = conf.get_config_dict(base, key_mangling=('-', '_'),
                                     get_first_key=True)

    # We have gathered the dict representation of the CLI, but there are default
    # options which we need to update into the dictionary retrived.
    default_values = defaults(base)
    conntrack = dict_merge(default_values, conntrack)

    return conntrack

def verify(conntrack):
    return None

def generate(conntrack):
    render(conntrack_config, 'conntrack/vyos_nf_conntrack.conf.tmpl', conntrack)
    render(sysctl_file, 'conntrack/sysctl.conf.tmpl', conntrack)

    return None

def find_nftables_ct_rule(rule):
    helper_search = re.search('ct helper set "(\w+)"', rule)
    if helper_search:
        rule = helper_search[1]
    return find_nftables_rule('raw', 'VYOS_CT_HELPER', [rule])

def find_remove_rule(rule):
    handle = find_nftables_ct_rule(rule)
    if handle:
        remove_nftables_rule('raw', 'VYOS_CT_HELPER', handle)

def apply(conntrack):
    # Depending on the enable/disable state of the ALG (Application Layer Gateway)
    # modules we need to either insmod or rmmod the helpers.
    for module, module_config in module_map.items():
        if dict_search(f'modules.{module}', conntrack) is None:
            if 'ko' in module_config:
                for mod in module_config['ko']:
                    # Only remove the module if it's loaded
                    if os.path.exists(f'/sys/module/{mod}'):
                        cmd(f'rmmod {mod}')
            if 'nftables' in module_config:
                for rule in module_config['nftables']:
                    find_remove_rule(rule)
        else:
            if 'ko' in module_config:
                for mod in module_config['ko']:
                    cmd(f'modprobe {mod}')
            if 'nftables' in module_config:
                for rule in module_config['nftables']:
                    if not find_nftables_ct_rule(rule):
                        cmd(f'nft insert rule ip raw VYOS_CT_HELPER {rule}')

    if process_named_running('conntrackd'):
        # Reload conntrack-sync daemon to fetch new sysctl values
        resync_conntrackd()

    # We silently ignore all errors
    # See: https://bugzilla.redhat.com/show_bug.cgi?id=1264080
    cmd(f'sysctl -f {sysctl_file}')

    return None

if __name__ == '__main__':
    try:
        c = get_config()
        verify(c)
        generate(c)
        apply(c)
    except ConfigError as e:
        print(e)
        exit(1)
