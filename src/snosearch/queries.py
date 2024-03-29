from collections import OrderedDict
from opensearch_dsl import A
from opensearch_dsl import Q
from opensearch_dsl import Search
from antlr4 import IllegalStateException
from lucenequery import dialects
from lucenequery.prefixfields import prefixfields


from .adapters.exceptions import get_default_exception
from .configs import ExistsAggregationConfig
from .configs import TermsAggregationConfig
from .decorators import assert_none_returned
from .decorators import assert_one_returned
from .decorators import assert_one_or_none_returned
from .decorators import assert_something_returned
from .decorators import deduplicate
from .defaults import AUDIT_FIELDS
from .defaults import BASE_AUDIT_FACETS
from .defaults import BASE_COLUMNS
from .defaults import BASE_FIELD_FACETS
from .defaults import BASE_RETURN_FIELDS
from .defaults import BASE_SEARCH_FIELDS
from .defaults import DEFAULT_COLUMNS
from .defaults import DEFAULT_FRAMES
from .defaults import DEFAULT_SCAN_SIZE
from .defaults import DEFAULT_SORT
from .defaults import DEFAULT_SORT_OPTIONS
from .defaults import INTERNAL_AUDIT_FACETS
from .defaults import MAX_ES_RESULTS_WINDOW
from .defaults import NOT_FILTERS
from .interfaces import ALL
from .interfaces import AND
from .interfaces import AND_JOIN
from .interfaces import AND_NOT_JOIN
from .interfaces import ASC
from .interfaces import AUDIT
from .interfaces import BOOL
from .interfaces import BOOST_VALUES
from .interfaces import COLLECTION_NAME
from .interfaces import COLON
from .interfaces import COLUMNS
from .interfaces import DASH
from .interfaces import DESC
from .interfaces import ELASTIC_SEARCH
from .interfaces import EMBEDDED
from .interfaces import EMBEDDED_TYPE
from .interfaces import EXCLUDE
from .interfaces import EXISTS
from .interfaces import FACETS
from .interfaces import FILTERS
from .interfaces import FROM_KEY
from .interfaces import GROUP_BY
from .interfaces import GROUP_SUBMITTER
from .interfaces import ITEM
from .interfaces import LIMIT_KEY
from .interfaces import LENGTH
from .interfaces import LONG
from .interfaces import MATRIX
from .interfaces import MAX
from .interfaces import MAX_SCORE
from .interfaces import MUST
from .interfaces import MUST_NOT
from .interfaces import NOT_EXISTS
from .interfaces import NOT_JOIN
from .interfaces import NOT_RANGES
from .interfaces import NO
from .interfaces import NO_LIMIT
from .interfaces import ORDER
from .interfaces import PERIOD
from .interfaces import PICKER
from .interfaces import PRINCIPALS_ALLOWED_VIEW
from .interfaces import PROPERTIES
from .interfaces import QUERY_STRING
from .interfaces import RANGE
from .interfaces import RANGES
from .interfaces import RESOURCES_INDEX
from .interfaces import _SCORE
from .interfaces import SEARCH_AUDIT
from .interfaces import SEARCH_CONFIG
from .interfaces import SIMPLE_QUERY_STRING
from .interfaces import _SOURCE
from .interfaces import STATS
from .interfaces import TITLE
from .interfaces import TERMS
from .interfaces import TOP_HITS
from .interfaces import TYPES
from .interfaces import TYPE_KEY
from .interfaces import WILDCARD
from .interfaces import X
from .interfaces import Y
from .interfaces import YES


