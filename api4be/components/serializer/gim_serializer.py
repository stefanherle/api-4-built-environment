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

import json
import logging

import ifcopenshell
import shapely

from api4be.components.cache import cache
from api4be.components.serializer import bim_serializer
from api4be.components.utils import geom_utils, spatial_tree_utils
from api4be.components.utils.geom_utils import get_2d_bbox_of_ifc_element, get_2d_footprint_of_ifc_element, \
    _get_2d_footprint_of_shape
from api4be.components.utils.georef_utils import transform_local_to_world
from api4be.components.utils.guid_utils import get_guids


@cache.memoize()
def serialize_collections_info(collections_names, params):
    return _serialize_collections_info(collections_names, params)


@cache.memoize()
def serialize_collection_info(collection_name, projects_dict, params):
    return _serialize_collection_info(collection_name, projects_dict, params)


@cache.memoize()
def serialize_collection_projects_as_geojson(projects_dict, params):
    return _serialize_collection_projects_as_geojson(projects_dict, params)


@cache.memoize()
def serialize_project_as_geojson(project_name, project_dict, params):
    return _serialize_project_as_geojson(project_name, project_dict, params)


@cache.memoize()
def serialize_ifcelement_by_guid_as_geojson(model, guid, params, georef=None):
    return _serialize_ifcelement_by_guid_as_geojson(model, guid, params, georef)


@cache.memoize()
def serialize_ifcelement_as_geojson(model, element, params, georef=None, guids=None):
    return _serialize_ifcelement_as_geojson(model, element, params, georef, guids)


@cache.memoize()
def serialize_ifcelements_as_geojson(model, elements, params, georef=None):
    return _serialize_ifcelements_as_geojson(model, elements, params, georef)


def _serialize_collections_info(collections_names, params):
    result_collections = []
    for collection_name in collections_names:
        result_collections.append({
            'id': collection_name,
            'name': collection_name,
            'title': collection_name,
            'collection@bim.navigationLink': params['GIM_COLLECTIONS_URL'] + '/' + collection_name,
        })
    return result_collections


def _serialize_collection_info(collection_name, projects_dict, params):
    projects = []
    for key, value in projects_dict.items():
        projects.append({
            'id': value['id'],
            'name': value['name'],
            'title': value['title'],
            'item@gim.navigationLink': params['GIM_ITEMS_URL'] + '/' + key
        })
    result = {
        'id': collection_name,
        'name': collection_name,
        'title': collection_name,
        'items@gim.navigationLink': params['GIM_ITEMS_URL'],
        'items': projects,
        'total': len(projects_dict)
    }
    return result


def _serialize_collection_projects_as_geojson(projects_dict, params):
    features = []
    for project_name in projects_dict:
        feature = _serialize_project_as_geojson(project_name, projects_dict[project_name], params)
        features.append(feature)

    geojson_feature_collection = {
        'type': 'FeatureCollection',
        'features': features
    }
    return geojson_feature_collection


def _serialize_project_as_geojson(project_name, project_dict, params):
    properties = {}
    properties['id'] = project_dict['id']
    properties['name'] = project_dict['name']
    properties['title'] = project_dict['title']
    properties['project@bim.navigationLink'] = params['BIM_PROJECTS_URL'] + '/' + project_name
    properties['tree@bim.navigationLink'] = params['BIM_PROJECTS_URL'] + '/' + project_name + '/tree'
    properties['feature@gim.navigationLink'] = params['GIM_COLLECTION_URL'] + '/items/' + project_name
    feature = {
        'type': 'Feature',
        'geometry': project_dict['geojson_geometry'],
        'properties': properties
    }
    return feature


def _serialize_ifcelement_by_guid_as_geojson(model, guid, params, georef=None):
    guids = get_guids(guid)
    element = model.by_id(guids['ifc_guid'])
    return _serialize_ifcelement_as_geojson(model, element, params, georef=georef, guids=guids)


