#/usr/bin/python
 
import boto.ec2
import time 

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

# Credentials 
access_id = "xxxxxx"
secret_key = "xxxxxx"

# Establish connection to region "us-east-1" along with aws_access_key_id and
# aws_secret_access_key
conn =  boto.ec2.connect_to_region(region, aws_access_key_id = access_id, aws_secret_access_key = secret_key)

# Create an SSH key to use when logging into instances.
key = conn.create_key_pair(key_name)

# Save the key as a .pem key file needed to SSH the new instances
key.save(key_dir)

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

