# Keys are defined in configuration file
# MAKE SURE YOU UPDATED YOUR .AWS/credentials file
# MAKE SURE boto3, matplotlib, requests and tornado are all installed using pip
import boto3
import paramiko
from pathlib import Path
import json
import time
import requests
from datetime import datetime, date, timedelta
import matplotlib.pyplot as plt
import matplotlib as mpl
import webbrowser

"""
The user data constant is used to setup and download programs on the instances
They are passed as arguments in the create instance step
https://fedingo.com/how-to-automate-mysql_secure_installation-script/
"""

userdata_SA="""#!/bin/bash
cd /home/ubuntu
sudo apt-get update
yes | sudo apt-get upgrade
yes | sudo apt-get install mysql-server

# Sakila download
sudo wget http://downloads.mysql.com/docs/sakila-db.zip
sudo apt install unzip
sudo unzip sakila-db.zip -d "/tmp/"
sudo mysql -e "SOURCE /tmp/sakila-db/sakila-schema.sql;"
sudo mysql -e "SOURCE /tmp/sakila-db/sakila-data.sql;"

# MySQL installation
sudo mysql -e "UPDATE mysql.user SET Password=PASSWORD('admin') WHERE User='root';"
sudo mysql -e "DELETE FROM mysql.user WHERE User='';"
sudo mysql -e "DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');"
sudo mysql -e "DROP DATABASE test"
sudo mysql -e "FLUSH PRIVILEGES;"
sudo mysql -e "CREATE USER 'victor'@'localhost' IDENTIFIED BY 'password';"
sudo mysql -e "GRANT ALL PRIVILEGES on sakila.* TO 'victor'@'localhost';"

# Sysbench installation and benchmarking
yes | sudo apt-get install sysbench
# Prepare
sysbench --db-driver=mysql --mysql-user=victor --mysql_password=password --mysql-db=sakila --tables=6 --table-size=200 /usr/share/sysbench/oltp_read_write.lua prepare
sysbench --db-driver=mysql --mysql-user=victor --mysql_password=password --mysql-db=sakila --tables=6 --table-size=200 --threads=6 --time=60 /usr/share/sysbench/oltp_read_write.lua run > SA.txt
"""

# allows us to geth the path for the pem file
def get_project_root() -> Path:
    """
    Function for getting the path where the program is executed
    @ return: returns the parent path of the path were the program is executed
    """
    return Path(__file__).parent

def createSecurityGroup(ec2_client):
    """
        The function creates a new security group in AWS or fetches an existing one
        The function retrievs the vsp_id from the AWS portal, as it is personal and needed for creating a new group
        try:
            It then creates the security group using boto3 package
            then it waits for the creation
            then it assigns new rules to the security group
        except:
            fetch existing group

        Parameters
        ----------
        ec2_client
            client that allows for sertain functions using boto3

        Returns
        -------
        SECURITY_GROUP : list[str]
            list of the created security group ids
        vpc_id : str
            the vpc_id as it is needed for other operations

    """
    # Create security group, using SSH & HHTP access available from anywhere
    groups = ec2_client.describe_security_groups()
    vpc_id = groups["SecurityGroups"][0]["VpcId"]
    try:
        new_group = ec2_client.create_security_group(
            Description="SSH and HTTP access",
            GroupName="MySQL",
            VpcId=vpc_id
        )

        # Wait for the security group to exist!
        new_group_waiter = ec2_client.get_waiter('security_group_exists')
        new_group_waiter.wait(GroupNames=["MySQL"])

        group_id = new_group["GroupId"]

        rule_creation = ec2_client.authorize_security_group_ingress(
            GroupName="MySQL",
            GroupId=group_id,
            IpPermissions=[{
                'FromPort': 22,
                'ToPort': 22,
                'IpProtocol': 'tcp',
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            },
            {
                'FromPort': 80,
                'ToPort': 80,
                'IpProtocol': 'tcp',
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            }]
        )

        SECURITY_GROUP = [group_id]
        return SECURITY_GROUP, vpc_id

    except:
        print("Group already exists fetching it")
        #print("sec groups", groups)
        sec_groups = groups["SecurityGroups"]
        for group in sec_groups:
            if (group['GroupName'] == 'MySQL'):
                SECURITY_GROUP = [group['GroupId']]

        return SECURITY_GROUP, vpc_id

def getAvailabilityZones(ec2_client):
    """
        Retrieving the subnet ids for availability zones
        they are required to assign for example instances to a specific availabilityzone

        Parameters
        ----------
        ec2_client
            client of boto3 tho access certain methods related to AWS EC2

        Returns
        -------
        dict
            a dictonary, with availability zone name as key and subnet id as value

        """
    # Availability zones
    response = ec2_client.describe_subnets()

    availabilityzones = {}
    for subnet in response.get('Subnets'):
        # print(subnet)
        availabilityzones.update({subnet.get('AvailabilityZone'): subnet.get('SubnetId')})

    return availabilityzones

