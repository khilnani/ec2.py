# ec2.py

> Simple CLI / module to create/start/stop EC2 instances

Pypi Link: https://pypi.python.org/pypi/ec2.py

Features:

- Single command creation of security key and instance
- Idempotent, repeated calls do not result in multiple instances
- Waits for AWS task to complete and provides confirmation.

Supports:

- AWS Profiles
- Instance type specification
- Key generation
- Start/stop/terminate Instances

## Notes

By design, the application binds instance creation to a key file (custom name can be specified). 
This allows enhanced security around managing the life cycle of an instance,
but requires creation of more than one keyfile for multiple instances.

## Installation

- Install:
    - `pip install ec2.py --upgrade`

## Setup

- Configure AWS Credentials: `aws configure`
    - Install AWS CLI: `pip install --upgrade --user awscli`
    - See
        - http://docs.aws.amazon.com/cli/latest/userguide/installing.html
        - http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html

## Usage

- `ec2` - Creates a new AWS instance of t2.nano, and a new Key ec2.py if either do not exist. If these already exist, will start the instance if stopped.
- `ec2 -s` - Stop the instance. If one does not exist, will create a key and new instance.
- `ec2 -r` - Remove the instance (terminates) and delete the key.
- `ec2 -i` - Print the public dns name. Allows calling from another bash script.
- `ec2 -i -v` - Print the instance type, ami image, public ip address, public dns name.
- `ec2 -p myProfile -k myKey -t t2.medium` - Use a custom profile, key name and instance type.
- `ec2 -h` - Help



## Developer Setup

- Install VirtualEnvWrapper
    - `sudo pip install virtualenvwrapper --upgrade`
    - `echo "source /usr/local/bin/virtualenvwrapper.sh" >> ~/.bashrc"`
- Create / switch to Virtual Env
    - `mkvirtualenv ec2` or `workon ec2`
- Setup
    - `make setup`

## AMI Info

- AMI used: amzn-ami-hvm-2016.03.3.x86_64-gp2 (ami-6869aa05)
- Selected based on compatability with AWS Lambda environment

## Articles

- http://www.perrygeo.com/running-python-with-compiled-code-on-aws-lambda.html
- https://markn.ca/2015/10/python-extension-modules-in-aws-lambda/

## Links

- http://docs.aws.amazon.com/lambda/latest/dg/current-supported-versions.html
- http://boto3.readthedocs.io/en/latest/reference/services/ec2.html
