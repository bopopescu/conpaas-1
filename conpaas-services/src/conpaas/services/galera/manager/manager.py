# -*- coding: utf-8 -*-

"""
    :copyright: (C) 2010-2013 by Contrail Consortium.
"""

from threading import Thread
import os, tempfile
import string
from random import choice

from conpaas.core.https.server import HttpJsonResponse, HttpErrorResponse, \
                                      FileUploadField
from conpaas.core.expose import expose
from conpaas.core.manager import BaseManager, ManagerException

from conpaas.services.galera.agent import client
from conpaas.services.galera.manager.config import Configuration, E_ARGS_INVALID, \
                              E_ARGS_MISSING, E_STATE_ERROR, E_ARGS_UNEXPECTED

class GaleraManager(BaseManager):
    """
    Initializes :py:attr:`config` using Config and sets :py:attr:`state` to :py:attr:`S_INIT`

    :param conf: Configuration file.
    :type conf: str
    :type conf: boolean

    """

    # TODO: move this in core !!!!
    S_INIT = 'INIT'
    S_PROLOGUE = 'PROLOGUE'
    S_RUNNING = 'RUNNING'
    S_ADAPTING = 'ADAPTING'
    S_EPILOGUE = 'EPILOGUE'
    S_STOPPED = 'STOPPED'
    S_ERROR = 'ERROR'

    def __init__(self, conf, **kwargs):
        BaseManager.__init__(self, conf)

        self.logger.debug("Entering GaleraServerManager initialization")
        self.controller.generate_context('galera')
        self.controller.config_clouds({ "mem" : "512", "cpu" : "1" })
        self.state = self.S_INIT
        self.config = Configuration(conf)
        self.logger.debug("Leaving GaleraServer initialization")

        # The unique id that is used to start the main/subordinate
        self.id = 0

    @expose('POST')
    def startup(self, kwargs):
        ''' Starts the service - it will start and configure a Galera main '''
        self.logger.debug("Entering GaleraServerManager startup")

        if self.state != self.S_INIT and self.state != self.S_STOPPED:
            return HttpErrorResponse(ManagerException(E_STATE_ERROR).message)

        self.state = self.S_PROLOGUE
        Thread(target=self._do_startup, kwargs=kwargs).start()
        return HttpJsonResponse({'state': self.S_PROLOGUE})

    def _do_startup(self, cloud):
        ''' Starts up the service. The first node will be the MYSQL main.
            The next nodes will be subordinates to this main. '''

        startCloud = self._init_cloud(cloud)
        #TODO: Get any existing configuration (if the service was stopped and restarted)
        self.logger.debug('do_startup: Going to request one new node')

        # Generate a password for root
        # TODO: send a username?
        self.root_pass = ''.join([choice(string.letters + string.digits) for i in range(10)])
        self.controller.update_context(dict(mysql_username='mysqldb', \
                                mysql_password=self.root_pass),cloud=startCloud)
        try:
            node_instances = self.controller.create_nodes(1,
                                                    client.check_agent_process,
                                                    self.config.AGENT_PORT,
                                                    startCloud)
            self._start_main(node_instances)
            self.config.addMySQLServiceNodes(nodes=node_instances, isMain=True)
        except:
            self.logger.exception('do_startup: Failed to request a new node on cloud %s' % cloud)
            self.state = self.S_STOPPED
            return
        self.state = self.S_RUNNING

    def _start_main(self, nodes):
        for serviceNode in nodes:
            try:
                client.create_main(serviceNode.ip, self.config.AGENT_PORT,
                                    self._get_server_id())
            except client.AgentException:
                self.logger.exception('Failed to start Galera Main at node %s' % str(serviceNode))
                self.state = self.S_ERROR
                raise

    def _start_subordinate(self, nodes, main):
        subordinates = {}
        for serviceNode in nodes:
            subordinates[str(self._get_server_id())] = {'ip':serviceNode.ip,
                                                  'port':self.config.AGENT_PORT}
        try:
            self.logger.debug('create_subordinate for main.ip  = %s' % main)
            client.create_subordinate(main.ip,
                                self.config.AGENT_PORT, subordinates)
        except client.AgentException:
            self.logger.exception('Failed to start Galera Subordinate at node %s' % str(serviceNode))
            self.state = self.S_ERROR
            raise

    @expose('GET')
    def list_nodes(self, kwargs):
        """
        HTTP GET method.
        Uses :py:meth:`IaaSClient.listVMs()` to get list of
        all Service nodes. For each service node it gets it
        checks if it is in servers list. If some of them are missing
        they are removed from the list. Returns list of all service nodes.

        :returns: HttpJsonResponse - JSON response with the list of services
        :raises: HttpErrorResponse

        """
        if len(kwargs) != 0:
            return HttpErrorResponse(ManagerException(E_ARGS_UNEXPECTED, kwargs.keys()).message)

        return HttpJsonResponse({
            'mains': [ node.id for node in self.config.getMySQLmains() ],
            'subordinates': [ node.id for node in self.config.getMySQLsubordinates() ]
            })

    @expose('GET')
    def get_node_info(self, kwargs):
        """
        HTTP GET method. Gets info of a specific node.

        :param param: serviceNodeId is a VMID of an existing service node.
        :type param: str
        :returns: HttpJsonResponse - JSON response with details about the node.
        :raises: ManagerException

        """
        if 'serviceNodeId' not in kwargs:
            return HttpErrorResponse(ManagerException(E_ARGS_MISSING, 'serviceNodeId').message)
        serviceNodeId = kwargs.pop('serviceNodeId')
        if len(kwargs) != 0:
            return HttpErrorResponse(ManagerException(E_ARGS_UNEXPECTED, kwargs.keys()).message)
        if serviceNodeId not in self.config.serviceNodes:
            return HttpErrorResponse(ManagerException(E_ARGS_INVALID , \
                                                      "serviceNodeId" ,\
                                                      detail='Invalid "serviceNodeId"').message)
        serviceNode = self.config.getMySQLNode(serviceNodeId)
        return HttpJsonResponse({
            'serviceNode': {
                            'id': serviceNode.id,
                            'ip': serviceNode.ip,
                            'isMain': serviceNode.isMain,
                            'isSubordinate': serviceNode.isSubordinate
                            }
            })

    @expose('POST')
    def add_nodes(self, kwargs):
        """
        HTTP POST method. Creates new node and adds it to the list of existing nodes in the manager. Makes internal call to :py:meth:`createServiceNodeThread`.

        :param kwargs: number of nodes to add.
        :type param: str
        :returns: HttpJsonResponse - JSON response with details about the node.
        :raises: ManagerException

        """

        if self.state != self.S_RUNNING:
            return HttpErrorResponse('ERROR: Wrong state to add_nodes')
        if not 'subordinates' in kwargs:
            return HttpErrorResponse('ERROR: Required argument doesn\'t exist')
        if not isinstance(kwargs['subordinates'], int):
            return HttpErrorResponse('ERROR: Expected an integer value for "count"')
        count = int(kwargs.pop('subordinates'))
        self.state = self.S_ADAPTING
        Thread(target=self._do_add_nodes, args=[count, kwargs['cloud']]).start()
        return HttpJsonResponse()

    # TODO: also specify the main for which to add subordinates
    def _do_add_nodes(self, count, cloud):
        # Get the main
        mains = self.config.getMySQLmains()
        startCloud = self._init_cloud(cloud)
        # Configure the nodes as subordinates
        #TODO: modify this when multiple mains
        try:
            node_instances = self.controller.create_nodes(count,
                                           client.check_agent_process,
                                           self.config.AGENT_PORT, startCloud)
            for main in mains:
                self._start_subordinate(node_instances, main)
            self.config.addMySQLServiceNodes(nodes=node_instances, isSubordinate=True)
        except:
            self.logger.exception('_do_add_nodes: Could not start subordinate')
            self.state = self.S_ERROR
            return
        self.state = self.S_RUNNING

    def _get_server_id(self):
        self.id = self.id + 1
        return self.id

    @expose('GET')
    def get_service_performance(self, kwargs):
        ''' HTTP GET method. Placeholder for obtaining performance metrics.

        :param kwargs: Additional parameters.
        :type kwargs: dict
        :returns:  HttpJsonResponse -- returns metrics

        '''

        if len(kwargs) != 0:
            return HttpErrorResponse(ManagerException(E_ARGS_UNEXPECTED, kwargs.keys()).message)
        return HttpJsonResponse({
                'request_rate': 0,
                'error_rate': 0,
                'throughput': 0,
                'response_time': 0,
        })

    @expose('POST')
    def remove_nodes(self, kwargs):
        if self.state != self.S_RUNNING:
            self.logger.debug('Wrong state to remove nodes')
            return HttpErrorResponse('ERROR: Wrong state to remove_nodes')
        if not 'subordinates' in kwargs:
            return HttpErrorResponse('ERROR: Required argument doesn\'t exist')
        if not isinstance(kwargs['subordinates'], int):
            return HttpErrorResponse('ERROR: Expected an integer value for "count"')
        count = int(kwargs.pop('subordinates'))
        if count > len(self.config.getMySQLsubordinates()):
            return HttpErrorResponse('ERROR: Cannot remove so many nodes')
        self.state = self.S_ADAPTING
        Thread(target=self._do_remove_nodes, args=[count]).start()
        return HttpJsonResponse()

    def _do_remove_nodes(self, count):
        nodes = self.config.getMySQLsubordinates()[:count]
        self.controller.delete_nodes(nodes)
        self.config.remove_nodes(nodes)
        self.state = self.S_RUNNING
        return HttpJsonResponse()

    @expose('GET')
    def get_service_info(self, kwargs):
        if len(kwargs) != 0:
            return HttpErrorResponse('ERROR: Arguments unexpected')
        return HttpJsonResponse({'state': self.state, 'type': 'mysql'})

    @expose('POST')
    def shutdown(self, kwargs):
        """
        HTTP POST method. Shuts down the manager service.

        :returns: HttpJsonResponse - JSON response with details about the status of a manager node: . ManagerException if something went wrong.
        :raises: ManagerException

        """
        if len(kwargs) != 0:
            return HttpErrorResponse(ManagerException(E_ARGS_UNEXPECTED, kwargs.keys()).message)

        if self.state != self.S_RUNNING:
            return HttpErrorResponse(ManagerException(E_STATE_ERROR).message)

        self.state = self.S_EPILOGUE
        Thread(target=self._do_shutdown, args=[]).start()
        return HttpJsonResponse({'state': self.S_EPILOGUE})


    def _do_shutdown(self):
        ''' Shuts down the service. '''
        #self._stop_subordinates( config.getProxyServiceNodes())
        #self._stop_mains(config, config.getWebServiceNodes())
        self.controller.delete_nodes(self.config.serviceNodes.values())
        self.config.serviceNodes = {}
        self.state = self.S_STOPPED


    @expose('POST')
    def set_password(self, kwargs):
        self.logger.debug('Setting password')
        if self.state != self.S_RUNNING:
            self.logger.debug('Service not runnning')
            return HttpErrorResponse('ERROR: Service not running')
        if not 'user' in kwargs:
            return HttpErrorResponse('ERROR: Required argument \'user\' doesn\'t exist')
        if not 'password' in kwargs:
            return HttpErrorResponse('ERROR: Required argument \'password\' doesn\'t exist')

        # Get the main
        mains = self.config.getMySQLmains()

        #TODO: modify this when multiple mains
        try:
            for main in mains:
                client.set_password(main.ip, self.config.AGENT_PORT, kwargs['user'], kwargs['password'])
        except:
            self.logger.exception('set_password: Could not set password')
            self.state = self.S_ERROR
            return HttpErrorResponse('Failed to set password')
        else:
            return HttpJsonResponse()

    @expose('UPLOAD')
    def load_dump(self, kwargs):
        self.logger.debug('Uploading mysql dump')
        if 'mysqldump_file' not in kwargs:
            return HttpErrorResponse(ManagerException(ManagerException.E_ARGS_MISSING, \
                                                                     'mysqldump_file').message)
        mysqldump_file = kwargs.pop('mysqldump_file')
        if len(kwargs) != 0:
            return HttpErrorResponse(ManagerException(ManagerException.E_ARGS_UNEXPECTED, \
                                               detail='invalid number of arguments ').message)
        if not isinstance(mysqldump_file, FileUploadField):
            return HttpErrorResponse(ManagerException(ManagerException.E_ARGS_INVALID, \
                                               detail='mysqldump_file should be a file').message)
        fd, filename = tempfile.mkstemp(dir='/tmp')
        fd = os.fdopen(fd, 'w')
        upload = mysqldump_file.file
        bytes = upload.read(2048)
        while len(bytes) != 0:
            fd.write(bytes)
            bytes = upload.read(2048)
        fd.close()

        # Get main
        # TODO: modify this when multiple mains
        mains = self.config.getMySQLmains()
        try:
            for main in mains:
                client.load_dump(main.ip, self.config.AGENT_PORT, filename)
        except:
            self.logger.exception('load_dump: could not upload mysqldump_file ')
            self.state = self.S_ERROR
            return
        return HttpJsonResponse()
