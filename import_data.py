import json

import argparse
from elasticsearch import Elasticsearch

INDEX_NAME = 'bazos_offer'
TYPE_NAME = 'offer_type'
LIMIT = 1000
FILE_NAME = 'data/bazos.sample.json'
STOP_WORDS = 'data/stop.words.asciifold'


def get_data():
    with open(FILE_NAME) as f:
        data = json.load(f)

    result_data = []
    for i, d in enumerate(data):
        op_dict = {
            "index": {
                "_index": INDEX_NAME,
                "_type": TYPE_NAME,
            }
        }

        # pop this field. it was appended automatically in scrapy hosting server
        d.pop('_type')

        result_data.append(op_dict)
        result_data.append(d)
        if i == LIMIT:
            break

    return result_data


def get_stop_words():
    with open(STOP_WORDS, 'r') as f:
        sw = f.read().split(',')
        sw = [word.strip() for word in sw]
    return sw[:-1]


def get_mappings():
    sk_stop_words = get_stop_words()

    return {
        'settings': {
            'analysis': {
                'filter': {
                    "lemmagen_filter_sk": {
                        "type": "lemmagen",
                        "lexicon": "sk"
                    },
                    'sk_stop': {
                        'type': 'stop',
                        'stopwords': sk_stop_words
                    },
                    "nGram_filter": {
                        "type": "nGram",
                        "min_gram": 2,
                        "max_gram": 20,
                        "token_chars": [
                            "letter",
                            "digit",
                            "punctuation",
                            "symbol"
                        ]
                    },
                },
                'analyzer': {
                    'sk_analyzer': {
                        'tokenizer': 'standard',
                        'filter': ['sk_stop',
                                   'lemmagen_filter_sk',
                                   'lowercase',
                                   'sk_stop',
                                   'asciifolding']
                    },
                    'sk_ngram_analyzer': {
                        'tokenizer': 'standard',
                        'filter': ['sk_stop',
                                   'lemmagen_filter_sk',
                                   'lowercase',
                                   'sk_stop',
                                   'asciifolding',
                                   'nGram_filter']
                    }
                }
            }
        },
        'mappings': {
            TYPE_NAME: {
                'properties': {
                    'all_autocomplete': {
                        'type': 'text',
                        'analyzer': 'sk_ngram_analyzer',
                    },
                    'author_name': {
                        'type': 'keyword',
                        'index': 'not_analyzed',
                        'copy_to': 'all_autocomplete'
                    },
                    'title': {
                        'type': 'text',
                        'analyzer': 'sk_analyzer',
                        'copy_to': 'all_autocomplete'
                    },
                    'description': {
                        'type': 'text',
                        'analyzer': 'sk_analyzer',
                    },
                    'category': {
                        'type': 'keyword',
                        "index": "not_analyzed",
                        'copy_to': 'all_autocomplete'
                    },
                    'subcategory': {
                        'type': 'keyword',
                        "index": "not_analyzed",
                        'copy_to': 'all_autocomplete'
                    },
                    'price': {
                        'type': 'float',
                        "index": "not_analyzed",
                        'copy_to': 'all_autocomplete'
                    },
                    'phone_number': {
                        'type': 'string',
                        'index': 'not_analyzed',
                        'copy_to': 'all_autocomplete'
                    },
                    'release_date': {
                        'type': 'date',
                        'format': 'dd.MM.yyyy',
                        'index': 'not_analyzed',
                        'copy_to': 'all_autocomplete'
                    },
                    'price_type': {
                        'type': 'keyword',
                        'index': 'not_analyzed'
                    },
                    'city': {
                        'type': 'keyword',
                        'index': 'not_analyzed',
                        'copy_to': 'all_autocomplete'
                    },
                    'zip_code': {
                        'type': 'string',
                        'index': 'not_analyzed',
                        'copy_to': 'all_autocomplete'
                    },
                    'seen': {
                        'type': 'integer',
                        'index': 'not_analyzed'
                    },
                    'top': {
                        'type': 'boolean',
                        'index': 'not_analyzed',
                        'include_in_all': False
                    },
                    'offer_url': {
                        'type': 'keyword',
                        'index': 'no',
                        'include_in_all': False
                    }
                }
            }
        }
    }


def refresh_all(es):
    data = get_data()

    if es.indices.exists(INDEX_NAME):
        print('Deleting index %s ' % INDEX_NAME)
        es.indices.delete(INDEX_NAME)

    print('Creating index {i_name} with type {t_name}...'
          .format(i_name=INDEX_NAME, t_name=TYPE_NAME))
    mappings = get_mappings()
    res = es.indices.create(index=INDEX_NAME, body=mappings)

    print('Inserting all data - {len}'.format(len=len(data)/2))

    # data are doubled, because there is dict about index and type for every row in data
    # so we perform bulk for 20000k - 10000k items
    j = 20000
    for i in range(0, len(data), 20000):
        res = es.bulk(index=INDEX_NAME, body=data[i:j], refresh=True)
        print('Bulk {i}-{j} inserted.'.format(i=i, j=j))
        j += 20000

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--all",
                       default=False,
                       action='store_true',
                       help="Delete index, recreate mapping in elasticsearch and load data there."
                       )    
    parser.add_argument("--limit",
                       type=int,
                       help="Limit for data"
                       )
    args = parser.parse_args()
    es = Elasticsearch('localhost:9200', timeout=30, max_retries=10, retry_on_timeout=True)

    if args.limit:
        LIMIT = args.limit
    else:
        LIMIT = 100000000000

    if args.all:
        refresh_all(es)
    else:
        print('No inputs. Use --all to recreate index.')
