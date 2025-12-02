# Copyright (C) 2024-2025  Stefan Herlé
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see {@literal<http://www.gnu.org/licenses/>}.

from urllib.parse import urljoin
from urllib.parse import urlparse, urlunparse

from api4be import config


def _get_request_urls(endpoint, collection_name=None, project_name=None, guid=None):
    URLS_DICT = {}

    if (config.REL_URI):
        parsed = urlparse(endpoint)
        new_parts = ('', parsed.path, parsed.params, parsed.query, parsed.fragment)
        endpoint = urlunparse(('', *new_parts))

    URLS_DICT['BIM_COLLECTIONS_URL'] = endpoint + '/' + 'bim/collections'
    URLS_DICT['GIM_COLLECTIONS_URL'] = endpoint + '/' + 'gim/collections'

    if collection_name is not None:
        URLS_DICT['GIM_COLLECTION_URL'] = URLS_DICT['GIM_COLLECTIONS_URL'] + '/' + collection_name
        URLS_DICT['GIM_ITEMS_URL'] = URLS_DICT['GIM_COLLECTION_URL'] + '/items'
        URLS_DICT['BIM_COLLECTION_URL'] = URLS_DICT['BIM_COLLECTIONS_URL'] + '/' + collection_name
        URLS_DICT['BIM_PROJECTS_URL'] = URLS_DICT['BIM_COLLECTION_URL'] + '/projects'
    else:
        return URLS_DICT

    if project_name is not None:
        URLS_DICT['GIM_PROJECT_URL'] = URLS_DICT['GIM_ITEMS_URL'] + '/' + project_name
        URLS_DICT['BIM_PROJECT_URL'] = URLS_DICT['BIM_PROJECTS_URL'] + '/' + project_name
        URLS_DICT['BIM_IFCITEMS_URL'] = URLS_DICT['BIM_PROJECT_URL'] + '/ifcitems'
    else:
        return URLS_DICT

    if guid is not None:
        URLS_DICT['GIM_IFCITEM_URL'] = URLS_DICT['GIM_PROJECT_URL'] + ':' + guid,
        URLS_DICT['BIM_IFCITEM_URL'] = URLS_DICT['BIM_IFCITEMS_URL'] + '/' + guid
    else:
        return URLS_DICT

    return URLS_DICT


def _is_it_true(value):
    return value.lower() == 'true'


def get_bim_request_query_parameters(request, collection_name=None, project_name=None, guid=None):
    endpoint = urljoin(request.host_url, config.API_PATH)
    URLS_DICT = _get_request_urls(endpoint, collection_name, project_name, guid)

    BIM_PARAMS_DICT = {
        # Query parameters for IFC2JSON lib
        'COMPACT': request.args.get('compact', default=True, type=_is_it_true),
        'NO_INVERSE': request.args.get('no_inverse', default=True, type=_is_it_true),
        'EMPTY_PROPERTIES': request.args.get('empty', default=True, type=_is_it_true),
        'NO_OWNERHISTORY': request.args.get('no_ownership', default=True, type=_is_it_true),
        'GEOMETRY': request.args.get('geometry', default=False, type=_is_it_true),

        # Advanced query parameters for IFC2JSON
        'REFS': request.args.get('refs', default=False, type=_is_it_true),

        # Query parameters for geometry serialization
        'COMPOSED': request.args.get('composed', default=False, type=_is_it_true),
        'COMPOSE_ASSEMBLY': request.args.get('compose_assembly', default=True, type=_is_it_true),

        # Query parameter for format
        'FORMAT': request.args.get('format', default='json', type=str),
    }

    BIM_PARAMS_DICT.update(URLS_DICT)
    return BIM_PARAMS_DICT


def get_gim_request_query_parameters(request, collection_name=None, project_name=None, guid=None):
    endpoint = urljoin(request.host_url, config.API_PATH)
    URLS_DICT = _get_request_urls(endpoint, collection_name, project_name, guid)

    GIM_PARAMS_DICT = {
        # Query parameters for geojson serialization
        'REFS': request.args.get('refs', default=False, type=_is_it_true),
        'COMPOSED': request.args.get('composed', default=True, type=_is_it_true),
        'GTYPE': request.args.get('gtype', default='bbox', type=str),

        # Query parameter for format
        'FORMAT': request.args.get('format', default='application/geo+json', type=str),

    }

    GIM_PARAMS_DICT.update(URLS_DICT)
    return GIM_PARAMS_DICT
