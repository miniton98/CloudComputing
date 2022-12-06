# Keys are defined in configuration file
# MAKE SURE YOU UPDATED YOUR .AWS/credentials file
# MAKE SURE boto3, matplotlib, requests and tornado are all installed using pip
import boto3
from pathlib import Path

# This makes the plots made by the script open in a webbrowser
"""https://cloudinfrastructureservices.co.uk/how-to-create-a-multi-node-mysql-cluster-on-ubuntu-20-04/"""
"""https://www.digitalocean.com/community/tutorials/how-to-create-a-multi-node-mysql-cluster-on-ubuntu-18-04"""

userdata_primary="""#!/bin/bash
cd /home/ubuntu
sudo apt-get update
yes | sudo apt-get upgrade
wget https://downloads.mysql.com/archives/get/p/14/file/mysql-cluster-community-management-server_7.6.23-1ubuntu18.04_amd64.deb
sudo dpkg -i mysql-cluster-community-management-server_7.6.23-1ubuntu18.04_amd64.deb
sudo mkdir /var/lib/mysql-cluster

wget https://downloads.mysql.com/archives/get/p/14/file/mysql-cluster_7.6.23-1ubuntu18.04_amd64.deb-bundle.tar
sudo mkdir install
sudo tar -xvf mysql-cluster_7.6.23-1ubuntu18.04_amd64.deb-bundle.tar -C install/

# Sakila download
#some issues with unzip download
sudo wget http://downloads.mysql.com/docs/sakila-db.zip
sudo apt update
yes | sudo apt --fix-broken install
sudo apt install unzip
sudo unzip sakila-db.zip -d "/tmp/"

yes | sudo apt-get install sysbench
"""

userdata_secondary="""#!/bin/bash
cd /home/ubuntu
sudo apt-get update
wget https://downloads.mysql.com/archives/get/p/14/file/mysql-cluster-community-data-node_7.6.23-1ubuntu18.04_amd64.deb
sudo apt update
sudo apt install libclass-methodmaker-perl
sudo dpkg -i mysql-cluster-community-data-node_7.6.23-1ubuntu18.04_amd64.deb
"""

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
            GroupName="MySQLCluster",
            VpcId=vpc_id
        )

        # Wait for the security group to exist!
        new_group_waiter = ec2_client.get_waiter('security_group_exists')
        new_group_waiter.wait(GroupNames=["MySQLCluster"])

        group_id = new_group["GroupId"]

        #change rule to allow more port for the chldren
        rule_creation = ec2_client.authorize_security_group_ingress(
            GroupName="MySQLCluster",
            GroupId=group_id,
            IpPermissions=[{
                'FromPort': 22,
                'ToPort': 22,
                'IpProtocol': 'tcp',
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            },
            {
                'FromPort': 1186,
                'ToPort': 1186,
                'IpProtocol': 'tcp',
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            },
            {
                'FromPort': 0,
                'ToPort': 65535,
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
            if (group['GroupName'] == 'MySQLCluster'):
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
    INSTANCE_IMAGE = "ami-0ee23bfc74a881de5"

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

    # MySQL cluster instances
    instances_t2_primary = createInstance(ec2, "t2.micro", 1, SECURITY_GROUP, availability_zone_1a, userdata_primary)
    instances_t2_cluster = createInstance(ec2, "t2.micro", 3, SECURITY_GROUP, availability_zone_1a, userdata_secondary)
    # proxy instance
    #instances_t2_proxy = createInstance(ec2, "t2.large", 1, SECURITY_GROUP, availability_zone_1a, userdata_proxy)

    instance_ids = []
    primary_instance_id = []
    cluster_instance_ids = []
    proxy_instance_id = []



    for instance in instances_t2_primary:
        instance.wait_until_running()
        instance.reload()
        instance_ids.append(instance.id)
        primary_instance_id.append({'Id': instance.id,
                                    'Ip': instance.public_ip_address,
                                    'privateIp': instance.private_ip_address})

    for instance in instances_t2_cluster:
        instance.wait_until_running()
        instance.reload()
        instance_ids.append(instance.id)
        cluster_instance_ids.append({'Id': instance.id,
                                     'Ip': instance.public_ip_address,
                                     'privateIp': instance.private_ip_address})
    """
    for instance in instances_t2_proxy:
        instance_ids.append(instance.id)
        proxy_instance_id.append({'Id': instance.id})"""

    # Wait for all instances to be active!
    instance_running_waiter = ec2_client.get_waiter('instance_running')
    instance_running_waiter.wait(InstanceIds=(instance_ids))

    return instance_ids, primary_instance_id, cluster_instance_ids, proxy_instance_id


def main():

    """-------------------Get necesarry clients from boto3----------------------"""
    ec2_client = boto3.client("ec2")
    ec2 = boto3.resource('ec2')

    """-------------------Create security group----------------------"""
    SECURITY_GROUP, vpc_id = createSecurityGroup(ec2_client)
    print("security_group: ", SECURITY_GROUP)
    print("vpc_id: ", str(vpc_id), "\n")

    """-------------------Get availability Zones----------------------"""
    availabilityZones = getAvailabilityZones(ec2_client)
    print("Availability zones:")
    print("Zone 1a: ", availabilityZones.get('us-east-1a'), "\n")

    """-------------------Create the instances----------------------"""
    ins_ids, primary_instance_id, cluster_instance_ids, proxy_instance_id = createInstances(ec2_client, ec2, SECURITY_GROUP, availabilityZones)
    print("Instance ids: \n", str(ins_ids), "\n")
    print("Instance id primary: \n", str(primary_instance_id), "\n")
    print("Instance ids cluster:")
    for ins in cluster_instance_ids:
        print(ins)
    #print("Instance id proxy: \n", str(proxy_instance_id), "\n")

main()