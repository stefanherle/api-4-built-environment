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


def test_ifcguid_2_jsonguid():
    ifc_guid = '2O2Fr$t4X7Zf8NOew3FNr2'
    json_guid = '9808fd7f-dc48-478e-9217-628e833d7d42'
    guids = get_guids(ifc_guid)
    assert guids['json_guid'] == json_guid


def test_jsonguid_2_ifcguid():
    ifc_guid = '2O2Fr$t4X7Zf8NOew3FNr2'
    ifc_json = '9808fd7f-dc48-478e-9217-628e833d7d42'
    guids = get_guids(ifc_json)
    assert guids['ifc_guid'] == ifc_guid