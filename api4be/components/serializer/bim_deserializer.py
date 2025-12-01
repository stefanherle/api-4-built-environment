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

from api4be import ifcjson

logger = logging.getLogger()

def ifcjson_2_model(ifc_json_file):
    logger.debug(ifc_json_file)
    ifc_json = ifcjson.JSON2IFC(ifc_json_file)
    ifc_model = ifc_json.ifcModel()
    return ifc_model


def add_property_sets(model, element, psets):
    owner_history = model.by_type('IfcOwnerHistory')[0]
    for pset in psets:
        property_values = []
        for property in psets[pset]:
            single_value = None
            if isinstance(psets[pset][property], float):
                single_value = model.createIfcPropertySingleValue(property, property, model.create_entity('IfcReal',
                                                                                                          psets[
                                                                                                              pset][
                                                                                                              property]),
                                                                  None)
            elif isinstance(psets[pset][property], int):
                single_value = model.createIfcPropertySingleValue(property, property, model.create_entity('IfcInteger',
                                                                                                          psets[
                                                                                                              pset][
                                                                                                              property]),
                                                                  None)
            elif isinstance(psets[pset][property], bool):
                single_value = model.createIfcPropertySingleValue(property, property, model.create_entity('IfcBoolean',
                                                                                                          psets[
                                                                                                              pset][
                                                                                                              property]),
                                                                  None)
            else:
                single_value = model.createIfcPropertySingleValue(property, property, model.create_entity('IfcText',
                                                                                                          psets[
                                                                                                              pset][
                                                                                                              property]),
                                                                  None)
            property_values.append(single_value)
        property_set = model.createIfcPropertySet(ifcopenshell.guid.new(), owner_history, pset, None, property_values)
        model.createIfcRelDefinesByProperties(ifcopenshell.guid.new(), owner_history, None, None, [element],
                                              property_set)