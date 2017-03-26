#!/usr/bin/env python

import sys
import os
import json
import argparse
from pprint import pprint

import boto3

from utils import logger

##########################################################################

key_name = "ec2.py"
aws_image = "ami-6869aa05"
instance_type = "t2.nano"


parser = argparse.ArgumentParser(description='Simple CLI / module to create/start/stop EC2 instances')
parser.add_argument('-p', '--profile', dest='aws_profile', metavar="AWS_PROFILE", help="AWS Profile Name")
parser.add_argument('-k', '--key', dest='aws_key', metavar="AWS_KEY", help="AWS Key name to use. Default: %s" % key_name)
parser.add_argument('-t', '--type', dest='aws_type', metavar="AWS_INS_TYPE", help="AWS Instance type. Default: %s" % instance_type)
parser.add_argument('-d', '--dry-run', action='store_true', help="Dry run")
parser.add_argument('-i', '--info', action='store_true', help="Print instance info. Default: Only IP to allow usage in other scripts. If verbose is set, prints additional info.")
parser.add_argument('-s', '--stop', action='store_true', help="Stop the instance")
parser.add_argument('-r', '--remove', action='store_true', help="Remove: Terminate instance and delete created key")
parser.add_argument('-v', '--verbose', action='store_true', help="Verbose mode")

args = parser.parse_args()

##########################################################################

def main():
    global key_name, aws_image, instance_type

    session = None
    ec2 = None
    client = None
    key_pair = None
    instance_id = None
    instance_state = None

    session = boto3.Session( profile_name=args.aws_profile )
    ec2 = session.resource('ec2')
    client = session.client('ec2')

    ###############################################
    # KeyPair
    ###############################################

    if args.aws_key:
        key_name = args.aws_key

    if args.aws_type:
        key_name = args.aws_type

    try:
        key_pair = ec2.KeyPair(key_name)
        key_pair.load()
        logger.info( "Found key with fingerprint:")
        logger.info( key_pair.key_fingerprint )
    except:
        try:
            r = client.create_key_pair(KeyName=key_name)
            print( "New key created." )

            with open (key_name + '.pem', 'w') as f:
                f.write(r['KeyMaterial'])
            print( "Downloaded key." )

            key_pair = ec2.KeyPair(key_name)
            key_pair.load()
            logger.info( "Using key with fingerprint:")
            logger.info( key_pair.key_fingerprint )
        except Exception as e:
            print(e)
            logger.error("Unable to create key.")

    ###############################################
    # Create Instance
    ###############################################

    r = client.describe_instances(Filters=[{'Name':'key-name', 'Values': [key_name]}])
    if len(r['Reservations']) > 0:
        for res in r['Reservations']:
            for ins in res['Instances']:
                ins_id = ins['InstanceId']
                ins_state = ins['State']['Name']
                if not args.info:
                    print('Instance %s is %s' % (ins_id, ins_state))
                if ins_state not in ('shutting-down', 'terminated'):
                    instance_id = ins_id
                    instance_state = ins_state
                    if args.info:
                        if args.verbose:
                            print('Image Id: %s' % ins['ImageId'])
                            print('Instance Id: %s' % ins['InstanceId'])
                            print('Instance Type: %s' % ins['InstanceType'])
                            print('Public IP: %s' % ins['PublicIpAddress'])
                            print('Public DNS Name: %s' % ins['PublicDnsName'])
                        else:
                            print(ins['PublicDnsName'])

    if instance_id == None:
        if args.remove:
            print('No instance found.')
            sys.exit(0)
        else:
            if args.info:
                sys.exit(0)
            try:
                logger.info('Creating a new instance.')
                r = client.run_instances(
                        ImageId=aws_image,
                        MinCount=1,
                        MaxCount=1,
                        KeyName=key_name,
                        InstanceType=instance_type,
                        InstanceInitiatedShutdownBehavior='terminate'
                        )
                instance_id = r['Instances'][0]['InstanceId']
                instance_state = r['Instances'][0]['State']['Name']
                print("Instance %s is %s" % (instance_id, instance_state))
            except:
                print("Unable to create AWS instance.")

    if instance_state in ('shutting-down'):
        waiter = client.get_waiter('instance_terminated')
        waiter.wait(InstanceIds=[instance_id])
        instance_state = 'terminated'
        print('Instance %s terminated.' % (instance_id))

    if instance_state in ('terminated'):
        print('Instance %s terminated.' % (instance_id))

    if instance_state in ('stopping'):
        waiter = client.get_waiter('instance_stopped')
        waiter.wait(InstanceIds=[instance_id])
        instance_state = 'stopped'
        print('Instance %s stopped.' % (instance_id))

    if instance_state in ('stopped'):
        if args.remove:
            r = client.terminate_instances(InstanceIds=[instance_id])
            if len(r['TerminatingInstances']) > 0:
                instance_state = r['TerminatingInstances'][0]['CurrentState']['Name']
                print("Instance %s is %s" % (instance_id, instance_state))
            else:
                logger.error('Instance %s was stopped, but could not be terminated' % (instance_id))
        else:
            if not args.stop:
                r = client.start_instances(InstanceIds=[instance_id])
                if len(r['StartingInstances']) > 0:
                    instance_state = r['StartingInstances'][0]['CurrentState']['Name']
                    print("Instance %s is %s" % (instance_id, instance_state))
                else:
                    logger.error('Instance %s was stopped, but could not be started' % (instance_id))

    if instance_state in ('pending'):
        waiter = client.get_waiter('instance_running')
        waiter.wait(InstanceIds=[instance_id])
        print('Instance %s running.' % (instance_id))


    if args.remove:
        r = client.terminate_instances(InstanceIds=[instance_id])
        if len(r['TerminatingInstances']) > 0:
            instance_state = r['TerminatingInstances'][0]['CurrentState']['Name']
            print("Instance %s is %s" % (instance_id, instance_state))

            key_pair.delete()
            print('Deleted key.')
        else:
            logger.error('Instance %s was stopped, but could not be terminated' % (instance_id))



    if args.stop and instance_state not in ('stopped', 'shutting-down', 'terminated'):
        r = client.stop_instances(InstanceIds=[instance_id])
        if len(r['StoppingInstances']) > 0:
            instance_state = r['StoppingInstances'][0]['CurrentState']['Name']
            print("Instance %s is %s" % (instance_id, instance_state))

            if instance_state in ('stopping'):
                waiter = client.get_waiter('instance_stopped')
                waiter.wait(InstanceIds=[instance_id])
                instance_state = 'stopped'
                print('Instance %s stopped.' % (instance_id))
            else:
                logger.error('Unexpected... Instance %s is %s' % (instance_id, instance_state))
        else:
            logger.error('Instance %s was running, but could not be stopped' % (instance_id))

##########################################################################

if __name__ == '__main__':
    main()

##########################################################################
