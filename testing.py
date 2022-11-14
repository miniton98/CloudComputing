# Keys are defined in configuration file
# MAKE SURE YOU UPDATED YOUR .AWS/credentials file
# MAKE SURE boto3, matplotlib, requests and tornado are all installed using pip
import boto3
import json
import time
import requests
from datetime import datetime, date, timedelta
import matplotlib.pyplot as plt
import matplotlib as mpl
import webbrowser

# This makes the plots made by the script open in a webbrowser

def createSecurityGroup(ec2_client):
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

def main():
    ec2_client = boto3.client("ec2")
    SECURITY_GROUP, vpc_id = createSecurityGroup(ec2_client)

    print("Security Group", SECURITY_GROUP)

main()