class AbstractQueryFactory:
    '''
    Interface for building specific queries. Don't change functionality here, instead
    inherit and extend/override functions as needed.
    '''

    def __init__(self, params_parser, *args, **kwargs):
        self.search = None
        self.params_parser = params_parser
        self.args = args
        self.kwargs = kwargs

    def _get_or_create_search(self):
        if self.search is None:
            self.search = Search(
                using=self._get_client(),
                index=self._get_index(),
            )
        return self.search

    def _get_client(self):
        return self.kwargs.get('client') or self.params_parser._request.registry[ELASTIC_SEARCH]

    def _get_index(self):
        if self._should_search_over_all_indices():
            return [RESOURCES_INDEX]
        return self._get_collection_names_for_item_types(
            self._resolve_abstract_types_to_subtypes(
                self.params_parser.param_values_to_list(
                    params=self._get_item_types()
                )
            )
            or self.params_parser.param_values_to_list(
                params=self._get_default_item_types()
            )
        )

    def _get_principals(self):
        return self.params_parser._request.effective_principals

    def _get_search_config_registry(self):
        return self.params_parser._request.registry[SEARCH_CONFIG]

    def _get_registered_types(self):
        return self.params_parser._request.registry[TYPES]

    def _get_factory_for_item_type(self, item_type):
        return self._get_registered_types()[item_type].factory

    def _get_schema_for_item_type(self, item_type):
        return self._get_registered_types()[item_type].schema

    def _get_search_config_for_item_type(self, item_type):
        return self._get_search_config_registry().get(
            item_type,
            {}
        )

    def _get_search_configs_by_names(self, names, use_defaults=True):
        return self._get_search_config_registry().get_configs_by_names(
            names,
            use_defaults=use_defaults
        )

    def _get_subtypes_for_item_type(self, item_type):
        return self._get_registered_types()[item_type].subtypes

    def _get_name_for_item_type(self, item_type):
        return self._get_registered_types()[item_type].name

    def _get_collection_name_for_item_type(self, item_type):
        return getattr(
            self._get_registered_types()[item_type],
            COLLECTION_NAME,
            None
        )

    def _get_properties_for_item_type(self, item_type):
        return self._get_schema_for_item_type(item_type).get(PROPERTIES, {})

    def _get_boost_values_for_item_type(self, item_type):
        return self._get_schema_for_item_type(item_type).get(BOOST_VALUES, {})

    def _get_config_param_values(self):
        return self.kwargs.get(
            'config',
            self.params_parser.param_values_to_list(
                params=self.params_parser.get_config()
            )
        )

    def _get_configs_from_config_param_values(self):
        return self._get_search_configs_by_names(
            self._get_config_param_values(),
            use_defaults=False,
        )

    def _get_configs_from_item_types_as_combined_key(self):
        # Passing all the item types as one key.
        return self._get_search_configs_by_names(
            [
                tuple(
                    self.params_parser.param_values_to_list(
                        params=self._get_item_types()
                    )
                )
            ]
        )

    def _get_configs_from_item_types_as_individual_keys(self):
        return self._get_search_configs_by_names(
            self.params_parser.param_values_to_list(
                params=self._get_item_types()
            )
        )

    def _get_configs_from_default_item_types_as_individual_keys(self):
        return self._get_search_configs_by_names(
            self.params_parser.param_values_to_list(
                params=self._get_default_item_types()
            )
        )

    def _get_configs_from_param_values_or_item_types_as_combined_key(self):
        return (
            self._get_configs_from_config_param_values() or
            self._get_configs_from_item_types_as_combined_key()
        )

    def _extract_columns_from_configs(self, configs):
        return {
            k: v
            for config in configs
            for k, v in config.columns.items()
        }

    def _extract_facets_from_configs(self, configs):
        return [
            facet
            for config in configs
            for facet in config.facets.items()
        ]

    def _extract_matrix_from_configs(self, configs):
        for config in configs:
            if config.matrix:
                return config.matrix

    def _get_base_columns(self):
        return OrderedDict(BASE_COLUMNS)

    def _get_default_columns_for_item_type(self, item_type):
        properties = self._get_properties_for_item_type(item_type)
        return {
            k: v
            for k, v in DEFAULT_COLUMNS.items()
            if k in properties
        }

    def _get_columns_for_item_type(self, item_type):
        return self._get_search_config_for_item_type(item_type).get(COLUMNS, {})

    def _get_columns_for_item_types(self, item_types=None):
        columns = self._get_base_columns()
        item_type_values = item_types or self.params_parser.param_values_to_list(
            params=self._get_item_types() or self._get_default_item_types()
        )
        for item_type in item_type_values:
            columns.update(
                self._get_columns_for_item_type(item_type)
                or self._get_default_columns_for_item_type(item_type)
            )
        return columns

    def _get_columns_from_configs_or_item_types(self):
        columns = self._get_base_columns()
        columns.update(
            self._extract_columns_from_configs(
                self._get_configs_from_config_param_values()
            )
            or self._extract_columns_from_configs(
                self._get_configs_from_item_types_as_combined_key()
            )
            or self._get_columns_for_item_types()
        )
        return columns

    def _get_invalid_item_types(self, item_types):
        registered_types = self._get_registered_types()
        return [
            item_type
            for item_type in item_types
            if item_type not in registered_types
        ]

    def _normalize_item_types(self, item_types):
        return [
            self._get_name_for_item_type(item_type)
            for item_type in item_types
        ]

    def _get_collection_names_for_item_types(self, item_types):
        return [
            self._get_collection_name_for_item_type(item_type)
            for item_type in item_types
            if self._get_collection_name_for_item_type(item_type)
        ]

    def _escape_regex_slashes(self, query):
        return query.replace('/', '\\/')

    def _escape_fuzzy_tilde(self, query):
        return query.replace('~', '\\~')

    def _escape_boost_caret(self, query):
        return query.replace('^', '\\^')

    def _escape_reserved_query_string_characters(self, query):
        '''
        Removes some of the sharp edges of query strings from
        invalid user input.
        '''
        return self._escape_regex_slashes(
            self._escape_fuzzy_tilde(
                self._escape_boost_caret(
                    query
                )
            )
        )

    def _validated_query_string_query(self, query):
        try:
            query = prefixfields(EMBEDDED, query, dialects.elasticsearch)
        except IllegalStateException:
            msg = "Invalid query: {}".format(query)
            raise get_default_exception()(explanation=msg)
        return query.getText()

    def _get_default_item_types(self):
        mode = self.params_parser.get_one_value(
            params=self._get_mode()
        )
        if mode == PICKER:
            item_types = [ITEM]
        else:
            item_types = self.kwargs.get('default_item_types', [])
        return [
            (TYPE_KEY, item_type)
            for item_type in item_types
        ]

    def _wildcard_in_item_types(self, item_types):
        return self.params_parser.is_param(
            TYPE_KEY,
            WILDCARD,
            params=item_types
        )

    def _get_item_types(self):
        item_types = self.params_parser.get_type_filters()
        if self._wildcard_in_item_types(item_types):
            return [(TYPE_KEY, ITEM)]
        return item_types

    def _show_internal_audits(self):
        conditions = [
            self.params_parser._request.has_permission(SEARCH_AUDIT),
            GROUP_SUBMITTER in self._get_principals()
        ]
        return all(conditions)

    def _get_audit_facets(self):
        if self._show_internal_audits():
            return BASE_AUDIT_FACETS.copy() + INTERNAL_AUDIT_FACETS.copy()
        return BASE_AUDIT_FACETS.copy()

    def _get_default_facets(self):
        return self.kwargs.get(
            'default_facets',
            BASE_FIELD_FACETS.copy()
        )

    def _get_facets_from_configs(self):
        return (
            self._extract_facets_from_configs(
                self._get_configs_from_config_param_values()
            )
            or self._extract_facets_from_configs(
                self._get_configs_from_item_types_as_combined_key()
            )
        )

    def _get_default_and_maybe_item_facets(self):
        facets = self._get_default_facets()
        facets.extend(self._get_facets_from_configs())
        # Add these at end.
        facets.extend(self._get_audit_facets())
        return facets

    def _get_simple_query_string_query(self):
        return self._combine_search_term_queries(
            must_match_filters=self.params_parser.get_must_match_search_term_filters(),
            must_not_match_filters=self.params_parser.get_must_not_match_search_term_filters()
        )

    def _get_query_string_query(self):
        return self._combine_search_term_queries(
            must_match_filters=self.params_parser.get_must_match_advanced_query_filters(),
            must_not_match_filters=self.params_parser.get_must_not_match_advanced_query_filters()
        )

    def _get_reserved_keys(self):
        return self.kwargs.get('reserved_keys', NOT_FILTERS.copy())

    def _get_filters(self):
        return self.params_parser.get_not_keys_filters(
            not_keys=self._get_reserved_keys()
        )

    def _get_post_filters(self):
        return self.kwargs.get(
            'post_filters',
            self._get_filters() + self._get_item_types()
        )

    def _make_sort_key(self, key, prefix=EMBEDDED):
        return self._prefix_value(prefix, key)

    def _make_sort_value(self, order):
        sort_value = DEFAULT_SORT_OPTIONS.copy()
        sort_value[ORDER] = order
        return sort_value

    def _make_sort_key_and_value(self, key):
        if key.startswith(DASH):
            k, order = key[1:], DESC
        else:
            k, order = key, ASC
        return {
            self._make_sort_key(k): self._make_sort_value(order)
        }

    def _get_default_sort(self):
        if self._should_add_default_sort():
            return [
                self._make_sort_key_and_value(key)
                for key in self.kwargs.get('default_sort') or DEFAULT_SORT
            ]

    def _get_sort(self):
        return [
            self._make_sort_key_and_value(key)
            for key in self.params_parser.param_values_to_list(
                    params=self.params_parser.get_sort()
            )
        ]

    def _get_default_from(self):
        return [(FROM_KEY, 0)]

    @assert_one_or_none_returned(error_message='Invalid to specify multiple from parameters:')
    def _get_from(self):
        return self.params_parser.get_from() or self._get_default_from()

    def _get_from_value_as_int(self):
        from_ = self.params_parser.coerce_value_to_int_or_return_none(
            self.params_parser.get_one_value(
                params=self._get_from()
            )
        )
        if from_ is None:
            return self.params_parser.get_one_value(
                params=self._get_default_from()
            )
        return from_

    def _get_default_limit(self):
        return [(LIMIT_KEY, 25)]

    def _get_max_result_window(self):
        return self.kwargs.get('max_result_window', MAX_ES_RESULTS_WINDOW)

    def _get_scan_size(self):
        return self.kwargs.get('scan_size', DEFAULT_SCAN_SIZE)

    @assert_one_or_none_returned(error_message='Invalid to specify multiple limit parameters:')
    def _get_limit(self):
        return self.params_parser.get_limit() or self._get_default_limit()

    def _get_limit_value(self):
        return self.params_parser.maybe_int(
            self.params_parser.get_one_value(
                params=self._get_limit()
            )
        )

    def _get_limit_value_as_int(self):
        limit = self.params_parser.coerce_value_to_int_or_return_none(
            self._get_limit_value()
        )
        if limit is None:
            return self.params_parser.get_one_value(
                params=self._get_default_limit()
            )
        return limit

    def _limit_is_all(self):
        return self._get_limit_value() == ALL

    def _limit_is_over_maximum_window(self):
        limit = self._get_limit_value_as_int()
        if limit:
            return limit > self._get_max_result_window()
        return False

    def _should_scan_over_results(self):
        conditions = [
            self._limit_is_all(),
            self._limit_is_over_maximum_window()
        ]
        return any(conditions)

    def _should_add_default_sort(self):
        conditions = [
            not self.params_parser.get_search_term_filters(),
            not self.params_parser.get_advanced_query_filters()
        ]
        return all(conditions)

    def _should_search_over_all_indices(self):
        conditions = [
            not self._get_item_types(),
            self.params_parser.is_param(
                TYPE_KEY,
                ITEM,
                params=self._get_item_types() or self._get_default_item_types()
            )
        ]
        return any(conditions)

    def _get_bounded_limit_value_or_default(self):
        if self._should_scan_over_results():
            return 0
        return self._get_limit_value_as_int()

    @assert_one_or_none_returned(error_message='Invalid to specify multiple mode parameters:')
    def _get_mode(self):
        return self.params_parser.get_mode()

    @assert_one_or_none_returned(error_message='Invalid to specify multiple frame parameters:')
    def _get_frame(self):
        return self.params_parser.get_frame()

    def _get_frame_value(self):
        return self.params_parser.get_one_value(
            params=self._get_frame()
        )

    def _get_fields(self):
        return self.params_parser.get_field_filters()

    def _get_search_fields(self):
        return self.kwargs.get('search_fields', BASE_SEARCH_FIELDS.copy())

    def _get_return_fields_from_field_params(self, fields):
        return self.params_parser.param_values_to_list(
            params=self._map_param_values_to_elasticsearch_fields(fields)
        )

    def _get_return_fields_from_schema_columns(self):
        columns = self._get_columns_from_configs_or_item_types()
        return self._prefix_values(
            EMBEDDED,
            [c for c in columns]
        )

    @deduplicate
    def _get_return_fields(self):
        # Copy to avoid modifying template.
        return_fields = BASE_RETURN_FIELDS.copy()
        fields = self._get_fields()
        frame = self._get_frame_value()
        if fields:
            return return_fields + self._get_return_fields_from_field_params(fields)
        elif frame in DEFAULT_FRAMES:
            return_fields = [frame + PERIOD + WILDCARD]
        else:
            return_fields.extend(self._get_return_fields_from_schema_columns())
        return return_fields + [AUDIT + PERIOD + WILDCARD]

    def _get_facets(self):
        return self.kwargs.get('facets', self._get_default_and_maybe_item_facets())

    def _get_facet_size(self):
        return self.kwargs.get('facet_size')

    def _prefix_value(self, prefix, value):
        return prefix + value

    def _prefix_values(self, prefix, values):
        return [
            self._prefix_value(prefix, v)
            for v in values
        ]

    def _combine_search_term_queries(self, must_match_filters=[], must_not_match_filters=[]):
        must = AND_JOIN.join(['{}'.format(q[1]) for q in must_match_filters])
        must_not = AND_NOT_JOIN.join(['{}'.format(q[1]) for q in must_not_match_filters])
        if must and must_not:
            return must + AND_NOT_JOIN + must_not
        elif must:
            return must
        elif must_not:
            return NOT_JOIN.lstrip() + must_not

    def _make_simple_query_string_query(self, query, fields, default_operator=AND):
        return Q(
            SIMPLE_QUERY_STRING,
            query=query,
            fields=fields,
            default_operator=default_operator
        )

    def _make_query_string_query(self, query, fields, default_operator=AND):
        return Q(
            QUERY_STRING,
            query=query,
            fields=fields,
            default_operator=default_operator
        )

    def _make_bool_query(self, **kwargs):
        return Q(
            BOOL,
            **kwargs
        )

    def _make_queries_from_params(self, query_context, params):
        return [
            query_context(
                field=self._map_param_to_elasticsearch_field(field),
                terms=terms
            )
            for field, terms in self.params_parser.group_values_by_key(
                    self.params_parser.remove_not_flag(
                        params=params
                    )
            ).items()
        ]

    def _make_must_equal_terms_query(self, field, terms, **kwargs):
        return Q(
            TERMS,
            **{field: terms}
        )

    def _make_must_equal_terms_queries_from_params(self, params):
        return self._make_queries_from_params(
            query_context=self._make_must_equal_terms_query,
            params=params
        )

    def _make_field_must_exist_query(self, field, **kwargs):
        return Q(
            EXISTS,
            field=field
        )

    def _make_field_must_exist_queries_from_params(self, params):
        return self._make_queries_from_params(
            query_context=self._make_field_must_exist_query,
            params=params
        )

    @staticmethod
    def _convert_terms_to_range_syntax(terms):
        return dict(
            term.split(COLON, 1)
            for term in terms
        )


    def _make_range_query(self, field, terms, **kwargs):
        return Q(
            RANGE,
            **{
                field: self._convert_terms_to_range_syntax(terms)
            }
        )

    def _make_range_queries_from_params(self, params):
        return self._make_queries_from_params(
            query_context=self._make_range_query,
            params=params
        )

    def _make_default_filters(self):
        return [
            self._make_must_equal_terms_query(
                field=PRINCIPALS_ALLOWED_VIEW,
                terms=self._get_principals()
            ),
            self._make_must_equal_terms_query(
                field=EMBEDDED_TYPE,
                terms=(
                    self.params_parser.param_values_to_list(
                        params=self.params_parser.get_must_match_filters(
                            params=self._get_item_types()
                        )
                    )
                    or self.params_parser.param_values_to_list(
                        params=self._get_default_item_types()
                    )
                )
            )
        ]

    def _make_split_filter_queries(self, params=None):
        '''
        Returns appropriate queries from param filters.
        '''
        split_filters = self.params_parser.split_filters(
            params=params or self._get_post_filters()
        )
        must = self._make_must_equal_terms_queries_from_params(
            split_filters[MUST]
        )
        must_not = self._make_must_equal_terms_queries_from_params(
            split_filters[MUST_NOT]
        )
        exists = self._make_field_must_exist_queries_from_params(
            split_filters[EXISTS]
        )
        not_exists = self._make_field_must_exist_queries_from_params(
            split_filters[NOT_EXISTS]
        )
        ranges = self._make_range_queries_from_params(
            split_filters[RANGES]
        )
        not_ranges = self._make_range_queries_from_params(
            split_filters[NOT_RANGES]
        )
        return must, must_not, exists, not_exists, ranges, not_ranges

    def _make_terms_aggregation(self, field, **kwargs):
        return A(
            TERMS,
            field=field,
            **TermsAggregationConfig(**kwargs)
        )

    def _make_exists_aggregation(self, field, **kwargs):
        return A(
            FILTERS,
            filters={
                YES: Q(EXISTS, field=field),
                NO: ~Q(EXISTS, field=field)
            },
            **ExistsAggregationConfig(**kwargs)
        )

    def _make_stats_aggregation(self, field, **kwargs):
        return A(
            STATS,
            field=field
        )

    def _make_filter_aggregation(self, filter_context, **kwargs):
        return A(
            'filter',
            filter_context
        )

    def _make_filter_and_subaggregation(self, title, filter_context, subaggregation):
        a = self._make_filter_aggregation(filter_context)
        a.bucket(title, subaggregation)
        return a

    def _map_param_to_elasticsearch_field(self, param):
        '''
        Special rules for mapping param to actual field in ES.
        For exampe type -> embedded.@type.
        '''

        if param == TYPE_KEY:
            return EMBEDDED_TYPE
        elif param.startswith(AUDIT):
            return param
        else:
            return self._prefix_value(EMBEDDED, param)

    def _map_param_keys_to_elasticsearch_fields(self, params):
        '''
        Like _map_param_to_elasticsearch_field but used for iterating over keys
        in param tuples.
        '''
        for param_key, param_value in params:
            yield (
                self._map_param_to_elasticsearch_field(param_key),
                param_value
            )

    def _map_param_values_to_elasticsearch_fields(self, params):
        '''
        Like _map_param_to_elasticsearch_field but used for iterating over values
        in param tuples.
        '''
        for param_key, param_value in params:
            yield (
                param_key,
                self._map_param_to_elasticsearch_field(param_value)
            )

    def _subaggregation_factory(self, aggregation_type):
        if aggregation_type == EXISTS:
            return self._make_exists_aggregation
        elif aggregation_type == STATS:
            return self._make_stats_aggregation
        return self._make_terms_aggregation

    def _add_must_equal_terms_filter(self, field, terms):
        self.search = self._get_or_create_search().filter(
            self._make_must_equal_terms_query(
                field=field,
                terms=terms
            )
        )

    def _add_must_equal_terms_post_filter(self, field, terms):
        self.search = self._get_or_create_search().post_filter(
            self._make_must_equal_terms_query(
                field=field,
                terms=terms
            )
        )

    def _add_must_not_equal_terms_filter(self, field, terms):
        self.search = self._get_or_create_search().exclude(
            self._make_must_equal_terms_query(
                field=field,
                terms=terms
            )
        )

    def _add_must_not_equal_terms_post_filter(self, field, terms):
        self.search = self._get_or_create_search().post_filter(
            self._make_bool_query(
                filter=[
                    ~self._make_must_equal_terms_query(
                        field=field,
                        terms=terms
                    )
                ]
            )
        )

    def _add_field_must_exist_filter(self, field):
        self.search = self._get_or_create_search().query(
            self._make_bool_query(
                filter=[
                    self._make_field_must_exist_query(field=field),
                ]
            )
        )

    def _add_field_must_exist_post_filter(self, field):
        self.search = self._get_or_create_search().post_filter(
            self._make_bool_query(
                filter=[
                    self._make_field_must_exist_query(field=field),
                ]
            )
        )

    def _add_field_must_not_exist_filter(self, field):
        self.search = self._get_or_create_search().query(
            self._make_bool_query(
                filter=[
                    ~self._make_field_must_exist_query(field=field),
                ]
            )
        )

    def _add_field_must_not_exist_post_filter(self, field):
        self.search = self._get_or_create_search().post_filter(
            self._make_bool_query(
                filter=[
                    ~self._make_field_must_exist_query(field=field),
                ]
            )
        )

    def _add_terms_aggregation(self, title, field, exclude=[], size=200):
        self._get_or_create_search().aggs.bucket(
            title,
            self._make_terms_aggregation(
                field=field,
                size=size,
                exclude=exclude
            )
        )

    def _add_exists_aggregation(self, title, field):
        self._get_or_create_search().aggs.bucket(
            title,
            self._make_exists_aggregation(
                field=field
            )
        )

    def _resolve_abstract_types_to_subtypes(self, item_types):
        subtypes = set()
        for item_type in item_types:
            subtypes.update(self._get_subtypes_for_item_type(item_type))
        return list(sorted(subtypes))     

    @assert_none_returned(error_message='Invalid types:')
    def validate_item_types(self, item_types=[]):
        return self._get_invalid_item_types(
            item_types or self.params_parser.param_values_to_list(
                params=self._get_item_types()
            )
        )

    def validate_paging_constraints(self):
        from_value_as_int = self._get_from_value_as_int()
        limit_value_as_int = self._get_limit_value_as_int()
        paging_depth = from_value_as_int + limit_value_as_int
        max_result_window = self._get_max_result_window()
        if self._limit_is_all() and from_value_as_int != 0:
            msg = f'Invalid to specify from={from_value_as_int} and limit=all'
            raise get_default_exception()(explanation=msg)
        if self._should_scan_over_results() and from_value_as_int != 0:
            msg = f'Invalid to paginate when requesting more than {max_result_window} results'
            raise get_default_exception()(explanation=msg)
        if paging_depth > max_result_window and from_value_as_int !=0:
            msg = f'Paging depth {paging_depth} exceeds max depth of {max_result_window}'
            raise get_default_exception()(explanation=msg)


    def add_simple_query_string_query(self):
        query = self._get_simple_query_string_query()
        if query:
            self.search = self._get_or_create_search().query(
                self._make_simple_query_string_query(
                    query=query,
                    fields=self._get_search_fields(),
                    default_operator=AND
                )
            )

    def add_query_string_query(self):
        query = self._get_query_string_query()
        if query:
            query = self._validated_query_string_query(
                self._escape_reserved_query_string_characters(query)
            )
            self.search = self._get_or_create_search().query(
                self._make_query_string_query(
                    query=query,
                    fields=self._get_search_fields(),
                    default_operator=AND
                )
            )

    def add_filters(self):
        '''
        These filters apply to the entire aggregation and result context.
        '''
        self.search = self._get_or_create_search().filter(
                self._make_bool_query(
                    must=self._make_default_filters()
                )
        )

    def add_aggregations_and_aggregation_filters(self):
        '''
        Each aggregation is computed in a filter context that filters
        everything but the params of the same type.
        '''
        params = self._get_post_filters()
        for facet_name, facet_options in self._get_facets():
            filtered_params = self.params_parser.get_not_keys_filters(
                not_keys=[facet_name],
                params=params
            )
            must, must_not, exists, not_exists, ranges, not_ranges = self._make_split_filter_queries(
                params=filtered_params
            )
            subaggregation = self._subaggregation_factory(
                facet_options.get(TYPE_KEY)
            )
            subaggregation = subaggregation(
                field=self._map_param_to_elasticsearch_field(facet_name),
                exclude=facet_options.get(EXCLUDE),
                # TODO: size should be defined in schema instead of long keyword.
                size=3000 if facet_options.get(LENGTH) == LONG else 200
            )
            agg = self._make_filter_and_subaggregation(
                title=facet_name.replace(PERIOD, DASH),
                filter_context=self._make_bool_query(
                    must=must + exists + ranges,
                    must_not=must_not + not_exists + not_ranges
                ),
                subaggregation=subaggregation
            )
            self._get_or_create_search().aggs.bucket(facet_options.get(TITLE), agg)

    def add_post_filters(self):
        '''
        These filters apply to the final results returned, after aggregation
        has been computed.
        '''
        must, must_not, exists, not_exists, ranges, not_ranges = self._make_split_filter_queries()
        self.search = self._get_or_create_search().post_filter(
            self._make_bool_query(
                must=must + exists + ranges,
                must_not=must_not + not_exists + not_ranges
            )
        )

    def add_source(self):
        self.search = self._get_or_create_search().extra(
            **{
                _SOURCE: sorted(self._get_return_fields())
            }
        )

    def add_slice(self):
        '''
        If limit=all or limit > max result window we return
        default slice for the aggregations/total and scan over results
        in response mixin to_graph method.
        '''
        end = self._get_bounded_limit_value_or_default()
        self.search = self._get_or_create_search()[:end]

    def add_sort(self):
        sort_by = self._get_sort() or self._get_default_sort()
        if sort_by:
            self.search = self._get_or_create_search().sort(
                *sort_by
            )

    def add_exact_counting(self):
        self.search = self._get_or_create_search().extra(
            track_total_hits=True
        )

    def build_query(self):
        '''
        Public method to be implemented by children.
        '''
        raise NotImplementedError