def _serialize_ifcelement_as_geojson(model, element, params, georef=None, guids=None):
    if guids is None:
        guids = get_guids(element.GlobalId)

    if hasattr(element, 'CompositionType') or element.is_a('IFCProject'):
        elements_ids_with_geometry = spatial_tree_utils.collect_containing_geometry_elements_ids(element)
        if (params['COMPOSED']):
            geom = geojson_geometry_of_composed_element(model, element, gtype=params['GTYPE'], georef=georef,
                                                        elements_ids=elements_ids_with_geometry)
            properties = {}
            properties['globalId'] = guids['json_guid']
            properties['type'] = element.__dict__['type']
            properties['project@bim.navigationLink'] = params['BIM_PROJECT_URL']
            properties['ifcitem@bim.navigationLink'] = params['BIM_IFCITEM_URL']
            properties['geometry@bim.navigationLink'] = params['BIM_IFCITEM_URL'] + '/geometry'
            properties['features@gim.navigationLink'] = [params['GIM_PROJECT_URL'] + ':' + element_idx['json_guid'] for
                                                         element_idx in elements_ids_with_geometry]
            if params['REFS']:
                properties['psets@bim.navigationLink'] = params['BIM_IFCITEM_URL'] + '/psets'
                properties['materials@bim.navigationLink'] = params['BIM_IFCITEM_URL'] + '/materials'
            else:
                psets = bim_serializer._serialize_psets_entity(element)
                properties['psets'] = psets
                materials = bim_serializer._serialize_materials_entity(element)
                properties['materials'] = materials

            geojson = {
                'type': 'Feature',
                'geometry': geom,
                'properties': properties
            }

            return geojson

        else:
            features = []
            for element_idx in elements_ids_with_geometry:
                decomposed_element = model.by_id(element_idx['ifc_guid'])
                try:
                    geojson_feature = geojson_feature_of_element(decomposed_element, element_idx['json_guid'], params,
                                                                 georef=georef)
                    features.append(geojson_feature)
                except Exception as e:
                    logging.error(e)

            geojson_feature_collection = {
                'type': 'FeatureCollection',
                'features': features
            }
            test = str(geojson_feature_collection)
            return geojson_feature_collection

    else:
        geojson_feature = geojson_feature_of_element(element, guids['json_guid'], params, georef=georef)
        return geojson_feature


def _serialize_ifcelements_as_geojson(model, elements, params, georef=None):
    features = []
    with_feature_collections = False
    for element in elements:
        try:
            guids = get_guids(element.GlobalId)
            geojson_feature = serialize_ifcelement_as_geojson(model, element, params, georef, guids)
            if geojson_feature['type'] == 'FeatureCollection':
                with_feature_collections = True
            features.append(geojson_feature)
        except Exception as e:
            logging.error(e)

    if with_feature_collections:
        return features

    geojson_feature_collection = {
        'type': 'FeatureCollection',
        'features': features
    }

    return geojson_feature_collection


def geojson_geom_of_element(element, gtype='bbox', georef=None):
    geometry_as_polygon = None
    if gtype == 'footprint':
        geometry_as_polygon = get_2d_footprint_of_ifc_element(element)
    else:
        geometry_as_polygon = get_2d_bbox_of_ifc_element(element)

    if georef is not None:
        geometry_as_polygon_world = transform_local_to_world(geometry_as_polygon, georef)
        return json.loads(shapely.to_geojson(geometry_as_polygon_world))
    return json.loads(shapely.to_geojson(geometry_as_polygon))


def geojson_feature_of_element(element, guid, params, georef=None):
    geojson_geom = geojson_geom_of_element(element, gtype=params['GTYPE'], georef=georef)

    properties = {}
    properties['globalId'] = guid
    properties['type'] = element.__dict__['type']
    properties['project@bim.navigationLink'] = params['BIM_PROJECT_URL']
    properties['ifcitem@bim.navigationLink'] = params['BIM_IFCITEMS_URL'] + '/' + guid
    properties['feature@gim.navigationLink'] = params['GIM_PROJECT_URL'] + ':' + guid
    properties['geometry@bim.navigationLink'] = params['BIM_IFCITEMS_URL'] + '/' + guid + '/geometry'
    if params['REFS']:
        properties['psets@bim.navigationLink'] = params['BIM_IFCITEM_URL'] + '/psets'
        properties['materials@bim.navigationLink'] = params['BIM_IFCITEM_URL'] + '/materials'
    else:
        psets = bim_serializer._serialize_psets_entity(element)
        properties['psets'] = psets
        materials = bim_serializer._serialize_materials_entity(element)
        properties['materials'] = materials

    geojson_feature = {
        'type': 'Feature',
        'geometry': geojson_geom,
        'properties': properties
    }
    return geojson_feature


def geojson_geometry_of_composed_element(model, element, gtype='footprint', georef=None, elements_ids=None):
    elements_id_with_geometry = elements_ids
    if elements_id_with_geometry is None:
        elements_id_with_geometry = spatial_tree_utils.collect_containing_geometry_elements_ids(element)

    geom = None
    if element.is_a('IFCSpace'):
        geom = geojson_geom_of_element(element)
    else:
        geometry = None
        if gtype == 'footprint':
            geometry = geom_utils.get_2d_footprint_of_ifc_elements(model, elements_id_with_geometry)
        else:
            geometry = geom_utils.get_2d_bbox_of_ifc_elements(model, elements_id_with_geometry)

        if georef is not None:
            geometry = transform_local_to_world(geometry, georef)
        geom = json.loads(shapely.to_geojson(geometry))

    return geom