def createInstance(ec2, INSTANCE_TYPE, COUNT, SECURITY_GROUP, SUBNET_ID, userdata):
    """
        function that creates EC2 instances on AWS

        Parameters
        ----------
        ec2 : client
            ec2 client to perform actions on AWS EC2 using boto3
        INSTANCE_TYPE : str
            name of the desired instance type.size
        COUNT : int
            number of instances to be created
        SECURITY_GROUP : array[str]
            array of the security groups that should be assigned to the instance
        SUBNET_ID : str
            subnet id that assigns the instance to a certain availability zone
        userdata : str
            string that setups and downloads programs on the instance at creation

        Returns
        -------
        array
            list of all created instances, including their data

        """
    # Don't change these
    KEY_NAME = "vockey"
    INSTANCE_IMAGE = "ami-08d4ac5b634553e16"

    return ec2.create_instances(
        ImageId=INSTANCE_IMAGE,
        MinCount=COUNT,
        MaxCount=COUNT,
        InstanceType=INSTANCE_TYPE,
        KeyName=KEY_NAME,
        SecurityGroupIds=SECURITY_GROUP,
        SubnetId=SUBNET_ID,
        UserData=userdata
    )

def createInstances(ec2_client, ec2, SECURITY_GROUP, availabilityZones):
    """
        function that retrievs and processes attributes as well as defining the amount and types of instances to be created
        getting the decired subnet id
        calling function create instance to create the instances
        parces the return to just return the ids and ips of the instances
        currently handle only creation of one instance

        Parameters
        ----------
        ec2_client : client
            Boto3 client to access certain function to controll AWS CLI
        ec2 : client
            Boto3 client to access certain function to controll AWS CLI
        SECURITY_GROUP : array[str]
            list of security groups to assign to instances
        availabilityZones : dict{str, str}
            dict of availability zone names an key and subnet ids as value
        userdata : str
            script to setup instances

        Returns
        -------
        array
            containg instance id and ip
        """
    # Get wanted availability zone
    availability_zone_1a = availabilityZones.get('us-east-1a')

    # stand alone instance
    instances_t2_SA = createInstance(ec2, "t2.micro", 1, SECURITY_GROUP, availability_zone_1a, userdata_SA)

    instance_ids = []
    SA_instance_id = []

    instances_t2_SA[0].wait_until_running()
    instances_t2_SA[0].reload()

    for instance in instances_t2_SA:
        instance_ids.append(instance.id)
        SA_instance_id.append({'Id': instance.id,
                               'Ip': instance.public_ip_address})


    # Wait for all instances to be active!
    instance_running_waiter = ec2_client.get_waiter('instance_running')
    instance_running_waiter.wait(InstanceIds=(instance_ids))

    return SA_instance_id

def getParamikoClient():
    """
        Retrievs the users PEM file and creates a paramiko client required to ssh into the instances

        Returns
        -------
        client
            the paramiko client
        str
            the access key from the PEM file

        """
    path = str(get_project_root()).replace('\\', '/')
    print("path", path)
    accesKey = paramiko.RSAKey.from_private_key_file(path + "/labsuser.pem")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    return client, accesKey

def send_command(client, command):
    """
        function that sends command to an instance using paramiko
        print possible errors and return values

        Parameters
        ----------
        client : client
            the paramiko client required to connect to the intance usin ssh
        command : str
            The desired commands are sent to the instance

        Returns
        -------
        str
            returns the return value of commands

        """
    try:
        stdin, stdout, stderr = client.exec_command(command)
        # the read() function reads the output in bit form
        print("stderr.read():", stderr.read())
        # converts the bit string to str
        output = stdout.read().decode('ascii')
        print("output", output)
        return output
    except:
        print("error occured in sending command")

def getSysbechfile(client, accesKey, ip):
    try:
        client.connect(hostname=ip, username="ubuntu", pkey=accesKey)
    except:
        print("could not connect to client")

    res = send_command(client, "cat SA.txt")

def main():

    """-------------------Get necesarry clients from boto3----------------------"""
    ec2_client = boto3.client("ec2")
    ec2 = boto3.resource('ec2')

    """------------Create Paramiko Client------------------------------"""
    paramiko_client, accesKey = getParamikoClient()

    """-------------------Create security group----------------------"""
    SECURITY_GROUP, vpc_id = createSecurityGroup(ec2_client)
    print("security_group: ", SECURITY_GROUP)
    print("vpc_id: ", str(vpc_id), "\n")

    """-------------------Get availability Zones----------------------"""
    availabilityZones = getAvailabilityZones(ec2_client)
    print("Availability zones:")
    print("Zone 1a: ", availabilityZones.get('us-east-1a'), "\n")

    """-------------------Create the instances----------------------"""
    SA_instance_id = createInstances(ec2_client, ec2, SECURITY_GROUP, availabilityZones)

    print("Instance id SA: \n", str(SA_instance_id), "\n")

    print("Waiting for setup")
    time.sleep(300)

    """------------------Get Sysbech File----------------------------"""
    getSysbechfile(paramiko_client, accesKey, SA_instance_id[0]['Ip'])

main()