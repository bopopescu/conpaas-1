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
'''


def get_cloud_instance(cloud_name, cloud_type, iaas_config):
    if cloud_type == 'opennebula':
        from .clouds.opennebula import OpenNebulaCloud
        return OpenNebulaCloud(cloud_name, iaas_config)
    elif cloud_type == 'ec2':
        from .clouds.ec2 import EC2Cloud
        return EC2Cloud(cloud_name, iaas_config)
    elif cloud_type == 'openstack':
        from .clouds.openstack import OpenStackCloud
        return OpenStackCloud(cloud_name, iaas_config)
    elif cloud_type == 'dummy':
        from .clouds.dummy import DummyCloud
        return DummyCloud(cloud_name, iaas_config)
    elif cloud_type == 'federation':
        # ConPaaS running in federation mode
        pass


def get_clouds(iaas_config):
    '''Parses the config file containing the clouds'''
    return [get_cloud_instance(cloud_name,
                               iaas_config.get(cloud_name, 'DRIVER').lower(),
                               iaas_config)
            for cloud_name in iaas_config.get('iaas', 'OTHER_CLOUDS').split(',')
            if iaas_config.has_section(cloud_name)]
