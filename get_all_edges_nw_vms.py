#!/usr/bin/env python3

"""
===================================================================================================
   Author:          Petr Nemec
   Description:     It retrieves adat about Organizations, VDCs, Edges, Org Networks,
                    VMs and their network properties (MAC & IP addresses)
   Date:            2018-01-14
===================================================================================================
"""

from pyvcloud.vcd.client import BasicLoginCredentials
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import Client
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.vdc import VDC
from pyvcloud.vcd.vm import VM
from pyvcloud.vcd.vapp import VApp
from prettytable import PrettyTable
from termcolor import cprint
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Update with valid vCD's URL or IP address
client = Client('10.20.30.40',
                api_version='29.0',
                verify_ssl_certs=False,
                log_file='pyvcloud.log',
                log_requests=True,
                log_headers=True,
                log_bodies=True)

# Update with valid administrator's credentials
client.set_credentials(BasicLoginCredentials('administrator', 'SYSTEM', 'password'))


# print(client.is_sysadmin())

# Retrieve the list of all organizations ----------------------------------------------------------
orgs = client.get_org_list()

# Iterate over Organizations - 1st GO to print table of Organizations
orgtable = PrettyTable(["Organization name", "href"])
for o in orgs.Org:
    # print(o.attrib['name'])
    # print(o.get('name'))
    # print(o.get('href'))
    orgtable.add_row([o.get('name'), o.get('href')])
cprint('Print all Organizations', 'yellow')
print(orgtable)

# Iterate over Organizations - 2nd GO to retrieve data about VDCs ---------------------------------
for o in orgs.Org:
    cprint('\nOrganization ' + o.attrib['name'] + ' ###################################################################'
                                                  '############################################', 'green')
    # print(o.get('name'))

    # Create an Instance of Org by specifying org's href
    org = Org(client, href=(o.attrib['href']))

    cprint("\nList of all VDCs in the Organization {}".format(o.get('name')), 'yellow')
    vdclist = org.list_vdcs()
    vdctable = PrettyTable(["Organization", "VDC name", "VDC href"])
    for i in range(len(vdclist)):
        vdctable.add_row([o.get('name'), vdclist[i]['name'], vdclist[i]['href']])
    print(vdctable)

    # Iterate over VDCs to retrieve data about Edges, Org Networks, vAPPs and VMs
    for vdc in vdclist:
        # print("\nFetching VDC {}".format(vdc['name']))
        vdc_resource = org.get_vdc(vdc['name'])
        vdc_instance = VDC(client, resource=vdc_resource)

        cprint("\nList of all Tenant Edges in the VDC {}".format(vdc['name']), 'yellow')
        edgelist = vdc_instance.list_edge_gateways()
        edgetable = PrettyTable(["Organization", "VDC name", "Edge name", "Edge href"])
        for j in range(len(edgelist)):
            edgetable.add_row([o.get('name'), vdc['name'], edgelist[j]['name'], edgelist[j]['href']])
        print(edgetable)

        # Retrieve VDC Org Networks ---------------------------------------------------------------
        cprint("\nList of VDC Org Networks from VDC {}".format(vdc['name']), 'yellow')
        orgnets = vdc_instance.list_orgvdc_network_resources()
        orgnettable = PrettyTable(["Organization", "VDC name", "Org Nw name", "Org Nw href"])
        for k in range(len(orgnets)):
            orgnettable.add_row([o.get('name'), vdc['name'], orgnets[k].attrib['name'], orgnets[k].attrib['href']])
        print(orgnettable)

        # Retrieve all vApps from vCD -------------------------------------------------------------
        vapps_list = vdc_instance.list_resources()
        for vapp in vapps_list:
            # Exclude VM Templates from Catalogs
            # There're two types vApp+xml or vAppTemplate+xml
            if vapp.get('type').split('.')[-1] == 'vApp+xml':
                # print("\nFetching vAPP {}".format(vapp['name']))
                vapp_resource = vdc_instance.get_vapp(vapp['name'])
                vapp_instance = VApp(client, resource=vapp_resource)

                vapptable = PrettyTable(["VAPP name", "VM name", "VM href", "Connection", "MAC", "IP", "Primary"])

                'application/vnd.vmware.vcloud.vAppTemplate+xml'

                vms = vapp_resource.xpath('//vcloud:VApp/vcloud:Children/vcloud:Vm', namespaces=NSMAP)

                for vm in vms:
                    vm_instance = VM(client, resource=vm)
                    items = vm.xpath('//ovf:VirtualHardwareSection/ovf:Item', namespaces={'ovf': NSMAP['ovf']})

                    # Resource types https://opennodecloud.com/howto/2013/12/25/howto-ON-ovf-reference.html
                    # Open Virtualization Format (OVF), 10 - Ethernet Adapter
                    for item in items:
                        found_vnic = False
                        # If a vnic is found
                        if item['{' + NSMAP['rasd'] + '}ResourceType'] == 10:  # Ethernet Adapter
                            found_vnic = True
                            # print(item['{' + NSMAP['rasd'] + '}Address'])
                            # print(item['{' + NSMAP['rasd'] + '}Connection'])
                            connection = item['{' + NSMAP['rasd'] + '}Connection']
                            # print(connection.attrib['{' + NSMAP['vcloud'] + '}ipAddressingMode'])
                            # print(connection.attrib['{' + NSMAP['vcloud'] + '}ipAddress'])
                            # print(connection.attrib['{' + NSMAP['vcloud'] + '}primaryNetworkConnection'])

                            vapptable.add_row([vapp['name'],
                                               vm.attrib['name'],
                                               vm_instance.href.split('/')[-1],
                                               item['{' + NSMAP['rasd'] + '}Connection'],
                                               item['{' + NSMAP['rasd'] + '}Address'],
                                               connection.attrib['{' + NSMAP['vcloud'] + '}ipAddress'],
                                               connection.attrib['{' + NSMAP['vcloud'] + '}primaryNetworkConnection']])

                cprint("\nList of VMs nested in a VAPP defined in the VDC {}".format(vdc['name']), 'yellow')
                print(vapptable)

# Log out.
print("Logging out")
client.logout()