class BasicSearchQueryFactory(AbstractQueryFactory):

    def __init__(self, params_parser, *args, **kwargs):
        super().__init__(params_parser, *args, **kwargs)

    def add_slice(self):
        '''
        Frontend passes from and limit parameters to paginate.
        '''
        start = self._get_from_value_as_int()
        slice_size = self._get_bounded_limit_value_or_default()
        end = start + slice_size
        self.search = self._get_or_create_search()[start:end]

    def build_query(self):
        self.validate_item_types()
        self.validate_paging_constraints()
        self.add_simple_query_string_query()
        self.add_query_string_query()
        self.add_filters()
        self.add_post_filters()
        self.add_source()
        self.add_exact_counting()
        self.add_slice()
        return self.search


class BasicSearchQueryFactoryWithFacets(BasicSearchQueryFactory):

    def __init__(self, params_parser, *args, **kwargs):
        super().__init__(params_parser, *args, **kwargs)

    def build_query(self):
        super().build_query()
        self.add_aggregations_and_aggregation_filters()
        self.add_sort()
        return self.search


class BasicSearchQueryFactoryWithoutFacets(BasicSearchQueryFactory):
    '''
    Like BasicSearchQueryFactoryWithFacets but avoids adding aggregations
    for facets. Allows for caching facets in separate request.
    '''

    def __init__(self, params_parser, *args, **kwargs):
        super().__init__(params_parser, *args, **kwargs)

    def build_query(self):
        super().build_query()
        self.add_sort()
        return self.search


