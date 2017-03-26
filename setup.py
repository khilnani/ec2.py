#! /usr/bin/env python
#! -*- coding: utf-8 *-*-

from setuptools import setup, find_packages

readme = open('README.md', 'r').read()
setup(
    name='ec2.py',
    version='0.1.4',
    url='https://github.com/khilnani/ec2.py',
    license='MIT',
    author='khilnani',
    author_email='nik@khilnani.org',
    description='Simple CLI / module to create/start/stop EC2 instances',
    include_package_data=True,
    package_data={'ec2': ['logging.ini']},
    long_description=readme,
    packages=find_packages(),
    install_requires=['boto3'],
    entry_points={
        'console_scripts': [
            'ec2 = ec2.main:main',
            ]
    },
    keywords=('utility', 'api', 'ec2', 'aws', 'helper'),
    classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Console',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: MIT License',
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: Unix',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.7',
          'Topic :: Software Development',
          'Topic :: Software Development :: Libraries',
          'Topic :: Software Development :: Libraries :: Python Modules',
    ],  
    ) 
