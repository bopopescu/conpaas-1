'''
Copyright (c) 2010-2012, Contrail consortium.
All rights reserved.

Redistribution and use in source and binary forms, 
with or without modification, are permitted provided
that the following conditions are met:

 1. Redistributions of source code must retain the
    above copyright notice, this list of conditions
    and the following disclaimer.
 2. Redistributions in binary form must reproduce
    the above copyright notice, this list of 
    conditions and the following disclaimer in the
    documentation and/or other materials provided
    with the distribution.
 3. Neither the name of the <ORGANIZATION> nor the
    names of its contributors may be used to endorse
    or promote products derived from this software 
    without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, 
BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.


Created on Jan 21, 2011

@author: ielhelw, aaasz
'''

import urlparse 
from string import Template

from libcloud.types import Provider, NodeState
from libcloud.providers import get_driver
from libcloud.base import NodeImage

import libcloud.security
libcloud.security.VERIFY_SSL_CERT = False

from .base import Cloud

class OpenNebulaCloud(Cloud):

    def __init__(self, cloud_name, iaas_config):
        Cloud.__init__(self, cloud_name)
      
        self.connected = False
        self.cx_template = None
 
        # required parameters to describe this cloud
        cloud_params = ['URL', 'USER', 'PASSWORD', \
                        'IMAGE_ID', 'INST_TYPE',   \
                        'NET_ID', 'NET_GATEWAY',   \
                        'NET_NAMESERVER']

        for field in cloud_params:
            if not iaas_config.has_option(cloud_name, field)\
            or iaas_config.get(cloud_name, field) == '':
                raise Exception('Missing opennebula config param %s for %s' % \
                                                          (field, cloud_name))

        def _get(param):
            return iaas_config.get(cloud_name, param)

        self.url = _get('URL')
        self.user = _get('USER')
        self.passwd = _get('PASSWORD')
        self.img_id = _get('IMAGE_ID')
        #self.inst_types = _get('INST_TYPE')
        # choose the first inst_type by default
        #self.inst_type = self.inst_types[0]
        self.inst_type = _get('INST_TYPE')
        self.net_id = _get('NET_ID')
        self.net_gw = _get('NET_GATEWAY')
        self.net_ns = _get('NET_NAMESERVER')

        self.cpu = None
        self.mem = None

    def get_cloud_type(self):
      return 'opennebula'
 
    # connect to opennebula cloud 
    def _connect(self):
      parsed = urlparse.urlparse(self.url)
      ONDriver = get_driver(Provider.OPENNEBULA)
      self.driver = ONDriver(self.user,            \
                             secret = self.passwd,   \
                             secure = (parsed.scheme == 'https'), \
                             host = parsed.hostname,              \
                             port = parsed.port)
      self.connected = True

    # set the context template (i.e. without replacing anythong in it)
    def set_context_template(self, cx):
        self.cx_template = cx
        self.cx = cx.encode('hex')

    def get_context_template(self):
        return self.cx_template

    # set some VM specific parameters (TODO: what else?)
    def config(self, config_params={}, context=None):
        '''Sets some configuration parameters (Overrides the default ones).

           @keyword    inst_type:   Id of the node type of this driver (optional)
           @type       inst_type:   int

           @keyword    cpu:   Number of cpus for the VM. (optional)
           @type       cpu:   int

           @keyword    memory:  Quantity of RAM. (optional)
           @type       memory:  int

           @param      context: The context file

        '''

        if 'inst_type' in config_params:  
            self.inst_type = config_params['inst_type']

        if 'cpu' in config_params:  
            self.cpu = config_params['cpu']

        if 'mem' in config_params:  
            self.mem = config_params['mem']

        if context != None:
            self.cx = context.encode('hex')

    def list_vms(self):
        nodes = self.driver.list_nodes()
        vms = {}
        for i in nodes:
            vms[i.id] = {'id': i.id, \
                         'state': i.state, \
                         'name': i.name, \
                         'ip': i.public_ip[0]}
        return vms

    def list_instace_types(self):
        return self.inst_types

    def new_instances(self, count):
        '''Asks the provider for new instances.

           @param    count:   Id of the node type of this driver (optional)
       
        '''
        if self.connected == False:
            self._connect() 

        kwargs = {}
    
        # 'NAME'
        kwargs['name'] = 'conpaas'

        # 'INSTANCE_TYPE'
        kwargs['size'] = [ i for i in self.driver.list_sizes() \
                                 if i.id == self.inst_type ][0]

        # 'CPU'
        if self.cpu != None:
            kwargs['cpu'] = self.cpu

        # 'MEM'
        if self.mem != None:
            kwargs['mem'] = self.mem

        # 'DISK'
        kwargs['image'] = NodeImage(self.img_id, '', None)

        # 'NIC'
        kwargs['network'] = self.net_id

        # 'CONTEXT'
        context = {}
        context['HOSTNAME'] = '$NAME'
        context['IP_PUBLIC'] = '$NIC[IP]'
        context['IP_GATEWAY'] = self.net_gw
        context['NAMESERVER'] = self.net_ns
        context['USERDATA'] = self.cx
        context['TARGET'] = 'sdb'
        kwargs['context'] = context
 
        nodes = []
        for _ in range(count):
            node = self.driver.create_node(**kwargs)
            nodes.append({'id': node.id,
                          'state': node.state,
                          'name': node.name,
                          'ip': node.public_ip[0]})
        return nodes

    def kill_instance(self, vm_id):
        '''Kill a VM instance.

           @param    vm_id:   Id of the VM
       
        '''
        if self.connected == False:
            raise Exception('Not connected to cloud')

        nodes = self.driver.list_nodes()
        for i in nodes:
            if i.id == vm_id:
                return self.driver.destroy_node(i)
        return False
