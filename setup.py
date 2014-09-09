from distutils.core import setup

setup(
    name='empire-client',
    version='0.3.1',
    author='UPSHOT Data, Inc.',
    author_email='hello@empiredata.co',
    url='http://empiredata.co',
    description='Python client for the Empire API',
    long_description='Empire is an API for accessing enterprise SaaS services such as Salesforce, Zendesk, Google Apps, etc. It provides a uniform, database-like interface to every service that it supports. Empire makes it easy to integrate data from multiple enterprise services into your own enterprise app.',
    download_url='https://github.com/empiredata/empire-python-client',
    license='Apache License, Version 2.0',
    packages=['empire'],
    install_requires=[
        'requests',
        'pyaml',
        'pager',
        'python-dateutil'
    ],
    test_suite='nose.collector',
)