class CachedFacetsQueryFactory(BasicSearchQueryFactoryWithFacets):
    '''
    Like BasicSearchQueryFactoryWithFacets but avoids returning hits so that
    aggregations are cached by ES shard request_cache. Avoids adding source or sort
    to minimize cache misses.
    '''
    def __init__(self, params_parser, *args, **kwargs):
        super().__init__(params_parser, *args, **kwargs)

    def add_source(self):
        pass

    def add_slice(self):
        self.search = self._get_or_create_search()[0:0]

    def add_sort(self):
        pass


class CollectionSearchQueryFactoryWithFacets(BasicSearchQueryFactoryWithFacets):
    '''
    Like BasicSearchQueryFactoryWithFacets but only searches over context item type.
    Provides listing view for collections.
    '''

    def __init__(self, params_parser, *args, **kwargs):
        super().__init__(params_parser, *args, **kwargs)

    def _get_item_types(self):
        return [(TYPE_KEY, self.params_parser._request.context.type_info.name)]


class BasicReportQueryFactory(BasicSearchQueryFactory):
    '''
    Like BasicSearchQueryFactory but makes sure single item type
    without subtypes is specified.
    '''

    def __init__(self, params_parser, *args, **kwargs):
        super().__init__(params_parser, *args, **kwargs)

    @assert_one_returned(error_message='Report view requires specifying a single type:')
    def _get_item_types(self):
        return super()._get_item_types()

    @assert_one_or_none_returned(error_message='Report view requires a type with no child types:')
    def validate_item_type_subtypes(self):
        return self._get_subtypes_for_item_type(
            self.params_parser.get_one_value(
                params=self._get_item_types()
            )
        )

    def build_query(self):
        self.validate_item_types()
        self.validate_item_type_subtypes()
        return super().build_query()


