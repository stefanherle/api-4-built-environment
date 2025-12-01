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

import logging

from flask import request, jsonify, render_template
from furl import furl

from api4be.components.routes import gim
from api4be.components.serializer import gim_serializer
from api4be.components.service.bim_model_service import BimModelService
from api4be.components.utils.routes_utils import get_gim_request_query_parameters

bim_model_service = BimModelService()

logger = logging.getLogger()


@gim.route('/gim')
def get_gim():
    if 'format' in request.args and request.args['format'] == 'text/html':
        f = furl(request.url).remove(['format'])
        return get_generic_json_html('GIM Datasets', 'GIM Datasets', f.url)

    params = get_gim_request_query_parameters(request)
    result = {
        'collections@gim.navigationLink': params['GIM_COLLECTIONS_URL']
    }
    return jsonify(result)


@gim.route('/gim/collections')
def get_collections():
    if 'format' in request.args and request.args['format'] == 'text/html':
        f = furl(request.url).remove(['format'])
        return get_generic_json_html('GIM collections', 'GIM collections', f.url)

    params = get_gim_request_query_parameters(request)
    collections_names = bim_model_service.get_collections_names()
    result = gim_serializer.serialize_collections_info(collections_names, params)
    return jsonify(result)


@gim.route('/gim/collections/<collection_name>')
def get_collection(collection_name):
    if 'format' in request.args and request.args['format'] == 'text/html':
        f = furl(request.url).remove(['format'])
        return get_generic_json_html('GIM collection ' + collection_name, collection_name, f.url)

    params = get_gim_request_query_parameters(request, collection_name=collection_name)
    collection_projects = bim_model_service.get_projects_of_collection(collection_name)
    result = gim_serializer.serialize_collection_info(collection_name, collection_projects, params)
    return jsonify(result)


@gim.route('/gim/collections/<collection_name>/items')
def get_collection_items(collection_name='default'):
    if 'format' in request.args and request.args['format'] == 'text/html':
        f = furl(request.url).remove(['format'])
        return get_geojson_html(collection_name, f.url)

    params = get_gim_request_query_parameters(request, collection_name=collection_name)
    collection_projects = bim_model_service.get_projects_of_collection(collection_name)
    collection_as_geojson = gim_serializer.serialize_collection_projects_as_geojson(collection_projects, params)

    return jsonify(collection_as_geojson)


@gim.route('/gim/collections/<collection_name>/items/<project_name>')
def get_project(project_name, collection_name='default'):
    if 'format' in request.args and request.args['format'] == 'text/html':
        f = furl(request.url).remove(['format'])
        return get_geojson_html(project_name, f.url)

    params = get_gim_request_query_parameters(request, collection_name=collection_name, project_name=project_name)
    # filteroptions:
    if 'type' in request.args:
        filter_by_type = request.args.get('type')
        model = bim_model_service.get_ifc_model_of_project(project_name, collection_name)
        elements = model.by_type(filter_by_type)
        geojson = gim_serializer.serialize_ifcelements_as_geojson(model, elements, params,
                                                                  georef=bim_model_service.get_georef_of_project(
                                                                      collection_name, project_name))
        return jsonify(geojson)
    else:
        project = bim_model_service.get_project(collection_name, project_name)
        geojson = gim_serializer.serialize_project_as_geojson(project_name, project, params)
        return jsonify(geojson)


@gim.route('/gim/collections/<collection_name>/items/<project_name>/elements/<guid>')
@gim.route('/gim/collections/<collection_name>/items/<project_name>:<guid>')
def get_ifc_element(project_name, guid, collection_name='default'):
    if 'format' in request.args and request.args['format'] == 'text/html':
        f = furl(request.url).remove(['format'])
        return get_geojson_html(project_name + ':' + guid, f.url)

    params = get_gim_request_query_parameters(request, collection_name=collection_name, project_name=project_name, guid=guid)
    model = bim_model_service.get_ifc_model_of_project(collection_name, project_name)
    element_as_geojson = gim_serializer.serialize_ifcelement_by_guid_as_geojson(model, guid, params,
                                                                                georef=bim_model_service.get_georef_of_project(
                                                                                    collection_name, project_name))
    return jsonify(element_as_geojson)


####################################
# Return in HTML format
####################################

def get_geojson_html(name, geojson_url):
    return render_template('gim/item.html', name=name, geojson_url=geojson_url)


def get_generic_json_html(title, name, url, formats=[('JSON', 'json')]):
    return render_template('json.html', title=title, name=name, url=url, formats=formats)
