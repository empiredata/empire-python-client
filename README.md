Installation
============

```sh
virtualenv ./ENV
source ./ENV/bin/activate
pip install -r requirements.txt
```

Usage
=====

`./example.py YOUR_APP_KEY empire_service_secrets.yaml`

where `empire_service_secrets.yaml` was downloaded from [https://login.empiredata.co](https://login.empiredata.co)

Testing
=======

```sh
nosetests --with-coverage --cover-package=empire empire.tests
```
