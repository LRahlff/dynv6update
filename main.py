#!/usr/bin/env python3
import functools
import json
import operator
import socket
import os
import re
import time
from contextlib import closing

import dns.resolver
import requests


def get_ip_from_ipconfigwebsite(record):
    print('of, didnt got ip local')
    if record == 'AAAA':
        return [requests.get('https://ifconfig.co/ip').content.decode().split('\n')[0]]
    elif record == 'A':
        return [requests.get('https://api.ipify.org').content]
    else:
        return []


def get_namerserver_ips(nameservers, record):
    nameserver = []
    dnsresolver = dns.resolver.Resolver(configure=False)
    dnsresolver.nameservers = ['8.8.8.8']
    for ns in nameservers:
        try:
            answers = dnsresolver.resolve(ns, record)
            for rdata in answers:
                nameserver.append(rdata.to_text())
        except Exception as e:
            pass
            print(e)  # or pass
    return nameserver


# Thanks to akshaybabloo: https://gist.github.com/akshaybabloo/2a1df455e7643926739e934e910cbf2e
def get_records_of_nameserver(domain, nameservers, record=''):
    """
    Get all the records associated to domain parameter.
    :param domain:
    :return:
    """
    result = []
    dnsresolver = dns.resolver.Resolver(configure=False)
    ids = [
        'NONE',
        'A',
        'NS',
        'MD',
        'MF',
        'CNAME',
        'SOA',
        'MB',
        'MG',
        'MR',
        'NULL',
        'WKS',
        'PTR',
        'HINFO',
        'MINFO',
        'MX',
        'TXT',
        'RP',
        'AFSDB',
        'X25',
        'ISDN',
        'RT',
        'NSAP',
        'NSAP-PTR',
        'SIG',
        'KEY',
        'PX',
        'GPOS',
        'AAAA',
        'LOC',
        'NXT',
        'SRV',
        'NAPTR',
        'KX',
        'CERT',
        'A6',
        'DNAME',
        'OPT',
        'APL',
        'DS',
        'SSHFP',
        'IPSECKEY',
        'RRSIG',
        'NSEC',
        'DNSKEY',
        'DHCID',
        'NSEC3',
        'NSEC3PARAM',
        'TLSA',
        'HIP',
        'CDS',
        'CDNSKEY',
        'CSYNC',
        'SPF',
        'UNSPEC',
        'EUI48',
        'EUI64',
        'TKEY',
        'TSIG',
        'IXFR',
        'AXFR',
        'MAILB',
        'MAILA',
        'ANY',
        'URI',
        'CAA',
        'TA',
        'DLV',
    ]
    if record == '':
        for a in ids:
            data = []
            for ns in nameservers:
                dnsresolver.nameservers = [ns]
                try:
                    answers = dnsresolver.resolve(domain, a)
                    for rdata in answers:
                        data.append(rdata.to_text())

                except Exception as e:
                    pass
                    # print(e)
            result.append([a, data])

        return result
    else:
        for ns in nameservers:
            dnsresolver.nameservers = [ns]
            # try:
            answers = dnsresolver.resolve(domain, record)
            for rdata in answers:
                result.append(rdata.to_text())

        # except Exception as e:
        #     pass
        #     print(e)  # or pass
        return result


# Thanks to martinklepsch: https://gist.github.com/martinklepsch/375707/bb372a698412bca890506724ad26cc221cc569e3
def get_ipv4_from_FB(host='fritz.box', port=49000):
    # for getting the IP from the fritzbox
    http_body = '\r\n'.join((
        '<?xml version="1.0" encoding="utf-8"?>',
        '<s:Envelope s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">',
        '  <s:Body>',
        '    <u:GetExternalIPAddress xmlns:u="urn:schemas-upnp-org:service:WANIPConnection:1"/>',
        '  </s:Body>',
        '</s:Envelope>'))
    http_data = '\r\n'.join((
        'POST /igdupnp/control/WANIPConn1 HTTP/1.1',
        'Host: %s:%d' % (host, port),
        'SoapAction: urn:schemas-upnp-org:service:WANIPConnection:1#GetExternalIPAddress',
        'Content-Type: text/xml; charset="utf-8"',
        'Content-Length: %d' % len(http_body),
        '',
        http_body))
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.connect((host, port))
        s.send(http_data.encode())
        data = s.recv(1024)
        # print(data.decode())
        ipv4list = re.findall('(?<=<NewExternalIPAddress>)(.*?)(?=</NewExternalIPAddress>)', data.decode())
    return ipv4list


