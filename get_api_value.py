#!/usr/bin/env python
import json
import sys
import socket
import os
import urllib2
import argparse
from pprint import pprint
from time import time

import yaml
from objectpath import Tree
from pyzabbix import ZabbixMetric, ZabbixSender

try:
    with open(os.path.dirname(__file__) + '/extenalscripts_common.yaml', 'r') as file_pointer:
        config = yaml.load(file_pointer)
        file_pointer.close()
    zabbix_server = config['zabbix_server']
    zabbix_server_port = config['zabbix_server_port']
except:
    zabbix_server = 'zabbix.aws.internal'
    zabbix_server_port = 10051

zbxs = {'server': zabbix_server,
        'port': zabbix_server_port}

base_path = os.path.dirname(os.path.abspath(__file__))
endpoints_path = base_path + '/endpoints.yaml'

STATUSES = {
    '-1': 'Not all data sended to zabbix',
    '-2': 'Count of API values > 1',
    '-3': 'Value is Null',
    '-4': 'Value does not exist',
    '-5': 'Zabbix server connection problem',
    '-6': 'Cant get endpoint',
    '-7': 'Zabbix request is empty',
}

with open(endpoints_path, 'r') as f:
    global endpoints
    endpoints = yaml.load(f)


def get_url(url, user, password):
    start_time = time()
    passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
    passman.add_password(None, url, user, password)
    auth_handler = urllib2.HTTPBasicAuthHandler(passman)
    opener = urllib2.build_opener(auth_handler)

    urllib2.install_opener(opener)
    time_delta = time() - start_time

    return json.load(urllib2.urlopen(url)), time_delta


def send_values(zbx, host, values):
    packet = []
    for item in values:
        packet.append(ZabbixMetric(host, item, values[item]))

    try:
        result = ZabbixSender(zabbix_server=zbx['server'], zabbix_port=zbx['port']).send(packet)
    except socket.gaierror:
        sys.exit('-5')

    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Script for getting fullhouse values')
    parser.add_argument("--user", action="store", help="REST API user")
    parser.add_argument("--password", action="store", help="REST API password")
    parser.add_argument("--app_host", action="store", help="REST API host")
    parser.add_argument("--app_port", action="store", help="REST API port")
    parser.add_argument("--conf", action="store", help="Name of conf")
    parser.add_argument("--app_name", action="store", help="application name")
    parser.add_argument("--param1", action="store", help="argument")

    args = parser.parse_args()

    zbx_values = {}
    app_name = args.app_name
    conf = args.conf
    param1 = args.param1
    endpoint = endpoints[conf]['path']
    values_name = endpoints[conf]['items']
    rest_host = str(args.app_host)
    rest_port = int(args.app_port)
    rest_user = str(args.user)
    rest_user_password = str(args.password)
    url = "http://" + str(rest_host) + ":" + str(rest_port) + str(endpoint)
    # params = {}
    try:
        rest_result, time_delta = get_url(url, rest_user, rest_user_password)
    except Exception as err:
        sys.exit('-6')

    for key in values_name:
        tree = Tree(rest_result)
        path = str(values_name[key])
        path = path.format(param1)
        value = tree.execute(path)
        # pprint(rest_result)
        if value is None:
            sys.exit('-3')

        if isinstance(value, (unicode, int, float)):
            value = str(value)

        if not isinstance(value, str):
            value = list(value)
            if len(value) > 1:
                sys.exit('-2')
            elif len(value) < 1:
                print key
                sys.exit('-4')

            value = value[0]
        zbx_values.update({app_name + '.' + key: value})
    # zbx_values.update({})
    zbx_result = send_values(zbxs, rest_host, zbx_values)

    if zbx_result.failed > 0:
        pprint(zbx_values)
        sys.exit('-1')
    if zbx_result.processed == 0:
        pprint(zbx_values)
        sys.exit('-7')

    print(0)