class BasicReportQueryFactoryWithFacets(BasicReportQueryFactory, BasicSearchQueryFactoryWithFacets):
    '''
    Like BasicSearchQueryFactoryWithFacets but makes sure single item type
    without subtypes is specified.
    '''

    def __init__(self, params_parser, *args, **kwargs):
        super().__init__(params_parser, *args, **kwargs)


class BasicReportQueryFactoryWithoutFacets(BasicReportQueryFactory, BasicSearchQueryFactoryWithoutFacets):
    '''
    Like BasicSearchQueryFactoryWithoutFacets but makes sure single item type
    without subtypes is specified.
    '''

    def __init__(self, params_parser, *args, **kwargs):
        super().__init__(params_parser, *args, **kwargs)


class MultipleTypesReportQueryFactoryWithFacets(BasicSearchQueryFactoryWithFacets):
    '''
    it's just an alias over BasicSearchQueryFactoryWithFacets
    '''

    def __init__(self, params_parser, *args, **kwargs):
        super().__init__(params_parser, *args, **kwargs)


class BasicMatrixQueryFactoryWithFacets(BasicSearchQueryFactoryWithFacets):
    '''
    Like BasicSearchQueryFactoryWithFacets but sets size to zero and adds a
    filter aggregation with a nested subaggregation to calculate values in the matrix.
    '''

    def __init__(self, params_parser, *args, **kwargs):
        super().__init__(params_parser, *args, **kwargs)

    @assert_one_returned(error_message='Matrix view requires specifying a single type:')
    def _get_item_types(self):
        return super()._get_item_types()

    def _get_matrix_definition_name(self):
        '''
        Can add new groupby definitions to item type and pass name in here.
        '''
        return self.kwargs.get('matrix_definition_name') or MATRIX

    @assert_something_returned(error_message='Item type does not have requested view defined:')
    def _get_matrix_for_item_type(self, item_type):
        return (
            self._extract_matrix_from_configs(
                self._get_configs_from_config_param_values()
            )
            or self._extract_matrix_from_configs(
                self._get_configs_from_item_types_as_combined_key()
            )
            or getattr(
                self._get_factory_for_item_type(item_type),
                self._get_matrix_definition_name(),
                {}
            )
        )

    def _get_group_by_fields_by_item_type_and_value(self, item_type, value):
        group_by = self._get_matrix_for_item_type(item_type).get(value, {}).get(GROUP_BY, {})
        if not isinstance(group_by, list):
            return [group_by]
        return group_by

    def _get_x_group_by_fields(self):
        return self._get_group_by_fields_by_item_type_and_value(
            self.params_parser.get_one_value(
                self._get_item_types()
            ),
            X
        )

    def _get_y_group_by_fields(self):
        return self._get_group_by_fields_by_item_type_and_value(
            self.params_parser.get_one_value(
                self._get_item_types()
            ),
            Y
        )

    def _make_list_of_name_and_subagg_tuples(self, names, aggregation_type=TERMS):
        subaggregation = self._subaggregation_factory(aggregation_type)
        return [
            (
                name,
                subaggregation(
                    field=self._map_param_to_elasticsearch_field(name),
                    size=NO_LIMIT
                )
            )
            for name in names
        ]

    def _make_subaggregation_from_names(self, names):
        '''
        Returns (top-level name, nested terms aggregations) from list of field names.
        '''
        dummy_agg = None
        names_and_aggregations = self._make_list_of_name_and_subagg_tuples(names)
        for name, agg in names_and_aggregations:
            if dummy_agg is None:
                dummy_agg = agg
            else:
                dummy_agg = dummy_agg.bucket(name, agg)
        if names_and_aggregations:
            # The subaggregations have been accumulated on first agg in list.
            return names_and_aggregations[0][0], names_and_aggregations[0][1]
        return None, None

    def _get_group_by_names(self):
        x_group_by = self._get_x_group_by_fields()
        y_group_by = self._get_y_group_by_fields()
        return [
            (X, x_group_by),
            (Y, y_group_by + x_group_by)
        ]

    def add_matrix_aggregations(self):
        must, must_not, exists, not_exists, ranges, not_ranges = self._make_split_filter_queries(
            params=self._get_post_filters()
        )
        filter_context = self._make_bool_query(
            must=must + exists + ranges,
            must_not=must_not + not_exists + not_ranges
        )
        group_by_names = self._get_group_by_names()
        for axis, names in group_by_names:
            title, subaggregation = self._make_subaggregation_from_names(
                names
            )
            filter_agg = self._make_filter_and_subaggregation(
                title=title,
                filter_context=filter_context,
                subaggregation=subaggregation
            )
            self._get_or_create_search().aggs.bucket(axis, filter_agg)

    def add_slice(self):
        '''
        We just want aggregations not hits.
        '''
        self.search = self._get_or_create_search()[0:0]

    def build_query(self):
        self.validate_item_types()
        self.add_simple_query_string_query()
        self.add_query_string_query()
        self.add_filters()
        self.add_post_filters()
        self.add_exact_counting()
        self.add_slice()
        self.add_aggregations_and_aggregation_filters()
        self.add_matrix_aggregations()
        return self.search