def get_ipv6_from_OS():
    # for linux users, maybe you have to update the regular expression
    # ipreponse = os.popen("ip address | grep 'scope global temporary dynamic'").read()
    ipreponse = os.popen("ip address | grep 'scope global dynamic mngtmpaddr'").read()
    return re.findall('(?<=inet6 )(.*?)(?=/64 scope)', ipreponse)


def get_zoneID(token, name=''):
    header = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
    r = requests.get('https://dynv6.com/api/v2/zones', headers=header)
    zones = []
    if (r.status_code) == 200:
        for zone in r.json():
            if zone['name'] == name:
                return zone['id']
            zones.append([zone['name'], zone['id']])
            pass
    elif (r.status_code) == 401:
        raise Exception('Wrong Key')
    else:
        raise Exception('Other problems')
    return zones


def get_zone_details(token, zoneID):
    header = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
    r = requests.get('https://dynv6.com/api/v2/zones', headers=header)
    if (r.status_code) == 200:
        header = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
        r = requests.get(f'https://dynv6.com/api/v2/zones/{zoneID}', headers=header)
        zone = r.json()
    elif (r.status_code) == 401:
        raise Exception('Wrong Key')
    else:
        raise Exception('Other problems')
    return [zone['id'], zone['name'], zone['ipv4address'], zone['ipv6prefix'], zone['createdAt'], zone['updatedAt']]


def get_records_API(token, zoneID, name='@init', type=''):
    header = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
    r = requests.get(f'https://dynv6.com/api/v2/zones/{zoneID}/records', headers=header)
    # print(r.json())
    if (r.status_code) == 200:
        records = []
        for i in r.json():
            # print(f"{i['id']}, name: {i['name']}, type: {i['type']}, data: {i['data']}")
            records.append([i['id'], i['name'], i['type'], i['data']])
            pass
        if name != '@init':
            records = list(filter(lambda x: x[1] == name, records))
        if type != '':
            records = list(filter(lambda x: x[2] == type, records))
    elif (r.status_code) == 401:
        raise Exception('Wrong Key')
    else:
        raise Exception('Other problems')
    return records


def delete_record(token, zoneID, recordID):
    header = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
    r = requests.delete(f'https://dynv6.com/api/v2/zones/{zoneID}/records/{recordID}', headers=header)
    return r


def update_record(token, zoneID, recordID, data, name='@'):
    if name == '@':
        pload = {"data": f'{data}'}
    else:
        pload = {"name": f'{name}', "data": f'{data}'}
    header = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
    r = requests.patch(f'https://dynv6.com/api/v2/zones/{zoneID}/records/{recordID}', json=pload, headers=header)
    return r.status_code


def update_zone(token, zoneID, dataA='init', dataAAAA='init'):
    if dataA == 'init' and not dataAAAA == 'init':
        pload = {'ipv6prefix': f'{dataAAAA}'}
    elif not dataA == 'init' and not dataAAAA == 'init':
        pload = {'ipv4address': f'{dataA}', 'ipv6prefix': f'{dataAAAA}'}
    elif not dataA == 'init' and dataAAAA == 'init':
        pload = {'ipv4address': f'{dataA}'}
    else:
        return 400
    header = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
    r = requests.patch(f'https://dynv6.com/api/v2/zones/{zoneID}', json=pload, headers=header)
    return r.status_code


def add_record(token, zoneID, name, data, type):
    if name == '' and type == 'A':
        status = add_record(token, zoneID, 'notreallyimportantonlyjustarecordforaveryshorttime', data, type)
        time.sleep(10)
        recordID = get_records_API(token, zoneID, 'notreallyimportantonlyjustarecordforaveryshorttime', 'A')
        status = update_record(token, zoneID, recordID[0][0], data, '')
        return status
    else:
        pload = {"name": f'{name}', "data": f'{data}', 'type': f'{type}'}
        header = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
        r = requests.post(f'https://dynv6.com/api/v2/zones/{zoneID}/records', json=pload, headers=header)
        return r.status_code


