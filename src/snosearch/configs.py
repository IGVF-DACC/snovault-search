from collections.abc import Mapping
from dataclasses import dataclass
from .defaults import DEFAULT_TERMS_AGGREGATION_KWARGS
from .defaults import DEFAULT_EXISTS_AGGREGATION_KWARGS
from .defaults import DEFAULT_DATE_HISTOGRAM_AGGREGATION_KWARGS
from .defaults import DEFAULT_RANGE_AGGREGATION_KWARGS
from .interfaces import SEARCH_CONFIG

from typing import List
from typing import Union


class Config(Mapping):
    '''
    Used for filtering out inappropriate and None **kwargs before passing along to Elasticsearch.
    Implements Mapping type so ** syntax can be used.
    '''

    def __init__(self, allowed_kwargs=[], **kwargs):
        self._allowed_kwargs = allowed_kwargs
        self._kwargs = kwargs

    def _filtered_kwargs(self):
        return {
            k: v
            for k, v in self._kwargs.items()
            if v and k in self._allowed_kwargs
        }

    def __iter__(self):
        return iter(self._filtered_kwargs())

    def __len__(self):
        return len(self._filtered_kwargs())

    def __getitem__(self, key):
        return self._filtered_kwargs()[key]


class TermsAggregationConfig(Config):

    def __init__(self, allowed_kwargs=[], **kwargs):
        super().__init__(
            allowed_kwargs=allowed_kwargs or DEFAULT_TERMS_AGGREGATION_KWARGS,
            **kwargs
        )


class ExistsAggregationConfig(Config):

    def __init__(self, allowed_kwargs=[], **kwargs):
        super().__init__(
            allowed_kwargs=allowed_kwargs or DEFAULT_EXISTS_AGGREGATION_KWARGS,
            **kwargs
        )


class DateHistogramAggregationConfig(Config):

    def __init__(self, allowed_kwargs=[], **kwargs):
        super().__init__(
            allowed_kwargs=allowed_kwargs or DEFAULT_DATE_HISTOGRAM_AGGREGATION_KWARGS,
            **kwargs
        )


class RangeAggregationConfig(Config):

    def __init__(self, allowed_kwargs=[], **kwargs):
        super().__init__(
            allowed_kwargs=allowed_kwargs or DEFAULT_RANGE_AGGREGATION_KWARGS,
            **kwargs
        )


class SortedTupleMap:

    def __init__(self):
        self._map = {}

    @staticmethod
    def _convert_key_to_sorted_tuple(key):
        if isinstance(key, str):
            key = [key]
        return tuple(sorted(key))

    def __setitem__(self, key, value):
        key = self._convert_key_to_sorted_tuple(key)
        self._map[key] = value

    def __getitem__(self, key):
        key = self._convert_key_to_sorted_tuple(key)
        return self._map[key]

    def __contains__(self, key):
        key = self._convert_key_to_sorted_tuple(key)
        return key in self._map

    def get(self, key, default=None):
        return self._map.get(
            self._convert_key_to_sorted_tuple(key),
            default
        )

    def drop(self, key):
        key = self._convert_key_to_sorted_tuple(key)
        if key in self._map:
            del self._map[key]

    def as_dict(self):
        return dict(self._map)


def get_search_config():
    return SearchConfig


def flatten_single_values(values):
    if len(values) == 1:
        return values[0]
    return values


def groups_to_dict(defaults):
    return {
        k: v.as_dict()
        for k, v in defaults.items()
    }


def stringify(values):
    if isinstance(values, dict):
        return {
            str(k): stringify(v)
            for k, v in values.items()
        }
    return values


