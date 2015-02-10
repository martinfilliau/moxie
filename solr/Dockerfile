FROM makuk66/docker-solr
MAINTAINER Micah Martin <micahlmartin@gmail.com>

ADD ./conf/ /opt/solr/example/solr/collection1/conf/

EXPOSE 8983
CMD ["/bin/bash", "-c", "cd /opt/solr/example; java -jar start.jar"]

