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

import ifcopenshell.guid as guid


def json_2_ifc_guid(global_id):
    return guid.compress(global_id.replace('-', ''))


def ifc_2_json_guid(global_id):
    return guid.split(guid.expand(global_id)).replace('{', '').replace('}', '')


def get_json_guid(element):
    return ifc_2_json_guid(element.GlobalId)


def get_guids_by_element(element):
    return get_guids(element.GlobalId)


def get_guids(global_id):
    ifc_guid = global_id
    json_guid = global_id
    if '-' in global_id:
        ifc_guid = json_2_ifc_guid(global_id)
    else:
        json_guid = ifc_2_json_guid(global_id)
    return {
        'json_guid': json_guid,
        'ifc_guid': ifc_guid
    }
