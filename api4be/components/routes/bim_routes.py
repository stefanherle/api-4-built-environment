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

import ifcopenshell
from flask import request, send_file, jsonify, render_template
from furl import furl

from api4be.components.routes import bim
from api4be.components.serializer import bim_serializer
from api4be.components.service.bim_model_service import BimModelService
from api4be.components.utils.routes_utils import get_bim_request_query_parameters
from api4be.components.utils.georef_utils import georef_params_to_4978, georef_params_to_4326
from api4be.components.utils.guid_utils import get_guids

bim_model_service = BimModelService()
logger = logging.getLogger()


@bim.route('/bim')
def get_bim():
    if 'format' in request.args and request.args['format'] == 'text/html':
        f = furl(request.url).remove(['format'])
        return get_generic_json_html('BIM endpoint', 'BIM endpoint', f.url)

    params = get_bim_request_query_parameters(request)
    result = {
        'collections@bim.navigationLink': params['BIM_COLLECTIONS_URL']
    }
    return jsonify(result)


@bim.route('/bim/collections')
def get_collections():
    if 'format' in request.args and request.args['format'] == 'text/html':
        f = furl(request.url).remove(['format'])
        return get_generic_json_html('Collections', 'Collections', f.url)

    params = get_bim_request_query_parameters(request)
    collections_names = bim_model_service.get_collections_names()
    result = bim_serializer.serialize_collections_info(collections_names, params)
    return jsonify(result)


@bim.route('/bim/collections/<collection_name>')
def get_collection(collection_name):
    if 'format' in request.args and request.args['format'] == 'text/html':
        f = furl(request.url).remove(['format'])
        return get_generic_json_html(collection_name, collection_name, f.url)

    params = get_bim_request_query_parameters(request, collection_name=collection_name)
    projects_dict = bim_model_service.get_projects_of_collection(collection_name)
    result = bim_serializer.serialize_collection_info(collection_name, projects_dict, params)
    return jsonify(result)


@bim.route('/bim/collections/<collection_name>/projects')
def get_collection_models(collection_name):
    if 'format' in request.args and request.args['format'] == 'text/html':
        f = furl(request.url).remove(['format'])
        return get_generic_json_html(collection_name + ' projects', collection_name + ' projects', f.url)

    params = get_bim_request_query_parameters(request, collection_name=collection_name)
    projects_dict = bim_model_service.get_projects_of_collection(collection_name)
    result = bim_serializer.serialize_projects_info(collection_name, projects_dict, params)
    return jsonify(result)


@bim.route('/bim/collections/<collection_name>/projects/<project_name>')
def get_ifc_project(collection_name, project_name):
    params = get_bim_request_query_parameters(request, collection_name=collection_name, project_name=project_name)
    if params['FORMAT'] == 'ifcjson':
        # for ifcjson lib we need to use a copy of the models
        return bim_serializer.model_2_ifcjson(bim_model_service.get_ifc_model_of_project_copy(collection_name, project_name),
                                              params)
    elif params['FORMAT'] == 'text/html':
        f = furl(request.url).remove(['format'])
        return get_generic_json_html(project_name, ['Content', 'Georeferencing', 'Spatial Tree'],
                                     [f.url, (f / 'georef').url, (f / 'tree').url],
                                     formats=[('JSON', 'json'), ('IFCJSON', 'ifcjson')])

    elif params['FORMAT'] == 'ifc':
        path = bim_model_service.get_ifc_filepath(project_name, collection_name)
        with open(path, 'r') as f:
            return f.read()
    elif params['FORMAT'] == 'ifc_file':
        path = bim_model_service.get_ifc_filepath(project_name, collection_name)
        return send_file(path)
    else:
        params['BIM_IFCPROJECT_URL'] = params['BIM_PROJECT_URL'] + '/ifcitems/' + \
                                       bim_model_service.get_project(collection_name, project_name)['ifc_project_guid'][
                                           'json_guid']
        project_dict = bim_model_service.get_project(collection_name, project_name)
        project_info = bim_serializer.serialize_project_info(collection_name, project_dict, params)
        return jsonify(project_info)


@bim.route('/bim/collections/<collection_name>/projects/<project_name>/tree')
def get_ifc_project_spatialtree(collection_name, project_name):
    if 'format' in request.args and request.args['format'] == 'text/html':
        f = furl(request.url).remove(['format'])
        return get_generic_json_html(project_name, project_name, f.url)

    params = get_bim_request_query_parameters(request, collection_name=collection_name, project_name=project_name)
    modeltree = bim_model_service.get_ifc_spatial_tree_of_project(collection_name, project_name)
    return jsonify(bim_serializer.serialize_project_tree(modeltree.as_dict(), params))


@bim.route('/bim/collections/<collection_name>/projects/<project_name>/georef')
def get_ifc_project_georef(project_name, collection_name):
    if 'format' in request.args and request.args['format'] == 'text/html':
        f = furl(request.url).remove(['format'])
        return get_generic_json_html(project_name, project_name, f.url)

    geref = bim_model_service.get_georef_of_project(collection_name, project_name)
    georef4978 = georef_params_to_4978(geref)
    georef4326 = georef_params_to_4326(geref)
    return jsonify([georef4978['trs'], georef4326['trs']])


