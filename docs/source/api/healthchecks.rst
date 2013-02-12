Health checks
=============

Health checks are used to test the status of some services at runtime.

Result is exposed in an URL that can be given to a monitoring solution based on HTTP status code, providing a quick health check of your API.

Configuration
-------------

Your configuration file can have a `healthchecks` section that has a dictionary of services to check. See following example.

.. code-block::

    healthchecks:
        Places index:
            moxie.core.search.SearchService:
                backend_uri: 'solr+http://url/solr/places'
        Events index:
            moxie.core.search.SearchService:
                backend_uri: 'solr+http://url/solr/events'


Defining an health check on a service
-------------------------------------

A method `healthcheck` will be called on every service defined in the configuration section `healthchecks`.

This method shouldn't take any argument, and should return a tuple with:

- a boolean value True / False: True if the service answered as expected, else False
- a string that represents a "friendly" message to represent the answer of the service

The code below is an example from a check to the search server Apache Solr.

.. code-block::

    def healthcheck(self):
        try:
            response = requests.get('{url}{core}/{method}'.format(url=self.server_url,
                core=self.core, method=self.methods['healthcheck']), timeout=2,
                config={'danger_mode': True})
            return response.ok, response.json['status']
        except Exception as e:
            return False, e


Running health checks
---------------------

Health checks are available at `/_health` and are exposed as a list (in plain text) with the status of each service.

The response has a status code of 200 if all services returned a correct value, otherwise the status code will be 500.


Inspired from `Dropwizard Health Checks <http://dropwizard.codahale.com/manual/core/#health-checks>`_.
