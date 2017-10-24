#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
set_priority.py: This script generates RESTCONF calls that can be sent to an Opendaylight controller
to manage QoS rules in an SDN network.
"""
import sys
import argparse
import logging
import requests
from requests.auth import HTTPBasicAuth
from lxml import etree

__author__ = "Pablo Couñago"
__copyright__ = "Copyright 2017, Gradiant"
__credits__ = ["Pablo Couñago", "Carlos Giraldo"]
__version__ = "0.1"
__email__ = "pcounhago@gradiant.org"

# Create and configure logging functionalities
logging.basicConfig(stream=sys.stdout,
                    level=logging.DEBUG,
                    format='%(asctime)s %(name)s %(levelname)s %(message)s')
LOG = logging.getLogger('set_priority')


class RestconfConnection(object):
    """
    The class RestconfConnection implements methods to generate RESTCONF calls
    to an Opendaylight controller configuring rules for QoS provisioning.

    :param controller_addr: String containing Opendaylight controller IP address
    :param controller_port: Integer with the port number where Opendaylight is listening
    for REST requests
    """
    def __init__(self,
                 controller_addr='127.0.0.1',
                 controller_port=8181):
        self.headers = {'Content-type': 'application/xml', 'Accept': 'application/xml'}
        self.auth = HTTPBasicAuth('admin', 'admin')
        self.controller_addr = controller_addr
        self.controller_port = controller_port

    def __generate_flow_id(self,
                           src_addr,
                           dst_addr):
        """
        Generates a string to be used as a flow identifier in the Opendaylight inventory.
        The returned string has the form \"src1dst3\" where the numbers are the least
        significant bytes from the source and destination IP addresses.

        :param src_addr: String containing the source IP address of the flow
        :param dst_addr: String containing the destination IP address of the flow
        :return: String containing the generated flow id.
        """
        src = src_addr[src_addr.rfind('.')+1:]
        dst = dst_addr[dst_addr.rfind('.')+1:]
        flow_id = 'src{0}dst{1}'.format(src, dst)
        return flow_id

    def get_nodes(self):
        """
        Retrieves the list of nodes registered in Opendaylight inventory.

        :return: List of strings corresponding to the node ids for the registered nodes.
        """
        url = 'http://'+self.controller_addr+':'+str(self.controller_port) + \
              '/restconf/operational/opendaylight-inventory:nodes/'

        response = requests.get(url, headers=self.headers, auth=self.auth)
        if response.status_code == 200 or response.status_code == 201:
            # Parse response XML response from the controller
            content = etree.fromstring(response.text)
            # Look for node ids using XPATH
            nodes = content.xpath('//ns:node/ns:id/text()',
                                  namespaces={'ns': 'urn:opendaylight:inventory'})
            return nodes
        else:
            LOG.error("Request failed with code %s", response.status_code)

    def assign_flow_to_queue(self,
                             node_id,
                             table_id,
                             src_addr,
                             dst_addr,
                             queue_id,
                             output_port,
                             priority=10,
                             idle_timeout=60,
                             hard_timeout=0):

        """
        Creates a new flow in the specified node and table. The generated rule assigns the
        flow to the specified queue and outputs the generated packets through the specified port.

        :param node_id: String containing the ID of the node where the route will be installed.
        :param table_id: Integer with the value of the table ID that will hold the rule.
        :param src_addr: String containing the source IP address that originates the flow.
        :param dst_addr: String containing the destination IP address that receives the flow.
        :param queue_id: Integer with the value of the ID for the queue that will handle packets
        matching the considered flow.
        :param output_port: Integer with the value of the port where the packet will be sent.
        :param priority: Integer with the value of the priority that will be applied to the
        generated rule
        :param idle_timeout: Integer with the amount of seconds that the rule must be in idle state
        before it is removed.
        :param hard_timeout: Integer with the amount of seconds that will be elapsed before the rule
        is removed.
        """
        # Generate flow id from the source and destination addresses
        flow_id = self.__generate_flow_id(src_addr, dst_addr)

        flow = etree.Element('flow', attrib={'xmlns': 'urn:opendaylight:flow:inventory'})

        id_element = etree.SubElement(flow, 'id')
        id_element.text = flow_id
        instructions = etree.SubElement(flow, 'instructions')
        instruction = etree.SubElement(instructions, 'instruction')
        etree.SubElement(instruction, 'order').text = str(0)
        apply_actions = etree.SubElement(instruction, 'apply-actions')

        # Create set queue action
        action = etree.SubElement(apply_actions, 'action')
        etree.SubElement(action, 'order').text = str(0)
        queue_action = etree.SubElement(action, 'set-queue-action')
        etree.SubElement(queue_action, 'queue-id').text = str(queue_id)

        # Create output action
        action = etree.SubElement(apply_actions, 'action')
        etree.SubElement(action, 'order').text = str(1)
        output_action = etree.SubElement(action, 'output-action')
        etree.SubElement(output_action, 'output-node-connector').text = str(output_port)
        etree.SubElement(output_action, 'max-length').text = str(65535)

        # Create match
        match = etree.SubElement(flow, 'match')
        eth_match = etree.SubElement(match, 'ethernet-match')
        eth_type = etree.SubElement(eth_match, 'ethernet-type')
        etree.SubElement(eth_type, 'type').text = str(2048)
        etree.SubElement(match, 'ipv4-source').text = src_addr + '/32'
        etree.SubElement(match, 'ipv4-destination').text = dst_addr + '/32'

        # Extra params
        etree.SubElement(flow, 'table_id').text = str(table_id)
        etree.SubElement(flow, 'hard-timeout').text = str(hard_timeout)
        etree.SubElement(flow, 'idle-timeout').text = str(idle_timeout)
        etree.SubElement(flow, 'priority').text = str(priority)
        etree.SubElement(flow, 'flow-name').text = flow_id
        etree.SubElement(flow, 'barrier').text = 'true'

        # Get XML string with declaration and encoding included
        data = etree.tostring(flow,
                              method='xml',
                              pretty_print=True,
                              xml_declaration=True,
                              encoding='UTF-8')

        url = 'http://'+self.controller_addr+':'+str(self.controller_port) + \
              '/restconf/config/opendaylight-inventory:nodes/node/' + node_id + \
              '/table/'+str(table_id)+'/flow/'+flow_id

        # Send PUT request using the previously generated XML payload
        response = requests.put(url,
                                data=data,
                                headers=self.headers,
                                auth=self.auth)

        # Verify the response status code
        if response.status_code != 200 and response.status_code != 201:
            LOG.error("Request failed with code '%s'", response.status_code)

    def remove_flow(self,
                    node_id,
                    table_id,
                    src_addr,
                    dst_addr,):
        """
        Removes a flow rule previously installed in the specified node and table.

        :param node_id: String containing the ID of the node where the route will be installed.
        :param table_id: Integer with the value of the table ID that will hold the rule.
        :param src_addr: String containing the source IP address that originates the flow.
        :param dst_addr: String containing the destination IP address that receives the flow.
        """
        # Generate flow id from the source and destination addresses
        flow_id = self.__generate_flow_id(src_addr, dst_addr)

        url = 'http://'+self.controller_addr+':'+str(self.controller_port) + \
              '/restconf/config/opendaylight-inventory:nodes/node/'+node_id + \
              '/table/'+str(table_id)+'/flow/'+flow_id

        # Send the DELETE request
        response = requests.delete(url,
                                   headers=self.headers,
                                   auth=self.auth)

        # Verify the response status code
        if response.status_code != 200 and response.status_code != 201:
            LOG.error("Request failed with code '%s'", response.status_code)


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(description='Set flow priority.')
    PARSER.add_argument('src_addr',
                        type=str,
                        help='IP address where the flow is generated')
    PARSER.add_argument('dst_addr',
                        type=str,
                        help='IP address where the flow is received')
    PARSER.add_argument('priority',
                        type=str,
                        help='Flow priority. Accepted values are "hi" and "lo"')

    ARGS = PARSER.parse_args()

    # Create RstconfConnection instance with the default parameters
    CONNECTION = RestconfConnection()

    # Verify that Core2 node is detected by Opendaylight. Node ids are generated from node DPIDs
    # that can be modified in mininet.
    if 'openflow:2' in CONNECTION.get_nodes():
        if ARGS.priority == 'hi':
            # When the user sets hi priority the corresponding rule is added to the node
            CONNECTION.assign_flow_to_queue(node_id='openflow:2',
                                            table_id=0,
                                            src_addr=ARGS.src_addr,
                                            dst_addr=ARGS.dst_addr,
                                            queue_id=1,
                                            output_port=2)
        elif ARGS.priority == 'lo':
            # When the user sets lo priority the corresponding rule is removed from the node
            CONNECTION.remove_flow(node_id='openflow:2',
                                   table_id=0,
                                   src_addr=sys.argv[1],
                                   dst_addr=sys.argv[2])
        else:
            LOG.error('Invalid priority specified. Valid priority values are "hi" and "lo"')
            quit()
    else:
        LOG.error('Node "Core2" not found')
        quit()
