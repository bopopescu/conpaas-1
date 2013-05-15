#!/bin/sh

start_service() {
    service_type=$1
    manager_ip=`cpsclient.py create $1 | awk '{ print $5 }' | sed s/...$//`
    sid=`cpsclient.py list | grep $manager_ip | awk '{ print $2 }'`

    cpsclient.py start $sid > /dev/null
    return $sid
}

wait_for_running() {
    sid=$1

    while [ -z "`cpsclient.py info $sid | grep 'state: RUNNING'`" ]
    do
        sleep 2
    done
}

# Create and start service
echo "XtreemFS functional test started" | ts

start_service "xtreemfs"
xtreemfs_sid="$?"

echo "XtreemFS service created" | ts

wait_for_running $xtreemfs_sid

echo "XtreemFS service running" | ts

# Create a new volume
cpsclient.py create_volume $xtreemfs_sid testvol > /dev/null
wait_for_running $xtreemfs_sid

# The list of volumes should contain "testvol"
if [ "testvol" = "`cpsclient.py list_volumes $xtreemfs_sid | awk '/testvol/ { print $1 }'`" ]
then 
    echo "Volume created successfully" | ts
else
    echo "Volume creation FAILED" | ts
    exit 1
fi

# List OSD selection policies
if [ "DEFAULT, FQDN, UUID, DCMAP, VIVALDI" = "`cpsclient.py list_policies $xtreemfs_sid osd_sel`" ]
then
    echo "OSD selection policies listing OK" | ts
else
    echo "OSD selection policies listing FAILED" | ts
    exit 1
fi

# Set OSD selection policy to UUID
if [ "Policy set." = "`cpsclient.py set_policy $xtreemfs_sid osd_sel testvol UUID | grep Policy`" ]
then
    echo "OSD selection policy setting OK" | ts
else
    echo "OSD selection policy setting FAILED" | ts
    exit 1
fi

# List replica selection policies
if [ "DEFAULT, FQDN, DCMAP, VIVALDI" = "`cpsclient.py list_policies $xtreemfs_sid replica_sel`" ]
then
    echo "Replica selection policies listing OK" | ts
else
    echo "Replica selection policies listing FAILED" | ts
    exit 1
fi

# Set replica selection policy to VIVALDI
if [ "Policy set." = "`cpsclient.py set_policy $xtreemfs_sid replica_sel testvol VIVALDI | grep Policy`" ]
then
    echo "Replica selection policy setting OK" | ts
else
    echo "Replica selection policy setting FAILED" | ts
    exit 1
fi

# List replication policies
if [ "ronly, WaR1, WqRq" = "`cpsclient.py list_policies $xtreemfs_sid replication`" ]
then
    echo "Replication policies listing OK" | ts
else
    echo "Replication policies listing FAILED" | ts
    exit 1
fi

# Set replica selection policy to VIVALDI
if [ "Policy set." = "`cpsclient.py set_policy $xtreemfs_sid replication testvol WaR1 2 | grep Policy`" ]
then
    echo "Replication policy setting OK" | ts
else
    echo "Replication policy setting FAILED" | ts
    exit 1
fi

# Delete test volume
cpsclient.py delete_volume $xtreemfs_sid testvol > /dev/null
wait_for_running $xtreemfs_sid

if [ "testvol" = "`cpsclient.py list_volumes $xtreemfs_sid | awk '/testvol/ { print $1 }'`" ]
then 
    echo "Volume deletion FAILED" | ts
    exit 1
else
    echo "Volume deleted successfully" | ts
fi

cpsclient.py stop $xtreemfs_sid | ts

while [ -z "`cpsclient.py info $xtreemfs_sid | grep 'state: STOPPED'`" ]
do
    sleep 2
done

cpsclient.py terminate $xtreemfs_sid | ts
