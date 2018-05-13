from elasticsearch import Elasticsearch
from flask import Flask, render_template, request, jsonify, redirect

from utils import build_aggs, build_filters, get_filters_dict

app = Flask(__name__)


@app.route('/')
def index():
    """
    Index redirect on /search immediately.
    """
    return redirect('/search')


def build_query(q, filters):
    """
    Build query. If no q passed - return all.
    Multimatch with fuzzy + boost TOP.
    Author name more weight than description.
    Append filters if they are there.

    :param q: query text
    :param filters: dict of filters to apply. Example:

        {
            'category' : ['Mobil', 'Daco']
            'subcategory': ['a', 'b']
        }

    :return: query dict
    """

    built_filters = build_filters(filters)

    if q:
        query = {
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
        if built_filters:
            query['query']['bool']['filter'] = built_filters
    else:
        query = {
            'query': {
                'bool': {
                    'must': [
                        {
                            'match_all': {}
                        }
                    ]
                },
            },
            'sort': [
                {
                    'release_date': {'order': 'desc'},
                    'price': {'order': 'desc'}
                }
            ]
        }
        if built_filters:
            query['query']['bool']['filter'] = built_filters

            # query['filter'] = build_filters(filters)
    return query


def perform_search():
    """
    Compose query with filters.
    Add aggregations - to display it in frontend
    Fire query and return offers.
    :return: tuple (q, offers, filter)
    """
    q = request.args.get('q') or ''
    filters = get_filters_dict(request)

    es = Elasticsearch()
    query = build_query(q, filters)

    aggs = build_aggs(builder_schema=[{'field': 'category', 'exclude': filters['category']},
                                      {'field': 'subcategory', 'exclude': filters['subcategory']},
                                      {'field': 'price_type', 'exclude': filters['price_type']},
                                      {'field': 'city', 'exclude': filters['city']},
                                      ])
    query.update(aggs)
    offers = es.search(index='bazos_offer', body=query)

    return q, offers, filters


@app.route('/search')
def search():
    q, offers, filters = perform_search()
    return render_template('index.html', q=q, offers=offers, filters=filters)


@app.route('/search-ajax')
def ajax_search():
    """
    Used as ajax endpoint for filtering price and dates.
    :return:
    """
    q = request.args.get('q')
    filters = get_filters_dict(request)

    # prices
    price_from = request.args.get('price_from')
    price_to = request.args.get('price_to')

    # dates
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    query = build_query(q, filters)
    es = Elasticsearch()

    # add price filter
    price_filter = {
        'range': {
                'price': {
                    'gte': price_from,
                    'lte': price_to
                }
            }
    }

    try:
        query['query']['bool']['filter'].append(price_filter)
    except KeyError:
        query['query']['bool']['filter'] = [price_filter]

    date_filter = None
    # if one of the dates. create filter dict
    if date_from or date_to:
        # add date_filter
        date_filter = {
            'range': {
                'release_date': {

                }
            }
        }

    # append filters
    if date_from:
        date_filter['range']['release_date']['gte'] = date_from
    if date_to:
        date_filter['range']['release_date']['lte'] = date_to

    if date_filter:
        try:
            query['query']['bool']['filter'].append(date_filter)
        except KeyError:
            query['query']['bool']['filter'] = [date_filter]

    offers = es.search(index='bazos_offer', body=query)
    return render_template('results.html', offers=offers)


@app.route('/autocomplete')
def autocomplete():
    """
    Endpoint for autocomplete.
    It returns first 10 best matched documents from field `all_autocomplete` -> see mappings in
    `import_data.py` to see whats in there.
    """
    es = Elasticsearch()
    q = request.args.get('q') or ''
    filters = get_filters_dict(request)
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
    if filters:
        query['query']['bool']['filter'] = build_filters(filters)

    results = es.search(index='bazos_offer', body=query)
    str_list_results = format_results_for_autocomplete(results)

    return jsonify(matching_results=str_list_results)


def format_results_for_autocomplete(results):
    """
    Formats results from autocomplete match to string representation.
    :param results: results from autocomplete query
    :return: list of dicts
        [
            {
                'value': 'I am a title'
                'label': 'I am a title | 50 € | 0911238987'
            }
        ]
    """
    formated = []
    for result in results['hits']['hits']:
        tmp = ''
        # tmp += result['_source']['category'] + ' | ' + result['_source']['subcategory']
        tmp += result['_source']['title']
        tmp += ' | ' + result['_source']['price'] + ' €'
        # tmp += ' | ' + result['_source']['release_date']
        tmp += ' | ' + result['_source']['phone_number']

        item = {
            'value': result['_source']['title'],
            'label': tmp
        }
        formated.append(item)
    return formated


@app.context_processor
def highlight():
    """
    Filter used in jinja templates to highlight fields
    """
    def _highlight(hit, field):
        return do_highlight(hit, field)
    return dict(highlight=_highlight)


def do_highlight(hit, field):
    if 'highlight' not in hit:
        return hit['_source'][field]
    return hit['highlight'][field][0] if field in hit['highlight'] else hit['_source'][field]


@app.context_processor
def get_buckets():
    """
    Filter used in jinja templates to get aggregations buckets.
    """
    def _get_buckets(offers, field):
        name = f'by_{field}'
        return offers['aggregations'][name]['buckets']
    return dict(get_buckets=_get_buckets)
