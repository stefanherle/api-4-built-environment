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

import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.geolocation
import pyproj
import shapely
from shapely.ops import transform

logger = logging.getLogger()


def check_georef_options(model):
    map_conversion = None
    projected_crs = None

    if model.schema.startswith('IFC4'):
        ifc_project = model.by_type('IfcProject')[0]

        for contexts in ifc_project.RepresentationContexts:
            for coordinate_operation in contexts.HasCoordinateOperation:
                map_conversion = {
                    'Eastings': coordinate_operation.Eastings,
                    'Northings': coordinate_operation.Northings,
                    'OrthogonalHeight': coordinate_operation.OrthogonalHeight,
                    'XAxisAbscissa': coordinate_operation.XAxisAbscissa,
                    'XAxisOrdinate': coordinate_operation.XAxisOrdinate,
                    'Scale': coordinate_operation.Scale
                }

                projected_crs = {
                    'Name': coordinate_operation.TargetCRS.Name
                }

    if map_conversion is None:
        ifc_site = model.by_type('IfcSite')[0]
        psets = ifcopenshell.util.element.get_psets(ifc_site)
        if 'ePSet_MapConversion' in psets and 'ePSet_ProjectedCRS' in psets:
            map_conversion = psets['ePSet_MapConversion']
            projected_crs = psets['ePSet_ProjectedCRS']

    if map_conversion is not None and projected_crs is not None:
        eastings = map_conversion['Eastings']
        northings = map_conversion['Northings']
        height = map_conversion['OrthogonalHeight']
        x_axis_abscissa = map_conversion['XAxisAbscissa'] or 0
        x_axis_ordinate = map_conversion['XAxisOrdinate'] or 0
        scale = map_conversion['Scale'] or 1
        epsg = projected_crs['Name']

        # function return rotation (accw = positive); ccw should be positive
        angle = ifcopenshell.util.geolocation.xaxis2angle(x_axis_abscissa, x_axis_ordinate)
        phi = math.radians(angle)

        def _transform(x, y, z=0):
            return ifcopenshell.util.geolocation.xyz2enh(x ,y ,z, eastings, northings, height, x_axis_abscissa, x_axis_ordinate, scale)

        return {
            'crs': epsg,
            'transform_from_local': _transform,
            'trs': {
                'translation': [eastings, northings, height],
                'rotation': phi,
                'scale': [scale, scale, scale],
            }
        }
    else:
        return None


def georef_params_to_4978(georef_params):
    origin = transform_local_to_world(shapely.Point(0, 0, 0), georef_params, to='EPSG:4978')

    # check for meridian convergence
    source_proj = pyproj.CRS(str(georef_params['crs']))
    p = pyproj.Proj(source_proj)
    facts = p.get_factors(origin.x, origin.y)
    rotation = georef_params['trs']['rotation'] + facts.meridian_convergence * (math.pi / 180)

    return {
        'trs': {
            'translation': [origin.x, origin.y, origin.z],
            'rotation': georef_params['trs']['rotation'],
            'scale': georef_params['trs']['scale'],
            'crs': 'EPSG:4978'
        }
    }


def georef_params_to_4326(georef_params):
    origin = transform_local_to_world(shapely.Point(0, 0, 0), georef_params, to='EPSG:4326')

    # check for meridian convergence
    source_proj = pyproj.CRS(str(georef_params['crs']))
    p = pyproj.Proj(source_proj)
    facts = p.get_factors(origin.x, origin.y)
    rotation = georef_params['trs']['rotation'] + facts.meridian_convergence * (math.pi / 180)

    return {
        'trs': {
            'translation': [origin.x, origin.y, origin.z],
            'rotation': rotation,
            'scale': georef_params['trs']['scale'],
            'crs': 'EPSG:4326'
        }
    }


def transform_local_to_world(geometry, georef_params, to='EPSG:4326'):
    logger.debug(georef_params)
    geometry_global = transform(georef_params['transform_from_local'], geometry)

    if to != georef_params['crs']:
        # transform to espg:4326
        source_proj = pyproj.CRS(str(georef_params['crs']))
        target_proj = pyproj.CRS(to)
        transform_2_4326 = pyproj.Transformer.from_crs(source_proj, target_proj, always_xy=True).transform
        geometry_global = shapely.ops.transform(transform_2_4326, geometry_global)

    return geometry_global
