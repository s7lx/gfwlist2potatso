#!/usr/bin/env python
# encoding: utf-8
from __future__ import absolute_import, unicode_literals

import urlparse
import logging
import urllib2
import json
import os
from collections import defaultdict

__all__ = ['main']


gfwlist_url = 'https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt'



def get_data_from_file(file_path):
    with open(file_path, 'rb') as f:
        builtin_rules = f.read()
        return builtin_rules


def decode_gfwlist(content):
    # decode base64 if have to
    try:
        if '.' in content:
            raise Exception()
        return content.decode('base64')
    except:
        return content


def get_hostname(something):
    try:
        # quite enough for GFW
        if not something.startswith('http:'):
            something = 'http://' + something
        r = urlparse.urlparse(something)
        return r.hostname
    except Exception as e:
        logging.error(e)
        return None


def add_domain_to_set(s, something):
    hostname = get_hostname(something)
    if hostname is not None:
        s.add(hostname)


def combine_lists(content):
    # gfwlist = get_data_from_file('resources/builtin.txt').splitlines(False)
    gfwlist = content.splitlines(False)
    return gfwlist


def parse_gfwlist(gfwlist):
    domains = set()
    for line in gfwlist:
        if line.find('.*') >= 0:
            continue
        elif line.find('*') >= 0:
            line = line.replace('*', '/')
        if line.startswith('||'):
            line = line.lstrip('||')
        elif line.startswith('|'):
            line = line.lstrip('|')
        elif line.startswith('.'):
            line = line.lstrip('.')
        if line.startswith('!'):
            continue
        elif line.startswith('['):
            continue
        elif line.startswith('@'):
            # ignore white list
            continue
        add_domain_to_set(domains, line)
    return domains


def reduce_domains(domains):
    # reduce 'www.google.com' to 'google.com'
    # remove invalid domains
    tld_content = get_data_from_file("resources/tld.txt")
    tlds = set(tld_content.splitlines(False))
    new_domains = set()
    for domain in domains:
        domain_parts = domain.split('.')
        last_root_domain = None
        for i in xrange(0, len(domain_parts)):
            root_domain = '.'.join(domain_parts[len(domain_parts) - i - 1:])
            if i == 0:
                if not tlds.__contains__(root_domain):
                    # root_domain is not a valid tld
                    break
            last_root_domain = root_domain
            if tlds.__contains__(root_domain):
                continue
            else:
                break
        if last_root_domain is not None:
            new_domains.add(last_root_domain)
    return new_domains


def generate_potatso(domains):
    # render the potatso.conf file
    potatso_conf_content = get_data_from_file('resources/potatso.tpl')
    rule = list()
    rule_tpl = "  - DOMAIN-SUFFIX,{domainstr},{proxy_name}"
    for domain in domains:
        rule.append(rule_tpl.format(
                domainstr=domain,
                proxy_name="Proxy"
            )
        )
    proxy = list()
    potatso_conf_content = potatso_conf_content.replace('__RULE__',
            "\n".join(rule))
    return potatso_conf_content.encode('utf-8')

def find_fast_ip(ips):
    table = defaultdict(list)
    for item in sum(ips.values(), []):
        table[item['ip']].append(item['delta'])
    table = map(
        lambda item: (item[0], sum(item[1]) / len(item[1])),
        table.items()
    )
    ip, rt = sorted(table, key=lambda item: item[1])[0]
    return ip

def write_file(fn,ct):
    ''' fn = file name
        ct = content '''

    fp=open(fn+"","w+")
    fp.write(ct)
    fp.close()
    return

def main():
    if os.path.isfile('gfwlist.txt') :
        with open("gfwlist.txt", 'rb') as f:
            content = f.read()
    else :
        print 'Downloading gfwlist from %s' % gfwlist_url
        content = urllib2.urlopen(gfwlist_url, timeout=10).read()
        write_file("gfwlist.txt",content)

    content = decode_gfwlist(content)
    gfwlist = combine_lists(content)
    domains = parse_gfwlist(gfwlist)
    domains = reduce_domains(domains)

    potatso_conf_content = generate_potatso(domains)
    potatso_conf_content = potatso_conf_content.decode('utf-8')



    with open("potatso.conf", 'wb') as f:
        f.write(potatso_conf_content.encode('utf-8'))


if __name__ == '__main__':
    main()