class MissingMatrixQueryFactoryWithFacets(BasicMatrixQueryFactoryWithFacets):
    '''
    Like BasicMatrixQueryFactoryWithFacets but allows specification of default value
    for objects missing an aggregation field.
    '''

    def _parse_name_and_default_value_from_name(self, name, default_value=None):
        '''
        Specifying a tuple in the group_by definition indicates a default value
        should be filled in when the field is missing. Assumes tuple is
        (name, default_value). Default value only applies if it is not None.
        '''
        if isinstance(name, tuple):
            name, default_value = name
        return name, default_value

    def _make_subaggregation_with_possible_default_value_from_name(self, subaggregation, name):
        name, default_value = self._parse_name_and_default_value_from_name(name)
        return (
            name,
            subaggregation(
                field=self._map_param_to_elasticsearch_field(name),
                size=NO_LIMIT,
                missing=default_value
            )
        )

    def _make_list_of_name_and_subagg_tuples(self, names, aggregation_type=TERMS):
        subaggregation = self._subaggregation_factory(aggregation_type)
        return [
            self._make_subaggregation_with_possible_default_value_from_name(
                subaggregation,
                name
            )
            for name in names
        ]


class AuditMatrixQueryFactoryWithFacets(BasicMatrixQueryFactoryWithFacets):
    '''
    Like BasicMatrixQueryFactoryWithFacets but adds aggregation for all audit fields.
    '''

    def _get_matrix_definition_name(self):
        return self.kwargs.get('matrix_definition_name') or AUDIT

    def _get_group_by_names(self):
        x_group_by = self._get_x_group_by_fields()
        audit_group_by = [
            (field, [field] + x_group_by)
            for field in AUDIT_FIELDS
        ]
        return [(X, x_group_by)] + audit_group_by


