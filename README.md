moxie
=====

The new Mobile Oxford

Requirements
------------

* Solr 4 BETA
* Redis
* pip (`easy_install pip`)
* bundler (`sudo gem install bundler`)
* node.js and npm

How to run
----------

Installation

* `pip install -r requirements.txt`
* `bundle install`
* `npm -g install uglify-js handlebars` (-g means install globally, it will be available from your PATH).

Preparing deployment

* `make static` to generate CSS and JS files

Running the application

* `celery worker --app moxie.worker`
* `python runserver.py`

Periodically, and the first time, you have to run importers to import data into the search index.
You can do this via a Python shell:

    >>> from moxie.places.tasks import import_all
    >>> import_all.delay()

