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

import inspect
import logging
import os
import sys

import ifcopenshell
from flask import jsonify

from api4be.components.cache import cache
from api4be.components.utils import gltf_utils
from api4be.components.utils.guid_utils import get_guids, ifc_2_json_guid
from api4be.components.utils.spatial_tree_utils import collect_containing_geometry_elements, \
    collect_containing_geometry_elements_ids

from api4be import ifcjson

logger = logging.getLogger()


@cache.memoize()
def model_2_ifcjson(model, params):
    return _model_2_ifcjson(model, params)


@cache.memoize()
def ifc_element_2_ifcjson(guid, model, params):
    return _ifc_element_2_ifcjson(guid, model, params)


@cache.memoize()
def serialize_collections_info(collections_names, params):
    return _serialize_collections_info(collections_names, params)


@cache.memoize()
def serialize_collection_info(collection_name, projects_dict, params):
    return _serialize_collection_info(collection_name, projects_dict, params)


@cache.memoize()
def serialize_projects_info(collection_name, projects_dict, params):
    return _serialize_projects_info(collection_name, projects_dict, params)


@cache.memoize()
def serialize_project_info(collection_name, project_dict, params):
    return _serialize_project_info(collection_name, project_dict, params)


@cache.memoize()
def serialize_ifc_element_info(model, guid, params):
    return _serialize_ifc_element_info(model, guid, params)


@cache.memoize()
def serialize_psets(model, guid):
    return _serialize_psets(model, guid)


@cache.memoize()
def serialize_geometry(model, guid, params):
    return _serialize_geometry(model, guid, params)


@cache.memoize()
def serialize_materials(model, guid):
    return _serialize_materials(model, guid)


@cache.memoize()
def serialize_project_tree(tree_dict, params):
    return _serialize_project_tree(tree_dict, params)


def _model_2_ifcjson(model, params):
    ifcjson_project = ifcjson.IFC2JSON4(model, COMPACT=params['COMPACT'], NO_INVERSE=params['NO_INVERSE'],
                                        EMPTY_PROPERTIES=params['EMPTY_PROPERTIES'],
                                        NO_OWNERHISTORY=params['NO_OWNERHISTORY'],
                                        GEOMETRY=params['GEOMETRY']).spf2Json()

    return jsonify(ifcjson_project)


