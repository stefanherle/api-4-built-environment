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
import math
import multiprocessing

import ifcopenshell.geom
import numpy as np
from shapely import MultiPoint, Polygon
from shapely.geometry import box
from shapely.ops import unary_union
from ifcopenshell.util.shape import get_bbox_centroid

from api4be.components.utils.logging_utils import print_ifc_element

logger = logging.getLogger()


####################################
# Get 3D shapes of ifc elements
####################################

def get_shape_object_of_ifc_element(element):
    logger.debug(print_ifc_element(element))
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    settings.set('dimensionality', ifcopenshell.ifcopenshell_wrapper.CURVES_SURFACES_AND_SOLIDS)
    shape = ifcopenshell.geom.create_shape(settings, element)
    return shape


def get_shape_of_ifc_element(element):
    shape = get_shape_object_of_ifc_element(element)

    # Indices of vertices per triangle face e.g. [f1v1, f1v2, f1v3, f2v1, f2v2, f2v3, ...]
    faces = shape.geometry.faces

    # Indices of vertices per edge e.g. [e1v1, e1v2, e2v1, e2v2, ...]
    edges = shape.geometry.edges

    # X Y Z of vertices in flattened list e.g. [v1x, v1y, v1z, v2x, v2y, v2z, ...]
    verts = shape.geometry.verts

    # A list of styles that are relevant to this shape
    styles = shape.geometry.materials

    materials = []
    for style in styles:
        material = {}
        # Each style is named after the entity class if a default
        # material is applied. Otherwise, it is named 'surface-style-{SurfaceStyle.name}'
        # All non-alphanumeric characters are replaced with a '-'.
        # logger.debug(style.original_name())
        # material['name'] = style.original_name()

        # A more human readable name
        material['name'] = style.name

        # Each style may have diffuse colour RGB codes
        if style.diffuse:
            material['diffuse'] = [style.diffuse.r(), style.diffuse.g(), style.diffuse.b()]
        else:
            material['diffuse'] = None

        # Each style may have transparency data
        if not math.isnan(style.transparency):
            material['transparency'] = style.transparency
        else:
            material['transparency'] = None
        materials.append(material)

    return {
        'vertices': verts,
        'edges': edges,
        'faces': faces,
        'materials': materials,
        'material_ids': shape.geometry.material_ids,
    }


def get_3d_bbox_of_ifc_element(element):
    shape = None
    try:
        shape = get_shape_of_ifc_element(element)
    except Exception as e:
        logger.error(e)
    grouped_verts = [[shape['vertices'][i], shape['vertices'][i + 1], shape['vertices'][i + 2]] for i in
                     range(0, len(shape['vertices']), 3)]

    return get_3d_bbox_from_list_of_vertices(grouped_verts)


def get_3d_bbox_from_list_of_vertices(vertices):
    np_verts = np.array(vertices)

    min_point = np.min(np_verts, axis=0)
    max_point = np.max(np_verts, axis=0)

    from shapely import MultiPoint
    shapely_points = MultiPoint([min_point.tolist(), max_point.tolist()])

    return shapely_points


########################################################################
# Get 2D footprint [bbox, footprint_approx, footprint] of shape
########################################################################


def _get_2d_bbox_of_shape(shape):
    grouped_verts = [[shape.geometry.verts[i], shape.geometry.verts[i + 1]] for i in
                     range(0, len(shape.geometry.verts), 3)]

    return box(*get_3d_bbox_from_list_of_vertices(grouped_verts).bounds)


def _get_2d_bbox_centroid_of_shape(shape):
    bbox_centroid = get_bbox_centroid(shape.geometry)
    return bbox_centroid


def _get_2d_footprint_of_shape(shape):
    grouped_2d_verts = [[shape.geometry.verts[i], shape.geometry.verts[i + 1]] for i in
                        range(0, len(shape.geometry.verts), 3)]
    grouped_2d_faces = [[shape.geometry.faces[i], shape.geometry.faces[i + 1], shape.geometry.faces[i + 2]] for i in
                        range(0, len(shape.geometry.faces), 3)]

    from shapely import Polygon
    polygons = []
    for face in grouped_2d_faces:
        polygon = Polygon([grouped_2d_verts[face[0]], grouped_2d_verts[face[1]], grouped_2d_verts[face[2]]])
        polygons.append(polygon)

    union_of_faces = unary_union(polygons)

    return union_of_faces

########################################################################
# Get 2D footprint [bbox, footprint_approx, footprint] of element(s)
########################################################################


def get_2d_bbox_of_ifc_element(element):
    bbox = get_3d_bbox_of_ifc_element(element)
    return box(*bbox.bounds)


def get_2d_bbox_of_ifc_elements(model, elements):
    geometries = _use_geom_iterator_on_guids(model, elements, _get_2d_bbox_of_shape)
    return unary_union(geometries)


def get_2d_footprint_approx_of_ifc_element(element):
    shape = None
    try:
        shape = get_shape_object_of_ifc_element(element)
    except Exception as e:
        logger.error(e)
    return _get_2d_bbox_centroid_of_shape(shape)


def get_2d_footprint_approx_of_ifc_elements(model, elements_ids):
    geometries = _use_geom_iterator_on_guids(model, elements_ids, _get_2d_bbox_centroid_of_shape)
    mp = MultiPoint(geometries)
    return mp.convex_hull


def get_2d_footprint_of_ifc_element(element):
    shape = None
    try:
        shape = get_shape_object_of_ifc_element(element)
    except Exception as e:
        logger.error(e)
    return _get_2d_footprint_of_shape(shape)


def get_2d_footprint_of_ifc_elements(model, elements_ids):
    geometries = _use_geom_iterator_on_guids(model, elements_ids, _get_2d_footprint_of_shape)
    return unary_union(geometries)


def _use_geom_iterator_on_guids(model, guids, shape_function):
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    iterator = ifcopenshell.geom.iterator(settings, model, multiprocessing.cpu_count(),
                                          include=[model.by_id(e['ifc_guid']) for e in guids])
    result = []
    if iterator.initialize():
        while True:
            shape = iterator.get()
            result.append(shape_function(shape))
            if not iterator.next():
                break
    return result