class TopHitsQueryFactory(BasicSearchQueryFactory):
    '''
    Like BasicSearchQueryFactory but returns top hits by @type aggregation.
    '''

    def __init__(self, params_parser, *args, **kwargs):
        super().__init__(params_parser, *args, **kwargs)

    def _make_max_aggregation(self, **kwargs):
        return A(
            MAX,
            **kwargs
        )

    def _make_top_hits_aggregation(self, **kwargs):
        return A(
            TOP_HITS,
            **kwargs
        )

    def _make_top_hits_by_type_aggregation(self):
        return self._make_terms_aggregation(
            field=EMBEDDED_TYPE,
            include=self.params_parser.param_values_to_list(
                params=self._get_item_types() or self._get_default_item_types()
            ),
            size=10,
            aggs={
                TOP_HITS: self._make_top_hits_aggregation(
                    _source=self._get_return_fields()
                ),
                MAX_SCORE: self._make_max_aggregation(
                    script=_SCORE
                )
            }
        )

    def add_filtered_top_hits_aggregation(self):
        must, must_not, exists, not_exists, ranges, not_ranges = self._make_split_filter_queries(
            params=self._get_post_filters()
        )
        filter_context = self._make_bool_query(
            must=must + exists + ranges,
            must_not=must_not + not_exists + not_ranges
        )
        subaggregation = self._make_top_hits_by_type_aggregation()
        filter_agg = self._make_filter_and_subaggregation(
                title=TYPES,
                filter_context=filter_context,
                subaggregation=subaggregation
            )
        self._get_or_create_search().aggs.bucket(TYPES, filter_agg)

    def add_slice(self):
        self.search = self._get_or_create_search()[0:0]

    def build_query(self):
        super().build_query()
        self.add_filtered_top_hits_aggregation()
        return self.search