def _ifc_element_2_ifcjson(guid, model, params):
    serializer = ifcjson.IFC2JSON4(model, COMPACT=params['COMPACT'], NO_INVERSE=params['NO_INVERSE'],
                                   EMPTY_PROPERTIES=params['EMPTY_PROPERTIES'],
                                   NO_OWNERHISTORY=params['NO_OWNERHISTORY'],
                                   GEOMETRY=params['GEOMETRY'])

    guids = get_guids(guid)

    entity = model.by_id(guids['ifc_guid'])
    entity_attributes = entity.__dict__
    entity_type = entity_attributes['type']
    if not entity_type == 'IfcOwnerHistory':
        if not serializer.NO_INVERSE:
            for attr in entity.wrapped_data.get_inverse_attribute_names():
                inverse_attribute = getattr(entity, attr)
                attr_value = serializer.getAttributeValue(inverse_attribute)
                if not attr_value and attr_value is not False:
                    continue

                if params['REFS']:
                    if attr in ['IsDecomposedBy', 'Decomposes', 'IsDefinedBy', 'PropertyDefinitionOf',
                                'ContainsElements', 'ContainedInStructure', 'ObjectTypeOf', 'HasAssociations',
                                'IsTypedBy']:
                        for rel in attr_value:
                            if 'relatingObject' in rel:
                                rel['relatingObject' + '@bim.navigationLink'] = params['BIM_IFCITEMS_URL'] + '/' + \
                                                                                rel['relatingObject']['globalId']
                                del rel['relatingObject']
                            if 'relatedObjects' in rel:
                                rel['relatedObjects' + '@bim.navigationLink'] = []
                                for relObj in rel['relatedObjects']:
                                    rel['relatedObjects' + '@bim.navigationLink'].append(
                                        params['BIM_IFCITEMS_URL'] + '/' + relObj['globalId'])
                                del rel['relatedObjects']
                            if 'relatingMaterial' in rel:
                                rel['relatingMaterials' + '@bim.navigationLink'] = params['BIM_IFCITEMS_URL'] + '/' + \
                                                                                   guids['json_guid'] + '/' + 'materials'
                                del rel['relatingMaterial']
                            if 'relatingMaterials' in rel:
                                rel['relatingMaterials' + '@bim.navigationLink'] = params['BIM_IFCITEMS_URL'] + '/' + \
                                                                                   guids['json_guid'] + '/' + 'materials'
                                del rel['relatingMaterials']
                            if 'relatingPropertyDefinition' in rel:
                                rel['relatingPropertyDefinition' + '@bim.navigationLink'] = params[
                                                                                                'BIM_IFCITEMS_URL'] + '/' + \
                                                                                            rel[
                                                                                                'relatingPropertyDefinition'][
                                                                                                'globalId']
                                del rel['relatingPropertyDefinition']
                            if 'relatedElements' in rel:
                                rel['relatedElements' + '@bim.navigationLink'] = []
                                for relObj in rel['relatedElements']:
                                    rel['relatedElements' + '@bim.navigationLink'].append(
                                        params['BIM_IFCITEMS_URL'] + '/' + relObj['globalId'])
                                del rel['relatedElements']
                            if 'relatingStructure' in rel:
                                rel['relatingStructure' + '@bim.navigationLink'] = params['BIM_IFCITEMS_URL'] + '/' + \
                                                                                   rel['relatingStructure'][
                                                                                       'globalId']
                                del rel['relatingStructure']
                            if 'relatingType' in rel:
                                rel['relatingType' + '@bim.navigationLink'] = params['BIM_IFCITEMS_URL'] + '/' + \
                                                                              rel['relatingType']['globalId']
                                del rel['relatingType']
                entity_attributes[attr] = attr_value

    entity_attributes['GlobalId'] = guids['json_guid']
    entity_attributes['IfcGlobalId'] = guids['ifc_guid']

    ifcjson_element = serializer.createFullObject(entity_attributes)
    del serializer
    return jsonify(ifcjson_element)


def _serialize_collections_info(collections_names, params):
    result_collections = []
    for collection_name in collections_names:
        result_collections.append({
            'id': collection_name,
            'name': collection_name,
            'title': collection_name,
            'collection@bim.navigationLink': params['BIM_COLLECTIONS_URL'] + '/' + collection_name,
        })
    return result_collections


def _serialize_collection_info(collection_name, projects_dict, params):
    projects = []
    for key, value in projects_dict.items():
        projects.append({
            'id': value['id'],
            'name': value['name'],
            'title': value['title'],
            'project@bim.navigationLink': params['BIM_PROJECTS_URL'] + '/' + key
        })
    result = {
        'id': collection_name,
        'name': collection_name,
        'title': collection_name,
        'projects@bim.navigationLink': params['BIM_PROJECTS_URL'],
        'projects': projects,
        'total': len(projects_dict)
    }
    return result


def _serialize_projects_info(collection_name, projects_dict, params):
    result = []
    for project_name, project_dict in projects_dict.items():
        result.append(_serialize_project_info(collection_name, project_dict, params))
    return result


def _serialize_project_info(collection_name, project_dict, params):
    project_info = {
        'id': project_dict['id'],
        'name': project_dict['name'],
        'title': project_dict['title'],
        'collection@bim.navigationLink': params['BIM_COLLECTION_URL'],
        'project@bim.navigationLink': params['BIM_PROJECTS_URL'] + '/' + project_dict['id'],
        'ifcproject@bim.navigationLink': params['BIM_PROJECTS_URL'] + '/' + project_dict['id'] + '/ifcitems/' +
                                         project_dict['ifc_project_guid']['json_guid'],
        'tree@bim.navigationLink': params['BIM_PROJECTS_URL'] + '/' + project_dict['id'] + '/tree',
        'georef@bim.navigationLink': params['BIM_PROJECTS_URL'] + '/' + project_dict['id']+ '/georef',
        'geometry@bim.navigationLink': params['BIM_PROJECTS_URL'] + '/' + project_dict['id'] + '/geometry',
        'project@gim.navigationLink': params['GIM_ITEMS_URL'] + '/' + project_dict['id']
    }
    return project_info


