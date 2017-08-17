import boto.ec2
import sys
import deployer

def terminate(instance_id):
    conn = establish_aws_conn()
    conn.terminate_instances(instance_ids=[instance_id])

    instances = conn.get_all_instance_status(instance_ids)
    if not instances:
        print "Instance: %s terminated successfully" % instance_id
    else:
        print "Error: Failed to terminate instance: %s" % instance_id


terminate(sys.argv[1])
