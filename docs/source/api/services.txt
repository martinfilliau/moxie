Service
=======

Services are HTTP (transport layer) agnostic instead operating at the Application Layer. Services encapsulate all operations made on the data. Views should never directly access data sources without going through a Service.

Configuration of services can be done for each Blueprint. Within the `Application context <http://flask.pocoo.org/docs/appcontext/>`_ they will be cached, this means the following code accesses the same Service object.::

    with app.app_context():
        service_one = MyService.from_context()
        service_two = MyService.from_context()
        assert(service_one is service_two)
