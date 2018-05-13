def build_aggs(builder_schema):
    """
    Build aggregations based on schema.
    :param builder_schema: list of dicts
        [
            {
                'field': 'category',
                'exclude': 'Mobily'
            },
            {...}
        ]
    :return:
    """
    aggs = dict()

    for agg in builder_schema:
        field = agg['field']
        filter_param = agg['exclude']

        aggs_key = 'by_{f}'.format(f=field)
        aggs[aggs_key] = {
                'terms': {
                    'field': field,
                    'size': 10,
                }
            }
        # if some of the values are filtered, exclude them
        if filter_param:
            aggs[aggs_key]['terms']['exclude'] = filter_param

    aggs["max_price"] = {"max": {"field": "price"}}
    aggs["min_price"] = {"min": {"field": "price"}}

    return dict(aggs=aggs)


def build_filters(filters):
    """
    Build filters that are appended to bool query.
    :param filters: list of dicts
        [
            {
                'term': {'category': 'Mobily'}
            },
            {
                'terms': {'subcategory': ['sub1', 'sub2']}
            }
        ]
    :return:
    """
    result = []

    for filter_key, filter_values in filters.items():
        t = dict()
        if len(filter_values) > 1:
            t['terms'] = {filter_key: filter_values}
        elif filter_values:
            t['term'] = {filter_key: filter_values[0]}

        if t:
            result.append(t)

    return result


def get_filters_dict(request):
    """
    Returns dict that maps filters that was selected by user.
    :return:
    """
    category_filter = request.args.getlist('category')
    subcategory_filter = request.args.getlist('subcategory')
    price_type_filter = request.args.getlist('price_type')
    city_filter = request.args.getlist('city')

    filters = {
        'category': category_filter,
        'subcategory': subcategory_filter,
        'price_type': price_type_filter,
        'city': city_filter
    }
    return filters
