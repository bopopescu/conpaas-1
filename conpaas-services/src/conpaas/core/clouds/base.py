# -*- coding: utf-8 -*-

"""
    conpaas.core.clouds.base
    ========================

    ConPaaS core: cloud-independent IaaS code.

    :copyright: (C) 2010-2013 by Contrail Consortium.
"""

from conpaas.core.node import ServiceNode
from conpaas.core.log import create_logger

class Cloud:
    ''' Abstract Cloud '''

    def __init__(self, cloud_name):
        #TODO: it shouldn't be cloud_name == config file section name
        self.cloud_name = cloud_name
        self.connected = False
        self.driver = None
        self.cx_template = None
        self.cx = None
        self.logger = create_logger(__name__)

    def get_cloud_name(self):
        return self.cloud_name

    def _check_cloud_params(self, iaas_config, cloud_params=[]):
        """Check for missing or empty parameters in iaas_config"""
        error_template = '%s config param %s for %s'

        for field in cloud_params:
            if not iaas_config.has_option(self.cloud_name, field):
                raise Exception('Missing ' + error_template % (
                    self.get_cloud_type(), field, self.cloud_name
                ))

            if iaas_config.get(self.cloud_name, field) == '':
                raise Exception('Empty ' + error_template % (
                    self.get_cloud_type(), field, self.cloud_name
                ))

        return None

    def _connect(self):
        '''
        _connect is the method used to set the driver and connect to the cloud

        '''
        raise NotImplementedError(
            '_connect not implemented for this cloud driver')

    def get_cloud_type(self):
        raise NotImplementedError(
            'get_cloud_type not implemented for this cloud driver')

    def get_context_template(self):
        return self.cx_template

    def set_context_template(self, cx):
        """
        Set the context template (i.e. without replacing anything in it)
        """
        self.cx_template = cx
        self.cx = cx

    def config(self, config_params, context):
        raise NotImplementedError(
            'config not implemented for this cloud driver')

    def list_vms(self, has_private_ip=True):
        '''
        lists the service nodes in the cloud instances

        @return vms: List[ServiceNode]

        '''
        self.logger.debug('list_vms(has_private_ip=%s)' % has_private_ip)

        if self.connected is False:
            self._connect()
        return [serviceNode for serviceNode in
                self._create_service_nodes(self.driver.list_nodes())]

    def new_instances(self, count, name='conpaas', inst_type=None):
        raise NotImplementedError(
            'new_instances not implemented for this cloud driver')

    def _create_service_nodes(self, instances, has_private_ip=True):
        '''
        creates a list of ServiceNode

        @param  instances: List of nodes provide by the driver or a single node
        @type   instances: L{libcloud.compute.Node} or C{libcloud.compute.Node}

        @param  has_private_ip: some instances only need the public ip
        @type   has_private_ip: C{bool}

        '''
        if type(instances) is list:
            return [ self.__create_one_service_node(node, has_private_ip)
                    for node in instances ]

        return self.__create_one_service_node(instances, has_private_ip)

    def __create_one_service_node(self, instance, has_private_ip=True):
        '''
        creates a single ServiceNode

        @param  instance: node provided by the driver
        @type   instance: C{libcloud.compute.Node}

        @param  has_private_ip: some instances only need the public ip
        @type   has_private_ip: C{bool}

        '''
        ip, private_ip = self.__get_ips(instance, has_private_ip)
        return ServiceNode(instance.id, ip, private_ip, self.cloud_name)

    def __get_ips(self, instance, has_private_ip):
        if instance.public_ips:
            ip = instance.public_ips[0]
        else:
            ip = ''
        if has_private_ip:
            if instance.private_ips:
                private_ip = instance.private_ips[0]
            else:
                private_ip = ''
        else:
            private_ip = ip

        if hasattr(ip, 'address'):
            ip = ip.address

        if hasattr(private_ip, 'address'):
            private_ip = private_ip.address

        return ip, private_ip

    def kill_instance(self, node):
        '''Kill a VM instance.

           @param node: A ServiceNode instance, where node.id is the
                        vm_id
        '''
        self.logger.debug('kill_instance(node=%s)' % node)

        if self.connected is False:
            self._connect()
        return self.driver.destroy_node(node.as_libcloud_node())
