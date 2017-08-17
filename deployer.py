import sqlite3
import boto.ec2
import time
import os
import sys

# Instance variables
region = 'us-east-1'
key_name = 'key_pair'
key_dir = '~/.ssh'
ami = 'ami-8caa1ce4'
instance_type = 't1.micro'
group_name = 'csc326-group1'
ping_port = -1
ssh_port = 22
http_port = 80
cidr = '0.0.0.0/0'

# Getting Credentials
credentials = {}
with open("rootkey.csv") as keyfile:
    for line in keyfile:
        name, key = line.partition("=")[::2]
        credentials[name.strip()] = key.strip()

    print credentials


def establish_aws_conn():
    return boto.ec2.connect_to_region(region, aws_access_key_id = credentials['AWSAccessKeyId'], aws_secret_access_key = credentials['AWSSecretKey'])

def launch_aws_instance():
    # Establish connection to region "us-east-1" along with aws_access_key_id and
    # aws_secret_access_key
    conn = establish_aws_conn()

    if len(conn.get_all_key_pairs(keynames=[key_name])) == 0:
        # Create an SSH key to use when logging into instances.
        key = conn.create_key_pair(key_name)

        # Save the key as a .pem key file needed to SSH the new instances
        key.save(key_dir)

    # Check for existing security groups
    groups = conn.get_all_security_groups(groupnames=[group_name])
    if len(groups) == 0:
        # Create a security group to provides restricted
        # access only from authorized IP address and ports
        group = conn.create_security_group(group_name, 'Group-01 security group.')
        
        # Authorize following protocols and ports for the security group
        group.authorize('ICMP', ping_port, ping_port, cidr)
        group.authorize('TCP', ssh_port, ssh_port, cidr)
        group.authorize('tcp', http_port, http_port, cidr)

    # Start a new instance
    new_instance = conn.run_instances(ami, key_name = key_name, instance_type = instance_type, security_groups = [group_name])
    instance = new_instance.instances[0]

    while instance.state != u'running':
        time.sleep(5)
        instance.update()

    address = conn.allocate_address()
    address.associate(instance.id)

    return instance.id, address.public_ip

def deploy():
    db_conn = sqlite3.connect('crawler.db')
    instance_id, public_ip_address = launch_aws_instance()
    os.system("ssh -i %s ubuntu@%s" % (key_pair_path, public_ip_address))
    os.system("scp -i %s %s ubuntu@%s:~/%s" % (key_pair_path, file_path, public_ip, remote_path))

    print "Public IP Address: %s" % public_ip_address
    print "Instance ID: %s" % instance_id

    return public_ip_address

deploy()