def _serialize_ifc_element_info(model, guid, params):
    guids = get_guids(guid)
    entity = model.by_id(guids['ifc_guid'])
    entity_info = entity.get_info(scalar_only=True)
    return {k: v for k, v in entity_info.items() if v is not None}


def _serialize_psets(model, guid):
    guids = get_guids(guid)
    entity = model.by_id(guids['ifc_guid'])
    return _serialize_psets_entity(entity)


def _serialize_psets_entity(entity):
    psets = ifcopenshell.util.element.get_psets(entity)
    return psets


def _serialize_geometry(model, guid, params):
    guids = get_guids(guid)
    entity = model.by_id(guids['ifc_guid'])
    return _serialize_geometry_entity(entity, params)


def _serialize_geometry_entity(entity, params):
    if (hasattr(entity, 'CompositionType') or entity.is_a('IFCProject') or len(
            entity.IsDecomposedBy) > 0) and not entity.is_a('IFCSpace'):

        if params['COMPOSED'] or (params['COMPOSE_ASSEMBLY'] and entity.is_a('IFCElementAssembly')):
            elements = collect_containing_geometry_elements(entity)
            return gltf_utils.get_json_serialized_gltf_of_ifc_elements(elements, params)
        else:
            elements_with_geometry = collect_containing_geometry_elements_ids(entity)
            geometry_hrefs = []
            for element in elements_with_geometry:
                geometry_hrefs.append(params['BIM_IFCITEMS_URL'] + '/' + element['json_guid'] + '/geometry')
            return geometry_hrefs
    else:
        return gltf_utils.get_json_serialized_gltf_of_ifc_element(entity, params)


def _serialize_materials(model, guid):
    guids = get_guids(guid)
    entity = model.by_id(guids['ifc_guid'])
    return _serialize_materials_entity(entity)


def _serialize_materials_entity(entity):
    materials = ifcopenshell.util.element.get_materials(entity)
    if len(materials) == 0:
        return {}
    materials_list = []
    for material in materials:
        material_dict = {
            "name": getattr(material, "Name", None),
            "description": getattr(material, "Description", None),
            "category": getattr(material, "Category", None),
            "properties": {}
        }
        for props in material.HasProperties:
            if props.is_a("IfcMaterialProperties"):
                for prop in props.Properties:
                    material_dict["properties"][prop.Name] = prop.NominalValue.wrappedValue
        materials_list.append(material_dict)
    return materials_list


def _serialize_project_tree(tree_dict, params):
    # enhance tree to refs to ifcelements
    def add_ref(parent):
        for item in parent['data']:
            item['ifcGlobalId'] = item['globalId']
            json_guid = ifc_2_json_guid(item['globalId'])
            item['ifcitem' + '@bim.navigationLink'] = params['BIM_IFCITEMS_URL'] + '/' + json_guid
            item['geometry' + '@bim.navigationLink'] = params['BIM_IFCITEMS_URL'] + '/' + json_guid + '/geometry'
            item['psets' + '@bim.navigationLink'] = params['BIM_IFCITEMS_URL'] + '/' + json_guid + '/psets'
            item['materials' + '@bim.navigationLink'] = params['BIM_IFCITEMS_URL'] + '/' + json_guid + '/materials'
            item['feature' + '@gim.navigationLink'] = params['GIM_PROJECT_URL'] + ':' + json_guid
            item['globalId'] = json_guid
            add_ref(item)

    add_ref(tree_dict)
    return tree_dict
