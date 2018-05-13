FROM docker.elastic.co/elasticsearch/elasticsearch:5.4.0

RUN ./bin/elasticsearch-plugin remove x-pack
ENV VERSION=5.4.0
RUN ./bin/elasticsearch-plugin install https://github.com/vhyza/elasticsearch-analysis-lemmagen/releases/download/v$VERSION/elasticsearch-analysis-lemmagen-$VERSION-plugin.zip
