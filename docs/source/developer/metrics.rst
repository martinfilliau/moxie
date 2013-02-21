Metrics
=======

Metrics are useful to understand the performances of your application.

Solr (search server) metrics
----------------------------

Display the average QTime (number of milliseconds to execute a search) of Solr from a log file:

.. code-block:: none

    cat /var/log/jetty/solr-0.log | grep QTime | awk '{print $NF}' | awk -F\= '{ s += $2} END {print s/NR}'

Display request handlers used per core:

.. code-block:: none

    cat /var/log/jetty/solr-0.log | grep path | awk '{print $2 $4}' | sort | uniq -c

Display search queries (parameter "q") which are not search for "identifiers", and not browsing (q="*:*"):

.. code-block:: none

	cat /var/log/jetty/solr-0.log | grep "places" | grep "path=/select" | grep "q=" | awk '{print substr($5,index($5,"q=")+2)}' | grep -v "identifiers" | grep -v "*:*"
