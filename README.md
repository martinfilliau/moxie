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

* Solr 4 BETA
* Redis
* pip (`easy_install pip`)

How to run
----------

Installation

* `pip install -r requirements.txt`

Running the application

* `celery worker --app moxie.worker`
* `python runserver.py` (you can also run it with a profiler: `python runserver.py --profiler`)

Periodically, and the first time, you have to run importers to import data into the search index.
You can do this via a Python shell:

    >>> from moxie.places.tasks import import_all
    >>> import_all.delay()


