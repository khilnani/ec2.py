#!/usr/bin/env python

import sys
import os
import json
import argparse

import boto3

from utils import logger



key_name = "lambda-py-extentions"
aws_image = "ami-6869aa05"
instance_type = "t2.nano"

session = None
ec2 = None
client = None
key_pair_info = None
instance_id = None
instance_state = None

parser = argparse.ArgumentParser(description='CLI to compile python dependencies for AWS Lambda')
parser.add_argument('-p', '--profile', dest='aws_profile', metavar="AWS_PROFILE", help="AWS Profile")
parser.add_argument('-d', '--dry-run', action='store_true', help="Dry run")
parser.add_argument('-s', '--stop', action='store_true', help="Stop when done")
parser.add_argument('-t', '--terminate', action='store_true', help="Terminate instance and delete key")

args = parser.parse_args()

if __name__ == '__main__':

    session = boto3.Session( profile_name=args.aws_profile )
    ec2 = session.resource('ec2')
    client = session.client('ec2')

    ###############################################
    # KeyPair
    ###############################################

    try:
        key_pair_info = ec2.KeyPair(key_name)
        key_pair_info.load()
        logger.info( "Using key with fingerprint:")
        logger.info( key_pair_info.key_fingerprint )
    except:
        r = client.create_key_pair(KeyName=key_name)
        try:
            with open (key_name + '.pem', 'w') as f:
                f.write(r['KeyMaterial'])

            logger.info( "New key created." )

            key_pair_info = ec2.KeyPair(key_name)
            key_pair_info.load()
            logger.info( "Using key with fingerprint:")
            logger.info( key_pair_info.key_fingerprint )
        except:
            client.delete_key_pair(KeyName=key_name)
            logger.error("Unable to write key file. Deleted key.")

    ###############################################
    # Create Instance
    ###############################################

    r = client.describe_instances(Filters=[{'Name':'key-name', 'Values': [key_name]}])
    if len(r['Reservations']) > 0:
        for res in r['Reservations']:
            for ins in res['Instances']:
                ins_id = ins['InstanceId']
                ins_state = ins['State']['Name']
                logger.info('Checking... Instance %s is %s' % (ins_id, ins_state))
                if ins_state not in ('shutting-down', 'terminated'):
                    instance_id = ins_id
                    instance_state = ins_state
                    logger.info("Instance %s is %s" % (instance_id, instance_state))
    
    if instance_id == None:
        if args.terminate:
            logger.info('No instance found. Not creating a new one.')
            sys.exit()
        else:
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
                logger.info("Instance %s is %s" % (instance_id, instance_state))
            except:
                logger.error("Unable to create AWS instance.")

    if instance_state in ('shutting-down'):
        waiter = client.get_waiter('instance_terminated')
        waiter.wait(InstanceIds=[instance_id])
        instance_state = 'terminated'
        logger.info('Instance %s terminated.' % (instance_id))

    if instance_state in ('terminated'):
        logger.info('Instance %s terminated.' % (instance_id))

    if instance_state in ('stopping'):
        waiter = client.get_waiter('instance_stopped')
        waiter.wait(InstanceIds=[instance_id])
        instance_state = 'stopped'
        logger.info('Instance %s stopped.' % (instance_id))

    if instance_state in ('stopped'):
        if args.terminate:
            r = client.terminate_instances(InstanceIds=[instance_id])
            if len(r['TerminatingInstances']) > 0:
                instance_state = r['TerminatingInstances'][0]['CurrentState']['Name']
                logger.info("Instance %s is %s" % (instance_id, instance_state))
            else:
                logger.error('Instance %s was stopped, but could not be terminated' % (instance_id))
        else:
            if not args.stop:
                r = client.start_instances(InstanceIds=[instance_id])
                if len(r['StartingInstances']) > 0:
                    instance_state = r['StartingInstances'][0]['CurrentState']['Name']
                    logger.info("Instance %s is %s" % (instance_id, instance_state))
                else:
                    logger.error('Instance %s was stopped, but could not be started' % (instance_id))

    if instance_state in ('pending'):
        waiter = client.get_waiter('instance_running')
        waiter.wait(InstanceIds=[instance_id])
        logger.info('Instance %s running.' % (instance_id))


    if args.terminate:
        r = client.terminate_instances(InstanceIds=[instance_id])
        if len(r['TerminatingInstances']) > 0:
            instance_state = r['TerminatingInstances'][0]['CurrentState']['Name']
            logger.info("Instance %s is %s" % (instance_id, instance_state))

            key_pair_info.delete()
            logger.info('Deleted key.')
        else:
            logger.error('Instance %s was stopped, but could not be terminated' % (instance_id))



    if args.stop and instance_state not in ('stopped', 'shutting-down', 'terminated'):
        r = client.stop_instances(InstanceIds=[instance_id])
        if len(r['StoppingInstances']) > 0:
            instance_state = r['StoppingInstances'][0]['CurrentState']['Name']
            logger.info("Instance %s is %s" % (instance_id, instance_state))

            if instance_state in ('stopping'):
                waiter = client.get_waiter('instance_stopped')
                waiter.wait(InstanceIds=[instance_id])
                instance_state = 'stopped'
                logger.info('Instance %s stopped.' % (instance_id))
            else:
                logger.warning('Unexpected... Instance %s is %s' % (instance_id, instance_state))
        else:
            logger.error('Instance %s was running, but could not be stopped' % (instance_id))


