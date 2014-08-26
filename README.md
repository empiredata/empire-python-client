Installation
============

```sh
virtualenv ./ENV
source ./ENV/bin/activate
pip install -r requirements.txt
```

Usage
=====

See `example.py`

Testing
=======

```sh
nosetests --with-coverage --cover-package=empire empire.tests
```