class SearchConfigRegistry:

    def __init__(self):
        self._initialize_storage()

    def _initialize_storage(self):
        self.registry = SortedTupleMap()
        self.aliases = {'global': SortedTupleMap()}
        self.defaults = {'global': SortedTupleMap()}

    def add(self, config):
        self.registry[config.name] = config

    # Add aliases for mapping random (nonexistant) config name to concrete config(s).
    def add_aliases(self, aliases, group='global'):
        if group not in self.aliases:
            self.aliases[group] = SortedTupleMap()
        for k, v in aliases.items():
            if k in self.registry:
                raise ValueError(
                    f'Alias name {k} conflicts with existing concrete search config. Use different name. {self.as_dict()}'
                )
            self.aliases[group][k] = v

    # Add defaults for mapping existing concrete config names to other config(s).
    def add_defaults(self, defaults, group='global'):
        if group not in self.defaults:
            self.defaults[group] = SortedTupleMap()
        for k, v in defaults.items():
            self.defaults[group][k] = v

    def update(self, config):
        if config.name in self.registry:
            self.get(config.name).update(**config)
        else:
            self.add(config)

    def register_from_func(self, name, func):
        config = get_search_config()(name, func())
        self.update(config)

    def register_from_item(self, item):
        config = get_search_config().from_item(item)
        self.update(config)

    def register_pieces_from_item(self, item):
        config_factory = get_search_config()
        for piece in config_factory.PIECES_KEYS:
            config = config_factory.from_item_piece(item, piece)
            if len(config) > 0:
                self.update(config)

    def clear(self):
        self._initialize_storage()

    def get(self, name, default=None):
        return self.registry.get(name, default)

    def _resolve_config_name(self, name, group='global', use_defaults=True):
        if name in self.aliases.get(group, {}):
            yield from self._resolve_config_names(
                self.aliases[group][name],
                group=group,
                use_defaults=use_defaults
            )
        elif use_defaults and name in self.defaults.get(group, {}):
            yield from self._resolve_config_names(
                self.defaults[group][name],
                group=group,
                use_defaults=False,
            )
        else:
            yield name

    def _resolve_config_names(self, names, group='global', use_defaults=True):
        config_names = []
        for name in names:
            config_names.extend(self._resolve_config_name(name, group=group, use_defaults=use_defaults))
        return config_names

    def get_configs_by_names(self, names, group='global', use_defaults=True):
        config_names = self._resolve_config_names(names, group=group, use_defaults=use_defaults)
        configs = (
            self.get(config_name)
            for config_name in config_names
        )
        return [
            config
            for config in configs
            if config
        ]

    def defaults_to_dict(self):
        return groups_to_dict(
            self.defaults
        )

    def aliases_to_dict(self):
        return groups_to_dict(
            self.aliases
        )

    def defaults_to_json(self):
        return stringify(
            self.defaults_to_dict()
        )

    def aliases_to_json(self):
        return stringify(
            self.aliases_to_dict()
        )

    def as_dict(self):
        return {
            flatten_single_values(name): dict(config.items())
            for name, config in self.registry.as_dict().items()
        }



class MutableConfig(Config):

    def update(self, **kwargs):
        self._kwargs.update(kwargs)


def to_camel_case(name):
    return ''.join(
        value.title()
        for value in name.split('_')
    )


def make_name_for_piece(item, piece):
    return f'{item.__name__}{to_camel_case(piece)}'


def extract_piece_from_item_pieces(item_pieces, piece):
    return {
        k: v
        for k, v in item_pieces.items()
        if k == piece
    }


class SearchConfig(MutableConfig):

    ITEM_CONFIG_LOCATION = 'schema'
    CONFIG_KEYS = [
        'facets',
        'columns',
        'boost_values',
        'matrix',
        'fields',
        'facet_groups',
    ]
    PIECES_KEYS = [
        'facets',
        'columns',
        'facet_groups',
    ]

    def __init__(self, name, config):
        config = config or {}
        super().__init__(
            allowed_kwargs=self.CONFIG_KEYS,
            **{
                k: v
                for k, v in config.items()
                if k in self.CONFIG_KEYS
            }
        )
        self.name = name

    def __getattr__(self, attr):
        if attr in self.CONFIG_KEYS:
            return self.get(attr, {})
        super().__getattr__(attr)

    @classmethod
    def _values_from_item(cls, item):
        return getattr(
            item,
            cls.ITEM_CONFIG_LOCATION,
            {}
        )

    @classmethod
    def from_item(cls, item):
        return cls(
            item.__name__,
            cls._values_from_item(item)
        )

    @classmethod
    def from_item_piece(cls, item, piece):
        item_pieces = cls._values_from_item(item) or {}
        return cls(
            make_name_for_piece(item, piece),
            extract_piece_from_item_pieces(
                item_pieces,
                piece,
            )
        )


@dataclass
class SearchConfigRegistryClientProps:
    registry: SearchConfigRegistry
    group: str = 'global'
    use_defaults: bool = True


class SearchConfigRegistryClient:

    def __init__(self, props: SearchConfigRegistryClientProps):
        self.props = props

    def get(self, value: Union[List[str], str]) -> List[SearchConfig]:
        if not isinstance(value, list):
            value = [value]
        return self.props.registry.get_configs_by_names(
            value,
            group=self.props.group,
            use_defaults=self.props.use_defaults,
        )
