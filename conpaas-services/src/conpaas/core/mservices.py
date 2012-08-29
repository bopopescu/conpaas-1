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
 3. Neither the name of the Contrail consortium nor the
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


   This file contains all the available manager services
implementations.

'''

services = {'php'    : {'class' : 'PHPManager', 
                        'module': 'conpaas.services.webservers.manager.internal.php'},
            'java'   : {'class' : 'JavaManager',
                        'module': 'conpaas.services.webservers.manager.internal.java'},
            'scalaris' : {'class' : 'ScalarisManager',
                        'module': 'conpaas.services.scalaris.manager.manager'},
            'hadoop' : {'class' : 'MapReduceManager',
                        'module': 'conpaas.services.mapreduce.manager.manager'},
            'helloworld' : {'class' : 'HelloWorldManager',
                        'module': 'conpaas.services.helloworld.manager.manager'},
            'cds' : {'class' : 'ContentDeliveryManager',
                     'module': 'conpaas.services.cds.manager.manager'},
            'mysql' : {'class' : 'MySQLManager',
                        'module': 'conpaas.services.mysql.manager.manager'},
            'selenium' : {'class' : 'SeleniumManager',
                        'module': 'conpaas.services.selenium.manager.manager'},
           }