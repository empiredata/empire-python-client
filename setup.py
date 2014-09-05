from distutils.core import setup

setup(
    name='empire',
    version='0.3',
    author='UPSHOT Data, Inc.',
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
