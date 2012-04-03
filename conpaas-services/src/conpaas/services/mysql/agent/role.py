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


Created in February, 2012

@author: alesc, aaasz
'''

import os, io, socket
import ConfigParser
import MySQLdb

from os.path import join, devnull, exists
from os import kill, chown, setuid, setgid
from pwd import getpwnam
from signal import SIGINT, SIGTERM, SIGUSR2, SIGHUP
from subprocess import Popen
from shutil import rmtree, copy2
from Cheetah.Template import Template

from conpaas.core.misc import verify_port, verify_ip_port_list, verify_ip_or_domain
from conpaas.core.log import create_logger

S_INIT        = 'INIT'
S_STARTING    = 'STARTING'
S_RUNNING     = 'RUNNING'
S_STOPPING    = 'STOPPING'
S_STOPPED     = 'STOPPED'

sql_logger = create_logger(__name__)

class MySQLServer(object):
    """
    Holds configuration of the MySQL server.
    """

    def __init__(self, config):
        """
        Creates a configuration from `config`. 
        
        :param config: Configuration read with ConfigParser.
        :type config: ConfigParser
        :param  _dummy_config: Set to `True` when used in unit testing.
        :type boolean: boolean value.
        """
        sql_logger.debug("Entering init MySQLServerConfiguration")
        try:
            hostname = socket.gethostname()

            # Get connection settings
            self.pid_file = "/var/lib/mysql/" + hostname + ".pid"
            sql_logger.debug("Trying to get params from configuration file ")        
            self.conn_location = config.get('MySQL_root_connection', 'location')
            self.conn_username = config.get("MySQL_root_connection", "username")
            self.conn_password = config.get("MySQL_root_connection", "password")
            sql_logger.debug("Got parameters for root connection to MySQL")

            # Get MySQL configuration parameters
            self.mysqldump_path = config.get('agent', 'MYSQLDUMP_PATH')
            self.mycnf_filepath = config.get("MySQL_configuration","my_cnf_file")
            self.path_mysql_ssr = config.get("MySQL_configuration","path_mysql_ssr")
            self.mysqlconfig = self._load_configuration(self.mycnf_filepath)

            # We need to remove the bind-address option (the default one is 
            # 127.0.0.1 = accepting conections only on local interface)
            if self.mysqlconfig.has_option('mysqld', 'bind-address'):
                self.mysqlconfig.remove_option('mysqld', 'bind-address')

        except ConfigParser.Error, err:
            #ex = AgentException(E_CONFIG_READ_FAILED, str(err))
            sql_logger.exception('Could not read config file')
        except IOError, err:
            #ex = AgentException(E_CONFIG_NOT_EXIST, str(err))
            sql_logger.exception('Config file doesn\'t exist')

        # Creating a supervisor object
        sql_logger.debug("Leaving init MySQLServerConfiguration")

    def _load_dump(self, f):
        sql_logger.debug("Entering load_dump")
        try:
            mysqldump = f.read()
            d = open('/tmp/mysqldump.db', 'w')
            d.write(mysqldump)
            d.close()
            os.system("mysql -u root  -p"  + self.conn_password + " < /tmp/mysqldump.db")
            #os.system('rm /tmp/mysqldump.db')
            sql_logger.debug("Leaving load_dump")
        except Exception as e:
            sql_logger.exception('Failed to load dump')
            raise e

    def start(self):
        self.state = S_STARTING
        devnull_fd = open(devnull, 'w')
        proc = Popen([self.path_mysql_ssr, "start"], stdout=devnull_fd, stderr=devnull_fd, close_fds=True)
        if proc.wait() != 0:
            sql_logger.critical('Failed to start mysqld (code=%d)' % proc.returncode)
            self.state = S_STOPPED
            raise OSError('Failed to start web server (code=%d)' % proc.returncode)
	self.state = S_RUNNING
	sql_logger.info(' started')

    def stop(self):
        if self.state == S_RUNNING:
            self.state = S_STOPPING
            if exists(self.pid_file):
                try:
                    pid = int(open(self.pid_file, 'r').read().strip())
                except IOError as e:
                    sql_logger.exception('Failed to open PID file "%s"' % (self.pid_file))
                    raise e
                except (ValueError, TypeError) as e:
                    sql_logger.exception('PID in "%s" is invalid' % (self.pid_file))
                    raise e
	    
                try:
                    kill(pid, self.stop_sig)
                    self.state = S_STOPPED
                    sql_logger.info('mysqld stopped')
                except (IOError, OSError) as e:
                    sql_logger.exception('Failed to kill mysqld PID=%d' % (pid))
                    raise e
            else:
                sql_logger.critical('Could not find PID file %s to kill mysqld' % (self.pid_file))
                raise IOError('Could not find PID file %s to kill mysqld' % (self.pid_file))
        else:
            sql_logger.warning('Request to kill mysqld while it is not running')

    def restart(self):
        sql_logger.debug("Entering MySQLServer restart")
        try:
            devnull_fd = open(devnull, 'w')
            sql_logger.debug('Restarting with arguments:' + self.config.path_mysql_ssr + " restart")
            proc = Popen([self.path_mysql_ssr, "restart"] , stdout=devnull_fd, stderr=devnull_fd, close_fds=True)
            sql_logger.debug("Restarting mysql server")
            proc.wait()                            
            if exists(self.pid_file) == False:
                sql_logger.critical('Failed to restart mysql server.)')
                raise OSError('Failed to restart mysql server.')
            self.state = S_RUNNING
            sql_logger.info('MySQL restarted')          
        except IOError as e:
            sql_logger.exception('Failed to open PID file "%s"' % (self._current_pid_file(increment=-1)))
            self.state = S_STOPPED
            raise e
        except (ValueError, TypeError) as e:
            sql_logger.exception('PID in "%s" is invalid' % (self._current_pid_file(increment=-1)))
            self.state = S_STOPPED
            raise e    
        sql_logger.debug("Leaving MySQLServer restart")

    # This is necessary because of the options without value that are in mysql's my.cnf
    # It is fixed in python 3+, where we could just use ConfigParser. 
    def _load_configuration(self, mycnf_filepath):
        """
        Parses MySQL server configuration into 
        """
        
        config = ConfigParser.ConfigParser()

        file = open(mycnf_filepath, 'r+w')
        text = file.read()
        file.close()
		            
        #comments inside
        while text.count("#")>0:
            text = text[0:text.index("#")] + text[text.index("\n",text.index("#")):]
	zac = 0
	while text.count("\n",zac)>1:
	    if ( text[text.index("\n",zac)+1:text.index("\n",text.index("\n",zac+1))].find("[") == -1 
	      & text[text.index("\n",zac)+1:text.index("\n",text.index("\n",zac+1))].find("=") == -1):
	        text = text[0:text.index("\n",zac)+1] + text[text.index("\n",text.index("\n",zac+1)):]
	    zac = text.index("\n", zac+1)         
	# \n inside
	while text.count("\t")>0:
	    text = text[0:text.index("\t")] + text[text.index("\t")+1:]
	while text.count(" ")>0:
	    text = text[0:text.index(" ")] + text[text.index(" ")+1:]
	while text.count("\n\n")>0:
	    text = text[0:text.index("\n\n")] + text[text.index("\n\n")+1:]

        file = open(mycnf_filepath, 'w')
	file.write(text)
        file.close()

        file = open(mycnf_filepath, 'r')
        config.readfp(file)
	file.close()

	return config

class MySQLMaster(MySQLServer):
    ''' Class describing a MySQL replication master. 
        It can be initializad with a dump, or without '''

    def __init__(self, config=None, master_server_id=0, dump=None):
        sql_logger.debug("Entering init MySQLServerConfiguration")
        MySQLServer.__init__(self, config)
    
        # Configure it as a master
        path=self.mycnf_filepath
        self.mysqlconfig.set("mysqld", "server-id", master_server_id)
        self.mysqlconfig.set("mysqld", "log_bin", "/var/log/mysql/mysql-bin.log")
        os.remove(path)
        newf = open(path,"w")
        self.mysqlconfig.write(newf)
        newf.close()

        # Start the replication master
        self.start()
        #if dump != None:
        #    self.load_dump(dump)

        # Change root password - not set as installation
        os.system("mysqladmin -u root password "  + self.conn_password)

	#TODO: add user conn_userame and grant privileges to it from any host 
        self.add_user(self.conn_username, self.conn_password)


    '''Before creating a data snapshot or starting 
    the replication process, you should record the 
    position of the binary log on the master. You will 
    need this information when configuring the slave so 
    that the slave knows where within the binary log to 
    start executing events. See Section 15.1.1.4, Obtaining 
    the Replication Master Binary Log Coordinates. 

    1st session
    mysql> FLUSH TABLES WITH READ LOCK;

    2nd session
    mysql > SHOW MASTER STATUS;
    record the values

    close 2nd session

    on the master 
    mysqldump --all-databases --lock-all-tables >dbdump.db

    1st session
    mysql>UNLOCK TABLES;

    '''

    def take_snapshot(self):
        '''1st session
        '''
        db1 = MySQLdb.connect(self.conn_location, 'root', self.conn_password)
        exc = db1.cursor()
        exc.execute("FLUSH TABLES WITH READ LOCK;")
        '''2nd session
        '''
        db2 = MySQLdb.connect(self.conn_location, 'root', self.conn_password)
        exc = db2.cursor()
        exc.execute("SHOW MASTER STATUS;")
        rows = exc.fetchall()
        db2.close()
        i = 0
        ret = {}
        for row in rows:
            i = i+1
	    ret['position' + str(i)] = {'binfile': row[0], 'position': row[1], 'mysqldump_path': self.mysqldump_path}

	# dump everything except test?
        os.system("mysql --user=root --password=" + self.conn_password + \
                  " --batch --skip-column-names " + \
                  "--execute=\"SHOW DATABASES\" | egrep -v \"information_schema|test\" " + \
                  "| xargs mysqldump --user=root --password=" + self.conn_password + \
                  " --lock-all-tables --databases > " + self.mysqldump_path)

        exc = db1.cursor()
        exc.execute("UNLOCK TABLES;")
        db1.close()
        return ret

    def register_slave(self, slave_ip):
        sql_logger.debug("Entering init register_slave")
        db = MySQLdb.connect(self.conn_location, 'root', self.conn_password)
        exc = db.cursor()
        exc.execute('GRANT REPLICATION SLAVE ON *.*' \
                    ' TO \'%s\'@\'%s\' IDENTIFIED BY \'%s\';' \
                      % ('root', slave_ip, self.conn_password))
        db.close()
        sql_logger.debug("Exit init register_slave")
        # TODO: test if successful
        return

    def add_user(self, new_username, new_password):
        db = MySQLdb.connect(self.conn_location, 'root', self.conn_password)
        exc = db.cursor()
        exc.execute ("create user '" + new_username + "'@'localhost' identified by '" + new_password + "'")
        exc.execute ("grant all privileges on *.* TO '" + new_username + "'@'localhost' with grant option;")
        exc.execute ("create user '" + new_username + "'@'%' identified by '" + new_password + "'")
        exc.execute ("grant all privileges on *.* TO '" + new_username + "'@'%' with grant option;")
        db.close()

    #def grant_user(self, username,  hosts, password):
    #    db = MySQLdb.connect(self.conn_location, self.conn_username, self.conn_password)
    #    exc = db.cursor()
    #    for host in hosts:
    #        exc.execute ("grant all privileges on *.* TO '" + username + \
    #                     "'@'" + host + "' with grant option;")
    #    db.close()

    def load_dump(self, file):
        self._load_dump(file)
   
    def remove_user(self, username):
        db = MySQLdb.connect(self.conn_location, 'root', self.conn_password)
        exc = db.cursor()
        exc.execute ("drop user '" + username +"'@'localhost'")
        exc.execute ("drop user '" + username +"'@'%'")
        db.close()
    
    def get_users(self):
        db = MySQLdb.connect(self.conn_location, 'root', self.conn_password)
        exc = db.cursor()
        exc.execute("SELECT user, host FROM mysql.user")
        rows = exc.fetchall()
        db.close()
        ret = {'opState': 'OK'}
        i = 0
        for row in rows:
            i = i+1
            ret['info' + str(i)] = {'location': row[1], 'username': row[0]}
        return ret

    def set_password(self, username, password):
        db = MySQLdb.connect(self.conn_location, 'root', self.conn_password)
        exc = db.cursor()
        exc.execute("set password for '" + username + "'@'%' = password('" + password + "')")
	db.close()

    def status(self):
        return {'state': self.state,
                'port': self.port 
               }


class MySQLSlave(MySQLServer):
    ''' Class describing a MySQL replication slave. 
        It initializes with a, or without '''
    def __init__(self, config = None, master_host = None, \
                 master_log_file = None, master_log_pos = 0, \
		 mysqldump_file = None, slave_server_id = 0):
        MySQLServer.__init__(self, config)

        path=self.mycnf_filepath
        self.mysqlconfig.set("mysqld", "server-id", slave_server_id)
       
        #self.mysqlconfig.set("mysqld", "skip-slave-start", slave_server_id)        
        os.remove(path)
        newf=open(path,"w")
        self.mysqlconfig.write(newf)
        newf.close()
  
        # Start the replication slave
        self.start()

        # Change root password - not set at installation
        os.system("mysqladmin -u root password "  + self.conn_password)

        # Configure it as a slave
        db = MySQLdb.connect(self.conn_location, 'root', self.conn_password)
        exc = db.cursor()
        query=(("CHANGE MASTER TO  MASTER_HOST='%s', " + 
                    "MASTER_USER='%s', " +
                    "MASTER_PASSWORD='%s', " 
                    "MASTER_LOG_FILE='%s', " +  
                    "MASTER_LOG_POS=%s;") % (master_host, 'root', self.conn_password, master_log_file, master_log_pos))
        exc.execute(query)

        # TODO: get the dump from the master ( replication from another slave?? )
        if mysqldump_file != None:
            self._load_dump(mysqldump_file)

        # Start the slave thread
        query=('START SLAVE;') 
        exc.execute(query)
        db.close()
        
    def status(self):
        return {'state': self.state,
                'port': self.port 
               }