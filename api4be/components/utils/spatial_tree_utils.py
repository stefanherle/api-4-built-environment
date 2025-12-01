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

from api4be.components.utils.guid_utils import get_guids


def collect_containing_geometry_elements(element):
    geometry_elements = []

    def collect_geometries(parent, geometry_elements):

        if hasattr(parent, 'ContainsElements') and len(parent.ContainsElements) > 0:
            for rel in parent.ContainsElements:
                for related_element in rel.RelatedElements:
                    if len(related_element.IsDecomposedBy) > 0:
                        collect_geometries(related_element, geometry_elements)
                    else:
                        geometry_elements.append(related_element)
        if hasattr(parent, 'IsDecomposedBy') and len(parent.IsDecomposedBy) > 0:
            for rel in parent.IsDecomposedBy:
                for related_object in rel.RelatedObjects:
                    if hasattr(related_object, 'Representation') and (len(related_object.IsDecomposedBy) > 0 or (
                            hasattr(related_object, 'ContainsElements') and len(related_object.ContainsElements) > 0)):
                        collect_geometries(related_object, geometry_elements)
                    else:
                        geometry_elements.append(related_object)

    collect_geometries(element, geometry_elements)
    return geometry_elements


def collect_containing_geometry_elements_ids(element):
    geometry_elements_guids = []
    geometry_elements = collect_containing_geometry_elements(element)
    for geometry_element in geometry_elements:
        geometry_element_guids = get_guids(geometry_element.GlobalId)
        geometry_elements_guids.append(geometry_element_guids)
    return geometry_elements_guids
