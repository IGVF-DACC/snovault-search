import pytest


integrations = [
    'pyramid',
    'flask',
]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_init(dummy_request):
    from snosearch.parsers import ParamsParser
    p = ParamsParser(dummy_request)
    assert isinstance(p, ParamsParser)
    assert p._request is dummy_request


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_query_string(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = 'type=Experiment'
    p = ParamsParser(dummy_request)
    assert 'type' in p._request.params
    assert p._request.params.getall('type') == ['Experiment']


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_query_string_not(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = 'type!=Experiment'
    p = ParamsParser(dummy_request)
    assert 'type!' in p._request.params


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_filters_by_condition_none(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = 'type=Experiment&type=File&field=status'
    p = ParamsParser(dummy_request)
    assert p.get_filters_by_condition() == [
        ('type', 'Experiment'),
        ('type', 'File'),
        ('field', 'status')
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_filters_by_condition_key_field(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = 'type=Experiment&type=File&field=status'
    p = ParamsParser(dummy_request)
    assert p.get_filters_by_condition(
        key_and_value_condition=lambda k, _: k == 'field'
    ) == [
        ('field', 'status')
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_filters_by_condition_key_type(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = 'type=Experiment&type=File&field=status'
    p = ParamsParser(dummy_request)
    assert p.get_filters_by_condition(
        key_and_value_condition=lambda k, _: k == 'type'
    ) == [
        ('type', 'Experiment'),
        ('type', 'File')
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_filters_by_condition_value_status(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = 'type=Experiment&type=File&field=status'
    p = ParamsParser(dummy_request)
    assert p.get_filters_by_condition(
        key_and_value_condition=lambda _, v: v == 'status'
    ) == [
        ('field', 'status')
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_filters_by_condition_key_type_value_file(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = 'type=Experiment&type=File&field=status'
    p = ParamsParser(dummy_request)
    assert p.get_filters_by_condition(
        key_and_value_condition=lambda k, v: k == 'type' and v == 'File'
    ) == [
        ('type', 'File')
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_filters_by_condition_contains_letter(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = 'type=Experiment&type=File&field=status'
    p = ParamsParser(dummy_request)
    assert p.get_filters_by_condition(
        key_and_value_condition=lambda k, v: 't' in k and 'F' in v
    ) == [
        ('type', 'File')
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_key_filters(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'type=Experiment&type=File&status=archived&type!=Item&status!=released'
    )
    p = ParamsParser(dummy_request)
    assert p.get_key_filters(key='status') == [
        ('status', 'archived'),
        ('status!', 'released')
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_type_filters(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'type=Experiment&type=File&field=status&type!=Item'
    )
    p = ParamsParser(dummy_request)
    assert p.get_type_filters() == [
        ('type', 'Experiment'),
        ('type', 'File'),
        ('type!', 'Item')
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_search_term_filters_empty(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'type=Experiment&type=File&field=status&type!=Item'
    )
    p = ParamsParser(dummy_request)
    assert p.get_search_term_filters() == []


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_search_term_filters(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'type=Experiment&type=File&field=status&type!=Item'
        '&query=my+favorite+experiment&query=my+other+experiment'
        '&query!=whatever'
    )
    p = ParamsParser(dummy_request)
    assert p.get_search_term_filters() == [
        ('query', 'my favorite experiment'),
        ('query', 'my other experiment'),
        ('query!', 'whatever')
    ]
    dummy_request.environ['QUERY_STRING'] = (
        'type=Experiment&type=File&field=status&type!=Item'
        '&query=my+favorite+experiment&query=my+other+experiment'
        '&query!=whatever&query=newQuery'
    )
    p = ParamsParser(dummy_request)
    assert p.get_search_term_filters() == [
        ('query', 'my favorite experiment'),
        ('query', 'my other experiment'),
        ('query!', 'whatever'),
        ('query', 'newQuery'),
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_must_match_search_term_filters(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'type=Experiment&type=File&field=status&type!=Item'
        '&query=my+favorite+experiment&query=my+other+experiment'
        '&query!=whatever'
    )
    p = ParamsParser(dummy_request)
    assert p.get_must_match_search_term_filters() == [
        ('query', 'my favorite experiment'),
        ('query', 'my other experiment')
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_must_not_match_search_term_filters(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'type=Experiment&type=File&field=status&type!=Item'
        '&query=my+favorite+experiment&query=my+other+experiment'
        '&query!=whatever'
    )
    p = ParamsParser(dummy_request)
    assert p.get_must_not_match_search_term_filters() == [
        ('query!', 'whatever')
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_advanced_query_filters_empty(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'type=Experiment&type=File&field=status&type!=Item'
    )
    p = ParamsParser(dummy_request)
    assert p.get_advanced_query_filters() == []


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_advanced_query_filters(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'type=Experiment&type=File&field=status&type!=Item'
        '&advancedQuery=my+favorite+experiment&query=my+other+experiment'
        '&query!=whatever'
    )
    p = ParamsParser(dummy_request)
    assert p.get_advanced_query_filters() == [
        ('advancedQuery', 'my favorite experiment')
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_must_match_advanced_query_filters(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'type=Experiment&type=File&field=status&type!=Item'
        '&advancedQuery=date_created:[01/01/2018 TO 01/02/2019]'
        '&advancedQuery=@type:Experiment date_released:[2009-01-01 TO 2019-12-31]'
        '&query=whatever'
    )
    p = ParamsParser(dummy_request)
    assert p.get_must_match_advanced_query_filters() == [
        ('advancedQuery', 'date_created:[01/01/2018 TO 01/02/2019]'),
        ('advancedQuery', '@type:Experiment date_released:[2009-01-01 TO 2019-12-31]')
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_must_not_match_advanced_query_filters(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'type=Experiment&type=File&field=status&type!=Item'
        '&advancedQuery!=whatever'
    )
    p = ParamsParser(dummy_request)
    assert p.get_must_not_match_advanced_query_filters() == [
        ('advancedQuery!', 'whatever')
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_field_filters(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'type=Experiment&type=File&field=status&type!=Item'
        '&query=my+favorite+experiment&query=my+other+experiment'
    )
    p = ParamsParser(dummy_request)
    assert p.get_field_filters() == [
        ('field', 'status')
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_is_param(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'type=Experiment&type=File&files.file_type=fastq&field=status'
    )
    p = ParamsParser(dummy_request)
    assert p.is_param(key='type', value='File')
    assert p.is_param(key='files.file_type', value='fastq')
    assert not p.is_param(key='files.file_type', value='bam')


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_must_match_filter(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'type=Experiment&type=File&files.file_type!=fastq&field=status'
    )
    p = ParamsParser(dummy_request)
    assert p.get_must_match_filters() == [
        ('type', 'Experiment'),
        ('type', 'File'),
        ('field', 'status')
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_must_not_match_filters(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'type!=Experiment&type=File&files.file_type=fastq&field=status'
    )
    p = ParamsParser(dummy_request)
    assert p.get_must_not_match_filters() == [
        ('type!', 'Experiment')
    ]

@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_inequality_filters(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'type=Experiment&type=File&files.file_type!=fastq&field=status'
        '&file_size=gte:30000&file_size=lt:2560000&replicates.read_count=lte:99999999'
        '&biosample.replicate.size=gt:2&quality_metric.RSC1!=lt:30&file_size=*'
    )
    p = ParamsParser(dummy_request)
    assert p.get_inequality_filters() == [
        ('file_size', 'gte:30000'),
        ('file_size', 'lt:2560000'),
        ('replicates.read_count', 'lte:99999999'),
        ('biosample.replicate.size', 'gt:2'),
        ('quality_metric.RSC1!', 'lt:30'),
    ]

@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_non_inequality_filters(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'type=Experiment&type=File&files.file_type!=fastq&field=status'
        '&file_size=gte:30000&file_size=lt:2560000&replicates.read_count=lte:99999999'
        '&biosample.replicate.size=gt:2&quality_metric.RSC1!=lt:30&file_size=*'
    )
    p = ParamsParser(dummy_request)
    assert p.get_non_inequality_filters() == [
        ('type', 'Experiment'),
        ('type', 'File'),
        ('files.file_type!', 'fastq'),
        ('field', 'status'),
        ('file_size', '*'),
    ]

@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_must_filters(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'type=Experiment&type=File&files.file_type!=fastq&field=status&type=*'
        '&file_size=gte:30000&file_size=lt:2560000&replicates.read_count=lte:99999999'
        '&biosample.replicate.size=gt:2&quality_metric.RSC1!=lt:30&file_size=*'
    )
    p = ParamsParser(dummy_request)
    assert p.get_must_filters() == [
        ('type', 'Experiment'),
        ('type', 'File'),
        ('field', 'status')
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_must_not_filters(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'type=Experiment&type=File&files.file_type!=fastq'
        '&field=status&type=*&file_size!=*'
        '&file_size=gte:30000&file_size=lt:2560000&replicates.read_count=lte:99999999'
        '&biosample.replicate.size=gt:2&quality_metric.RSC1!=lt:30&file_size=*'
    )
    p = ParamsParser(dummy_request)
    assert p.get_must_not_filters() == [
        ('files.file_type!', 'fastq')
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_exists_filters(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'type=Experiment&type=File&files.file_type!=fastq'
        '&field=status&type=*&file_size!=*'
        '&file_size=gte:30000&file_size=lt:2560000&replicates.read_count=lte:99999999'
        '&biosample.replicate.size=gt:2&quality_metric.RSC1!=lt:30&file_size=*'
    )
    p = ParamsParser(dummy_request)
    assert p.get_exists_filters() == [
        ('type', '*'),
        ('file_size', '*'),
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_not_exists_filters(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'type=Experiment&type=File&files.file_type!=fastq'
        '&field=status&type=*&file_size!=*'
        '&file_size=gte:30000&file_size=lt:2560000&replicates.read_count=lte:99999999'
        '&biosample.replicate.size=gt:2&quality_metric.RSC1!=lt:30&file_size=*'
    )
    p = ParamsParser(dummy_request)
    assert p.get_not_exists_filters() == [
        ('file_size!', '*')
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_range_filters(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'type=Experiment&type=File&files.file_type!=fastq'
        '&field=status&type=*&file_size!=*'
        '&file_size=gte:30000&file_size=lt:2560000&replicates.read_count=lte:99999999'
        '&biosample.replicate.size=gt:2&quality_metric.RSC1!=lt:30&file_size=*'
    )
    p = ParamsParser(dummy_request)
    assert p.get_range_filters() == [
        ('file_size', 'gte:30000'),
        ('file_size', 'lt:2560000'),
        ('replicates.read_count', 'lte:99999999'),
        ('biosample.replicate.size', 'gt:2')
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_not_range_filters(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'type=Experiment&type=File&files.file_type!=fastq'
        '&field=status&type=*&file_size!=*'
        '&file_size=gte:30000&file_size=lt:2560000&replicates.read_count=lte:99999999'
        '&biosample.replicate.size=gt:2&quality_metric.RSC1!=lt:30&file_size=*'
    )
    p = ParamsParser(dummy_request)
    assert p.get_not_range_filters() == [
        ('quality_metric.RSC1!', 'lt:30')
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_chain_filters(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'type!=Experiment&type=File&files.file_type=fastq&field!=status'
    )
    p = ParamsParser(dummy_request)
    assert p.get_type_filters(params=p.get_must_not_match_filters()) == [
        ('type!', 'Experiment')
    ]
    assert p.get_must_not_match_filters(params=p.get_type_filters()) == [
        ('type!', 'Experiment')
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_query_string(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'type=File&file_format%21=bigWig&file_type%21=bigBed+tss_peak'
        '&file_format_type=bed3%2B'
    )
    p = ParamsParser(dummy_request)
    assert dummy_request.environ['QUERY_STRING'] == p.get_query_string()


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_filter_and_query_string(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'type=File&file_format%21=bigWig&file_type%21=bigBed+tss_peak'
        '&file_format_type=bed3%2B'
    )
    p = ParamsParser(dummy_request)
    assert p.get_type_filters() == [
        ('type', 'File')
    ]
    assert p.get_query_string(
        params=p.get_type_filters()
    ) == 'type=File'
    assert p.get_must_not_match_filters() == [
        ('file_format!', 'bigWig'),
        ('file_type!', 'bigBed tss_peak')
    ]
    assert p.get_query_string(
        params=p.get_must_not_match_filters()
    ) == 'file_format%21=bigWig&file_type%21=bigBed+tss_peak'
    assert p.get_must_match_filters() == [
        ('type', 'File'),
        ('file_format_type', 'bed3+')
    ]
    assert p.get_query_string(
        params=p.get_must_match_filters()
    ) == 'type=File&file_format_type=bed3%2B'
    assert dummy_request.environ['QUERY_STRING'] == p.get_query_string()


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_filter_and_query_string_space(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'type=File&status=released&file_type=bed+bed3%2B'
    )
    p = ParamsParser(dummy_request)
    assert p.get_key_filters(
        key='file_type',
        params=p.get_must_match_filters()
    ) == [
        ('file_type', 'bed bed3+')
    ]
    assert p.get_search_term_filters() == []
    assert p.get_query_string(
        params=p.get_search_term_filters()
    ) == ''
    assert p.get_query_string(
        params=p.get_key_filters(key='file_type')
    ) == 'file_type=bed+bed3%2B'


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_filtered_is_param(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'type=File&status=released&file_type=bed+bed3%2B'
    )
    p = ParamsParser(dummy_request)
    assert p.is_param('status', 'released')
    assert not p.is_param(
        'status',
        'released',
        params=p.get_type_filters()
    )
    assert p.is_param(
        'file_type',
        'bed bed3+',
        params=p.get_key_filters(
            key='file_type',
            params=p.get_must_match_filters()
        )
    )


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_keys_filters(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'type=File&file_format%21=bigWig&file_type%21=bigBed+tss_peak'
        '&file_format_type=bed3%2B'
    )
    p = ParamsParser(dummy_request)
    assert p.get_keys_filters(['type', 'file_format_type']) == [
        ('type', 'File'),
        ('file_format_type', 'bed3+')
    ]
    assert p.get_keys_filters() == []


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_not_keys_filters(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'status=released&type=File&file_format%21=bigWig'
        '&file_type%21=bigBed+tss_peak&file_format_type=bed3%2B'
    )
    p = ParamsParser(dummy_request)
    assert p.get_not_keys_filters(['type', 'file_format_type']) == [
        ('status', 'released'),
        ('file_format!', 'bigWig'),
        ('file_type!', 'bigBed tss_peak')
    ]
    assert p.get_not_keys_filters() == [
        ('status', 'released'),
        ('type', 'File'),
        ('file_format!', 'bigWig'),
        ('file_type!', 'bigBed tss_peak'),
        ('file_format_type', 'bed3+')
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_wildcard_filters(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'status=released&type=*&file_format%21=*'
        '&file_type%21=bigBed+tss_peak&file_format_type=bed3%2B'
    )
    p = ParamsParser(dummy_request)
    assert p.get_wildcard_filters() == [
        ('type', '*'),
        ('file_format!', '*')
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_non_wildcard_filters(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'status=released&type=*&file_format%21=*'
        '&file_type%21=bigBed+tss_peak&file_format_type=bed3%2B'
    )
    p = ParamsParser(dummy_request)
    assert p.get_non_wildcard_filters() == [
        ('status', 'released'),
        ('file_type!', 'bigBed tss_peak'),
        ('file_format_type', 'bed3+')
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_remove_key_and_value_pair_from_filters(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'status=released&type=Biosample&type!=Experiment&type=*'
        '&file_format%21=*&file_type%21=bigBed+tss_peak'
        '&file_format_type=bed3%2B'
    )
    p = ParamsParser(dummy_request)
    assert p.remove_key_and_value_pair_from_filters(
        key='file_format!',
        value='*'
    ) == [
        ('status', 'released'),
        ('type', 'Biosample'),
        ('type!', 'Experiment'),
        ('type', '*'),
        ('file_type!', 'bigBed tss_peak'),
        ('file_format_type', 'bed3+')
    ]
    assert p.remove_key_and_value_pair_from_filters(
        key='status',
        value='released'
    ) == [
        ('type', 'Biosample'),
        ('type!', 'Experiment'),
        ('type', '*'),
        ('file_format!', '*'),
        ('file_type!', 'bigBed tss_peak'),
        ('file_format_type', 'bed3+')
    ]
    assert p.remove_key_and_value_pair_from_filters(
        key='type',
        value='Experiment'
    )== [
        ('status', 'released'),
        ('type', 'Biosample'),
        ('type!', 'Experiment'),
        ('type', '*'),
        ('file_format!', '*'),
        ('file_type!', 'bigBed tss_peak'),
        ('file_format_type', 'bed3+')
    ]
    assert p.remove_key_and_value_pair_from_filters(
        key='status',
        value='released'
    ) == [
        ('type', 'Biosample'),
        ('type!', 'Experiment'),
        ('type', '*'),
        ('file_format!', '*'),
        ('file_type!', 'bigBed tss_peak'),
        ('file_format_type', 'bed3+')
    ]
    assert p.remove_key_and_value_pair_from_filters(
        key='status!',
        value='released'
    ) == [
        ('status', 'released'),
        ('type', 'Biosample'),
        ('type!', 'Experiment'),
        ('type', '*'),
        ('file_format!', '*'),
        ('file_type!', 'bigBed tss_peak'),
        ('file_format_type', 'bed3+')
    ]
    with pytest.raises(ValueError):
        p.remove_key_and_value_pair_from_filters(key='type')
    with pytest.raises(ValueError):
        p.remove_key_and_value_pair_from_filters(value='*')


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_keys_filters_not_flag(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'status=released&status!=submitted&type=File&file_format%21=bigWig'
    )
    p = ParamsParser(dummy_request)
    assert p.get_not_keys_filters() == [
        ('status', 'released'),
        ('status!', 'submitted'),
        ('type', 'File'),
        ('file_format!', 'bigWig')
    ]
    assert p.get_not_keys_filters(
        not_keys=['status']
    ) == [
        ('type', 'File'),
        ('file_format!', 'bigWig')
    ]
    assert p.get_not_keys_filters(
        not_keys=['status', 'file_format']
    ) == [
        ('type', 'File')
    ]
    assert p.get_not_keys_filters(
        not_keys=['status', 'file_format', 'type']
    ) == []
    assert p.get_keys_filters(
        keys=['status']
    ) == [
        ('status', 'released'),
        ('status!', 'submitted')
    ]
    assert p.get_keys_filters(
        keys=['status', 'file_format']
    ) == [
        ('status', 'released'),
        ('status!', 'submitted'),
        ('file_format!', 'bigWig')
    ]
    assert p.get_must_not_match_filters(
        params=p.get_keys_filters(
            keys=['status', 'file_format'])
    ) == [
        ('status!', 'submitted'),
        ('file_format!', 'bigWig')
    ]
    assert p.get_must_match_filters(
        params=p.get_keys_filters(
            keys=['status', 'file_format'])
    ) == [
        ('status', 'released')
    ]
    assert p.get_query_string(
        params=p.get_must_match_filters(
            params=p.get_keys_filters(
                keys=['status', 'file_format']
            )
        )
    ) == 'status=released'


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_from(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'status=released&status!=submitted&type=File&file_format%21=bigWig'
    )
    p = ParamsParser(dummy_request)
    assert p.get_from() == []
    dummy_request.environ['QUERY_STRING'] = (
        'status=released&status!=submitted&type=File'
        '&file_format%21=bigWig&from=100'
    )
    p = ParamsParser(dummy_request)
    assert p.get_from() == [
        ('from', '100')
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_limit(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'status=released&status!=submitted&type=File&file_format%21=bigWig'
    )
    p = ParamsParser(dummy_request)
    assert p.get_limit() == []
    dummy_request.environ['QUERY_STRING'] = (
        'status=released&status!=submitted&type=File'
        '&file_format%21=bigWig&limit=all'
    )
    p = ParamsParser(dummy_request)
    assert p.get_limit() == [
        ('limit', 'all')
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_sort(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'status=released&status!=submitted&type=File&sort=date_created'
    )
    p = ParamsParser(dummy_request)
    assert p.get_sort() == [
        ('sort', 'date_created')
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_frame(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'frame=embedded&status!=submitted&type=File&sort=date_created'
    )
    p = ParamsParser(dummy_request)
    assert p.get_frame() == [
        ('frame', 'embedded')
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_mode(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'frame=embedded&status!=submitted&mode=picker&type=File&sort=date_created'
    )
    p = ParamsParser(dummy_request)
    assert p.get_mode() == [
        ('mode', 'picker')
    ]
    assert p.param_values_to_list(
        params=p.get_mode()
    )[0] == 'picker'


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_debug(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'frame=embedded&status!=submitted&type=File&sort=date_created&debug=true'
    )
    p = ParamsParser(dummy_request)
    assert p.get_debug() == [
        ('debug', 'true')
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_cart(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'frame=embedded&status!=submitted&type=File&sort=date_created&debug=true&cart=abc123&cart=def456'
    )
    p = ParamsParser(dummy_request)
    assert p.get_cart() == [
        ('cart', 'abc123'),
        ('cart', 'def456')
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_get_config(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'frame=embedded&status!=submitted&type=File&sort=date_created'
        '&debug=true&cart=abc123&cart=def456'
        '&config=Experiment&config=custom'
    )
    p = ParamsParser(dummy_request)
    assert p.get_config() == [
        ('config', 'Experiment'),
        ('config', 'custom')
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_param_keys_to_list(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'frame=embedded&status!=submitted&type=File&sort=date_created'
    )
    p = ParamsParser(dummy_request)
    assert p.param_keys_to_list() == [
        'frame',
        'status!',
        'type',
        'sort',
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_param_values_to_list(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'frame=embedded&status!=submitted&type=File&sort=date_created'
    )
    p = ParamsParser(dummy_request)
    assert p.param_values_to_list() == [
        'embedded',
        'submitted',
        'File',
        'date_created',
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_param_remove_not_flag(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'frame=embedded&status!=submitted&type=File&sort=date_created'
    )
    p = ParamsParser(dummy_request)
    assert p.remove_not_flag() == [
        ('frame', 'embedded'),
        ('status', 'submitted'),
        ('type', 'File'),
        ('sort', 'date_created')
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_params_to_list(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'frame=embedded&status!=submitted&type=File&sort=date_created'
    )
    p = ParamsParser(dummy_request)
    assert p.params_to_list(key=False) == [
        'embedded',
        'submitted',
        'File',
        'date_created',
    ]
    assert p.params_to_list(key=True) == [
        'frame',
        'status!',
        'type',
        'sort',
    ]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_params_get_one_value(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'frame=embedded&status!=submitted&type=File&sort=date_created'
    )
    p = ParamsParser(dummy_request)
    assert p.get_one_value() == 'embedded'


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_params_coerce_value_to_int_or_return_none(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'frame=embedded&status!=submitted&type=File&sort=date_created'
    )
    p = ParamsParser(dummy_request)
    assert p.coerce_value_to_int_or_return_none('12') == 12
    assert p.coerce_value_to_int_or_return_none(12) == 12
    assert p.coerce_value_to_int_or_return_none('all') is None


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_params_parser_group_values_by_key(dummy_request):
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'type=*&status=released&status!=submitted&type=File&file_size=*'
        '&file_format%21=bigWig&restricted!=*&no_file_available!=*&limit=all'
        '&status=archived&status=revoked&file_format!=fastq'
    )
    p = ParamsParser(dummy_request)
    values_by_key = p.group_values_by_key()
    assert values_by_key == {
        'file_format!': ['bigWig', 'fastq'],
        'file_size': ['*'],
        'limit': ['all'],
        'no_file_available!': ['*'],
        'restricted!': ['*'],
        'status': ['released', 'archived', 'revoked'],
        'status!': ['submitted'],
        'type': ['*', 'File']
    }


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searchers_parsers_params_parser_split_filters(dummy_request):
    from snosearch.defaults import NOT_FILTERS
    from snosearch.parsers import ParamsParser
    dummy_request.environ['QUERY_STRING'] = (
        'type=*&status=released&status!=submitted&type=File&file_size=*'
        '&file_format%21=bigWig&restricted!=*&no_file_available!=*&limit=all'
        '&file_size=gte:30000&file_size=lt:2560000&replicates.read_count=lte:99999999'
        '&biosample.replicate.size=gt:2&quality_metric.RSC1!=lt:30'
    )
    p = ParamsParser(dummy_request)
    params = p.split_filters(
        params=p.get_not_keys_filters(not_keys=NOT_FILTERS) + p.get_type_filters()
    )
    assert params['must'] == [
        ('status', 'released'),
        ('type', 'File')
    ]
    assert params['must_not'] == [
        ('status!', 'submitted'),
        ('file_format!', 'bigWig')
    ]
    assert params['exists'] == [
        ('file_size', '*'),
        ('type', '*')
    ]
    assert params['not_exists'] == [
        ('restricted!', '*'),
        ('no_file_available!', '*')
    ]
    assert params['ranges'] == [
        ('file_size', 'gte:30000'),
        ('file_size', 'lt:2560000'),
        ('replicates.read_count', 'lte:99999999'),
        ('biosample.replicate.size', 'gt:2'),
    ]
    assert params['not_ranges'] == [
        ('quality_metric.RSC1!', 'lt:30'),
    ]
    dummy_request.environ['QUERY_STRING'] = (
        'type=File&status=released'
    )
    p = ParamsParser(dummy_request)
    params = p.split_filters(
        params=p.get_not_keys_filters(not_keys=NOT_FILTERS) + p.get_type_filters()
    )
    for k, v in params.items():
        if k == 'must':
            assert v == [
                ('status', 'released'),
                ('type', 'File'),
            ]
        else:
            assert v == []


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_mutable_params_parser_init(dummy_request):
    from snosearch.parsers import MutableParamsParser
    mpp = MutableParamsParser(dummy_request)
    assert isinstance(mpp, MutableParamsParser)
    assert mpp.params == []
    dummy_request.query_string = 'type=Snowflake'
    mpp = MutableParamsParser(dummy_request)
    assert mpp.params == [
        ('type', 'Snowflake')
]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_mutable_params_parser_get_original_params(dummy_request):
    from snosearch.parsers import MutableParamsParser
    mpp = MutableParamsParser(dummy_request)
    assert mpp._get_original_params() == []
    dummy_request.query_string = 'type=Snowflake'
    mpp = MutableParamsParser(dummy_request)
    assert mpp._get_original_params() == [('type', 'Snowflake')]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_mutable_params_parser_get_original_query_string(dummy_request):
    from snosearch.parsers import MutableParamsParser
    mpp = MutableParamsParser(dummy_request)
    assert mpp._get_original_query_string() == ''
    dummy_request.query_string = 'type=Snowflake&status!=deleted'
    mpp = MutableParamsParser(dummy_request)
    assert mpp._get_original_query_string() == 'type=Snowflake&status%21=deleted'


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_mutable_params_parser_validate_param(dummy_request):
    from snosearch.parsers import MutableParamsParser
    mpp = MutableParamsParser(dummy_request)
    mpp._validate_param(('type', 'Snowflake'))
    mpp._validate_param(('status!', 'deleted'))
    with pytest.raises(ValueError):
        mpp._validate_param('abc')
        mpp._validate_param(['abc'])
        mpp._validate_param([('abc', 123), ('abc', 123)])
        mpp._validate_param(('abc', 123, 'cdf'))


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_mutable_params_parser_validate_params(dummy_request):
    from snosearch.parsers import MutableParamsParser
    mpp = MutableParamsParser(dummy_request)
    mpp._validate_params([('type', 'Snowflake')])
    mpp._validate_params([('type', 'Snowflake'), ('type!', 'Item')])
    with pytest.raises(ValueError):
        mpp._validate_params([('type', 'Snowflake'), ('type!', 'Item', 123)])
        mpp._validate_params(('type', 'Snowflake'))


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_mutable_params_parser_append(dummy_request):
    from snosearch.parsers import MutableParamsParser
    mpp = MutableParamsParser(dummy_request)
    mpp.append(('type', 'Snowflake'))
    assert mpp.params == [('type', 'Snowflake')]
    with pytest.raises(ValueError):
        mpp.append('asdf')
        assert mpp.params == [('type', 'Snowflake')]
    mpp.append(('type', 'Snowball'))
    assert mpp.params == [
        ('type', 'Snowflake'),
        ('type', 'Snowball')
    ]
    mpp.append(('type', 'Snowball'))
    assert mpp.params == [
        ('type', 'Snowflake'),
        ('type', 'Snowball'),
        ('type', 'Snowball')
    ]
    mpp.append(('type!', 'Snowball'))
    assert mpp.params == [
        ('type', 'Snowflake'),
        ('type', 'Snowball'),
        ('type', 'Snowball'),
        ('type!', 'Snowball')
    ]
    mpp.params = [('status', 'released')]
    mpp.append(('thing', 'other_thing'))
    assert mpp.params == [('status', 'released'), ('thing', 'other_thing')]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_mutable_params_parser_extend(dummy_request):
    from snosearch.parsers import MutableParamsParser
    mpp = MutableParamsParser(dummy_request)
    mpp.params = [('status', 'released')]
    mpp.extend(
        [
            ('type', 'Snowflake'),
            ('type', 'Snowball')
        ]
    )
    assert mpp.params == [
        ('status', 'released'),
        ('type', 'Snowflake'),
        ('type', 'Snowball')
    ]
    with pytest.raises(ValueError):
        mpp.extend([('x', 'y', 'z')])
        mpp.extend(('x', 'y'))


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_mutable_params_parser_drop_key(dummy_request):
    from snosearch.parsers import MutableParamsParser
    mpp = MutableParamsParser(dummy_request)
    mpp.params = [('status', 'released')]
    mpp._drop_key('status')
    assert mpp.params == []
    mpp.params = [('status', 'released'), ('status', 'deleted')]
    mpp._drop_key('status')
    assert mpp.params == []
    mpp.params = [('status', 'released'), ('status!', 'deleted'), ('type', 'Snowflake')]
    mpp._drop_key('status')
    assert mpp.params == [('type', 'Snowflake')]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_mutable_params_parser_drop_key_and_value(dummy_request):
    from snosearch.parsers import MutableParamsParser
    mpp = MutableParamsParser(dummy_request)
    mpp.params = [('status', 'released')]
    mpp._drop_key_and_value(key='status', value='deleted')
    assert mpp.params == [('status', 'released')]
    mpp._drop_key_and_value(key='status!', value='released')
    assert mpp.params == [('status', 'released')]
    mpp._drop_key_and_value(key='status', value='released')
    assert mpp.params == []


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_mutable_params_parser_drop(dummy_request):
    from snosearch.parsers import MutableParamsParser
    mpp = MutableParamsParser(dummy_request)
    mpp.params = [('status', 'released')]
    mpp.drop('status')
    assert mpp.params == []
    mpp.params = [('status', 'released')]
    mpp.drop(('status', 'released'))
    assert mpp.params == []
    mpp.params = [('status', 'deleted')]
    mpp.drop(('status', 'released'))
    assert mpp.params == [('status', 'deleted')]


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_mutable_params_parser_deduplicate(dummy_request):
    from snosearch.parsers import MutableParamsParser
    mpp = MutableParamsParser(dummy_request)
    mpp.params = [('status', 'released')]
    mpp.deduplicate()
    assert mpp.params == [('status', 'released')]
    mpp.params = [('status', 'released'), ('status', 'released'), ('limit', 'all')]
    mpp.deduplicate()
    assert mpp.params == [('status', 'released'), ('limit', 'all')]
    mpp.params = [
        ('status', 'released'),
        ('abc', 123),
        ('status', 'released'),
        ('limit', 'all'),
        ('type', 'Snowball'),
        ('type!', 'Snowball'),
        ('type', 'Snowflake'),
        ('limit', 'all')
    ]
    mpp.deduplicate()
    assert mpp.params == [
        ('status', 'released'),
        ('abc', 123),
        ('limit', 'all'),
        ('type', 'Snowball'),
        ('type!', 'Snowball'),
        ('type', 'Snowflake')
    ]

    
@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_mutable_params_parser_get_request_with_new_query_string(dummy_request):
    from snosearch.parsers import MutableParamsParser
    dummy_request.query_string = 'type=Snowflake&status=released&format=json'
    mpp = MutableParamsParser(dummy_request)
    assert mpp.get_request_with_new_query_string().query_string == 'type=Snowflake&status=released&format=json'
    mpp.append(('limit', 'all'))
    assert mpp.get_request_with_new_query_string().query_string == 'type=Snowflake&status=released&format=json&limit=all'
    mpp.append(('limit', 'all'))
    assert mpp.params == [
        ('type', 'Snowflake'),
        ('status', 'released'),
        ('format', 'json'),
        ('limit', 'all'),
        ('limit', 'all')
    ]
    assert mpp.get_request_with_new_query_string(
        deduplicate=False
    ).query_string == 'type=Snowflake&status=released&format=json&limit=all&limit=all'
    assert mpp.get_request_with_new_query_string().query_string == 'type=Snowflake&status=released&format=json&limit=all'


def test_searches_parsers_mutable_params_parser_get_request_with_new_query_string_sets_registry_if_exists(dummy_request):
    from pyramid.registry import Registry
    from snosearch.parsers import MutableParamsParser
    dummy_request.query_string = 'type=Snowflake&status=released&format=json'
    mpp = MutableParamsParser(dummy_request)
    request = mpp.get_request_with_new_query_string()
    assert request.query_string == 'type=Snowflake&status=released&format=json'
    assert isinstance(request.registry, Registry)
    delattr(dummy_request, 'registry')
    assert not hasattr(dummy_request, 'registry')
    mpp = MutableParamsParser(dummy_request)
    request =  mpp.get_request_with_new_query_string()
    assert not hasattr(request, 'registry')
    assert request.query_string == 'type=Snowflake&status=released&format=json'
    

@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_mutable_params_parser_get_request_with_new_query_string_special_values(dummy_request):
    from snosearch.parsers import MutableParamsParser
    dummy_request.query_string = 'type=Snowflake&subtype=abc123+abc3%2B'
    mpp = MutableParamsParser(dummy_request)
    assert mpp.get_request_with_new_query_string().query_string == 'type=Snowflake&subtype=abc123+abc3%2B'
    dummy_request.query_string = 'type=Snowflake'
    mpp = MutableParamsParser(dummy_request)
    assert mpp.get_request_with_new_query_string().query_string == 'type=Snowflake'
    mpp.append(('subtype', 'abc123 abc3+'))
    assert mpp.get_request_with_new_query_string().query_string == 'type=Snowflake&subtype=abc123+abc3%2B'
    mpp.drop(('subtype', 'abc123 abc3+'))
    assert mpp.get_request_with_new_query_string().query_string == 'type=Snowflake'


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_query_string_init(dummy_request):
    from snosearch.parsers import QueryString
    qs = QueryString(dummy_request)
    assert isinstance(qs, QueryString)


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_query_string__repr__(dummy_request):
    from snosearch.parsers import QueryString
    dummy_request.query_string = 'type=Snowflake&type!=Snowball'
    qs = QueryString(dummy_request)
    assert str(qs) == 'type=Snowflake&type%21=Snowball'
    dummy_request.query_string = 'type=Snowball&status!=revoked&files.file_type=bed+bed6%2B'
    qs = QueryString(dummy_request)
    assert str(qs) == 'type=Snowball&status%21=revoked&files.file_type=bed+bed6%2B'
    dummy_request.query_string = 'type=Snowball&status%21=revoked&files.file_type=bed+bed6%2B'
    qs = QueryString(dummy_request)
    assert str(qs) == 'type=Snowball&status%21=revoked&files.file_type=bed+bed6%2B'


@pytest.mark.parametrize(
    'dummy_request',
    integrations,
    indirect=True
)
def test_searches_parsers_mutable_params_parser_clear(dummy_request):
    from snosearch.parsers import MutableParamsParser
    dummy_request.query_string = 'type=Snowflake&status=released&format=json'
    mpp = MutableParamsParser(dummy_request)
    assert mpp.get_query_string() == 'type=Snowflake&status=released&format=json'
    assert mpp.get_request_with_new_query_string().query_string == 'type=Snowflake&status=released&format=json'
    assert mpp.params == [
        ('type', 'Snowflake'),
        ('status', 'released'),
        ('format', 'json')
    ]
    mpp.clear()
    assert mpp.get_query_string() == ''
    assert mpp.get_request_with_new_query_string().query_string == ''
    assert mpp.params == []