def hande_record(record):
    zone = record[0]
    sub = record[1]
    nameserver = record[2]
    recordtype = record[3]
    token = record[4]
    if sub == '':
        domain = zone
    else:
        domain = f'{sub}.{zone}'

    # get actual ip
    if recordtype == 'A':
        ipact = get_ipv4_from_FB()
        # if there is no ip comming from fritzbox get it from elsewhere
        if len(ipact) <= 0:
            pass
            ipact = get_ip_from_ipconfigwebsite(recordtype)
            print('didnt got the ip from OS, had to look online')
    elif recordtype == 'AAAA':
        ipact = get_ipv6_from_OS()
        # if there is no ip comming from os get it from elsewhere
        if len(ipact) <= 0:
            pass
            ipact = get_ip_from_ipconfigwebsite(recordtype)
            print('didnt got the ip from OS, had to look online')
    else:
        raise NotImplementedError('Andere Record Typen als A und AAAA sind noch nicht implementiert')
    # print(f'{domain}, {record}')

    # get ips from nameserver
    list_ips = []
    try:
        list_ips = get_records_of_nameserver(domain, nameserver, recordtype)
    except Exception as e:
        # print(e)
        pass

    update = False
    for ipold in list_ips:
        if ipold != ipact[0]:
            update = True
            break
    if update or len(list_ips) <= 0:
        # get zoneID
        zoneID = get_zoneID(token, zone)
        if (type(zoneID) == list):
            raise Exception(f'Zone {zone} is not accessable with that key')

        # get records
        oldrecords = get_records_API(token, zoneID, sub, recordtype)
        if len(oldrecords) > 1:
            for i in range(len(oldrecords) - 1):
                status = delete_record(token, zoneID, oldrecords[i][0])
        elif len(oldrecords) < 1 or len(list_ips) <= 0:
            status = add_record(token, zoneID, sub, ipact[0], recordtype)
            if status == 200:
                print(f'record added: {domain}, {ipact[0]}')
            else:
                print(
                    f'something went wrong while adding, status code not 200, but {status}: wanted: {domain}, {ipact[0]}')
        else:
            status = update_record(token, zoneID, oldrecords[0][0], ipact[0])
            if status == 200:
                print(f'record updated: {domain}, {ipact[0]}')
            else:
                print(
                    f'something went wrong while updating, status code not 200, but {status}: wanted: {domain}, {ipact[0]}')
    else:
        print(f'record is just fine: {domain}, {ipact[0]}')
        return True

    return False


if __name__ == '__main__':

    # Read key
    try:
        with open('my.cred', 'r') as file:
            data = file.read()
            cred = data.split('\n')
            file.close()
    except Exception as e:
        print(e)
        exit(1)

    finished = []
    allrecords = []

    # Get all records for update in a list
    try:
        with open('conf.json', 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(e)
        exit(1)
    updatelist = data['updatelist']
    updatenr = 0
    for update in updatelist:
        try:
            zone = update['zone']
            sub = update['sub']
            records = update['records']
            nameservers = update['nameserver']
            token = cred[updatenr]
            for record in records:
                nameserver = get_namerserver_ips(nameservers, record)
                allrecords.append([zone, sub, nameserver, record, token])
                finished.append(False)
        except Exception as e:
            print(f'Teil Nr {updatenr} enthält einen Fehler: {e}')
        updatenr += 1

    foldl = lambda func, acc, xs: functools.reduce(func, xs, acc)
    count = 0

    while (not foldl(operator.and_, True, finished) and count < 5):
        for recordnr in range(len(allrecords)):
            if not finished[recordnr]:
                # print(f'test {recordnr}: {allrecords[recordnr][0]}, {allrecords[recordnr][1]}, {allrecords[recordnr][2]}, {allrecords[recordnr][3]}')
                try:
                    finished[recordnr] = hande_record(allrecords[recordnr])
                except Exception as e:
                    print(e)
                time.sleep(10)

        count += 1
        if (not foldl(operator.and_, True, finished) and count < 5):
            time.sleep(120)

    exit()
