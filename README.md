moxie
=====

[![Build Status](https://secure.travis-ci.org/ox-it/moxie.png)](http://travis-ci.org/ox-it/moxie)



The new Mobile Oxford

This repository contains the (server-side) JSON API.

Documentation
-------------

Available at [Read the docs](http://moxie.readthedocs.org/en/latest/)

Documentation is also available at `/docs` in the repo, you need to install required packages (Sphinx) from `requirements_dev.txt`.

You can generate HTML documentation by running `make html` inside the `docs` directory.

Requirements
------------

* Solr 4.4
* Redis
* libgeos2
* pip (`easy_install pip`)

How to run
----------

Installation

* `pip install -r requirements.txt`

Running the application

* `celery worker --app moxie.worker`
* `python runserver.py`

Options available for runserver.py

* run with a profiler: `python runserver.py --profiler`
* specify the logging level (INFO by default): `python runserver.py --log-level DEBUG`

Periodically, and the first time, you have to run importers to import data into the search index.
You can do this via a Python shell:

    >>> from moxie.places.tasks import import_all
    >>> import_all.delay()

Deploying with Fabric
---------------------

Steps:

* Add your public SSH key to /srv/moxie/.ssh/authorized_keys
* Execute the fabric script on your local machine, which will then connect to the designated server and run the pre-programmed tasks:

 `fab deploy_api:GIT_BRANCH -g USER@GATEWAY -H moxie@PRIVATE_IP`

 For example: 

 `fab deploy_api:master -g martinfilliau@mox-api-front.oucs.ox.ac.uk -H moxie@192.168.2.102`

* Optional: Use an ssh_config file to define the gateway to and provide aliases for machines behind the front-end server, and the user to connect as. Then the -g flag and username become unnecessary and memorable hostnames can be used instead of IP addresses:

 `fab deploy_api:master -H mox-api-1.oucs.ox.ac.uk`

 See [puppet/fabric/ubuntu-ssh/ssh_config](https://github.com/ox-it/puppet/blob/master/fabric/ubuntu-ssh/ssh_config) for examples.