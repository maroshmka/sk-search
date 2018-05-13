from elasticsearch import Elasticsearch
from utils import build_filters


class Benchmark:

    def __init__(self, num=None):
        self.es = Elasticsearch()
        self.num_of_queries = num or 1000

    def do_query(self, query, desc):
        took = []
        for i in range(self.num_of_queries):
            offers = self.es.search(index='bazos_offer', body=query)
            took.append(offers['took'])

        print('{desc} - {n}'.format(desc=desc, n=self.num_of_queries))
        print('AVG TIME - {t}ms'.format(t=sum(took)/self.num_of_queries))
        print()

    def get_base_query(self, q):
        return {
            'query': {
                'bool': {
                    'must': [
                        {
                            'multi_match': {
                                'query': q,
                                'type': 'most_fields',
                                'fields': ['title^2', 'description'],
                                "fuzziness": "AUTO",
                                "prefix_length": 3
                            },
                        },
                    ],
                    'should': [
                        {
                            'term': {'top': {'value': True, 'boost': 2}}
                        }
                    ]
                },
            },
            'highlight': {'fields': {'*': {}}}
        }

    def test_query(self):
        q = 'auto fábia škoda'
        query = self.get_base_query(q)
        self.do_query(query, 'Query')

    def test_filters_query(self):
        filters = {
            'category': ['Mobily'],
            'subcategory': [],
            'price_type': ['Cena'],
            'city': []
        }
        q = 'mobil xperia'
        query = self.get_base_query(q)
        built_filters = build_filters(filters)
        query['query']['bool']['filter'] = built_filters
        self.do_query(query, 'Filters')

    def test_autocomplete(self):
        q = 'telef'
        query = {
            'size': 10,
            "query": {
                "bool": {
                    "must": [{
                        "multi_match": {
                            'query': q,
                            'operator': 'and',
                            'fields': ['all_autocomplete'],
                        }
                    },
                    ]
                }
            },
        }
        self.do_query(query, 'Autocomplete')


if __name__ == '__main__':
    b = Benchmark()
    b.test_query()
    b.test_filters_query()
    b.test_autocomplete()