@bim.route('/bim/collections/<collection_name>/projects/<project_name>/geometry')
def get_ifc_project_geometry(collection_name, project_name):
    params = get_bim_request_query_parameters(request, collection_name=collection_name, project_name=project_name)
    if 'format' in request.args and request.args['format'] == 'text/html':
        f = furl(request.url).remove(['format'])
        return get_ifc_geometry_html(project_name, f.url)

    model = bim_model_service.get_ifc_model_of_project(collection_name, project_name)
    ifcproject_guid = bim_model_service.get_project(collection_name, project_name)['ifc_project_guid']['json_guid']
    gltf = bim_serializer.serialize_geometry(model, ifcproject_guid, params)
    response = jsonify(gltf)
    return response


@bim.route('/bim/collections/<collection_name>/projects/<project_name>/groundplan')
def get_ifc_project_groundplan(collection_name, project_name):
    params = get_bim_request_query_parameters(request, collection_name=collection_name, project_name=project_name)
    geojson = bim_model_service.get_geojson_of_project(collection_name, project_name)
    return jsonify(geojson)


@bim.route('/bim/collections/<collection_name>/projects/<project_name>/ifcitems/<guid>')
def get_ifc_element(collection_name, project_name, guid):
    if 'format' in request.args and request.args['format'] == 'text/html':
        f = furl(request.url).remove(['format'])
        return get_ifc_element_html(project_name, guid, f.url)

    if 'format' in request.args and request.args['format'] == 'ifcjson':
        params = get_bim_request_query_parameters(request, collection_name=collection_name, project_name=project_name, guid=guid)
        # for ifcjson we need to use a copy of the models
        model = bim_model_service.get_ifc_model_of_project_copy(collection_name, project_name)
        response = bim_serializer.ifc_element_2_ifcjson(guid, model, params)
        return response

    params = get_bim_request_query_parameters(request, collection_name=collection_name, project_name=project_name, guid=guid)
    model = bim_model_service.get_ifc_model_of_project(collection_name, project_name)
    response = jsonify(bim_serializer.serialize_ifc_element_info(model, guid, params))
    return response


@bim.route('/bim/collections/<collection_name>/projects/<project_name>/ifcitems/<guid>/psets')
def get_ifc_element_psets(collection_name, project_name, guid):
    if 'format' in request.args and request.args['format'] == 'text/html':
        f = furl(request.url).remove(['format'])
        return get_generic_json_html(project_name, 'PSets of ' + guid, f.url)

    model = bim_model_service.get_ifc_model_of_project(collection_name, project_name)
    response = jsonify(bim_serializer.serialize_psets(model, guid))
    return response


@bim.route('/bim/collections/<collection_name>/projects/<project_name>/ifcitems/<guid>/psets/<pset_name>')
def get_ifc_element_pset(collection_name, project_name, guid, pset_name):
    model = bim_model_service.get_ifc_model_of_project(collection_name, project_name)
    guids = get_guids(guid)
    entity = model.by_id(guids['ifc_guid'])
    psets = ifcopenshell.util.element.get_psets(entity)
    response = jsonify(psets[pset_name])
    return response


@bim.route('/bim/collections/<collection_name>/projects/<project_name>/ifcitems/<guid>/geometry')
def get_ifc_element_geometry(project_name, guid, collection_name):
    params = get_bim_request_query_parameters(request, collection_name=collection_name, project_name=project_name, guid=guid)
    if 'format' in request.args and request.args['format'] == 'text/html':
        f = furl(request.url).remove(['format'])
        return get_ifc_geometry_html(project_name, f.url, guid=guid)

    params = get_bim_request_query_parameters(request, collection_name=collection_name, project_name=project_name, guid=guid)
    model = bim_model_service.get_ifc_model_of_project(collection_name, project_name)
    geometries = bim_serializer.serialize_geometry(model, guid, params)
    response = jsonify(geometries)
    return response

@bim.route('/bim/collections/<collection_name>/projects/<project_name>/ifcitems/<guid>/materials')
def get_ifc_element_material(collection_name, project_name, guid):
    if 'format' in request.args and request.args['format'] == 'text/html':
        f = furl(request.url).remove(['format'])
        return get_generic_json_html(project_name, 'Material of ' + guid, f.url)

    model = bim_model_service.get_ifc_model_of_project(collection_name, project_name)
    response = jsonify(bim_serializer.serialize_materials(model, guid))
    return response


####################################
# Return in HTML format
####################################

def get_ifc_geometry_html(project_name, geometry_url, guid=''):
    return render_template('bim/geom.html', project_name=project_name, guid=guid, geometry_url=geometry_url)


def get_ifc_element_html(project_name, guid, url):
    return render_template('bim/item.html', project_name=project_name, guid=guid, url=url)


def get_generic_json_html(title, name, url, formats=[('JSON', 'json')]):
    return render_template('json.html', title=title, name=name, url=url, formats=formats)
