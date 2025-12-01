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
from urllib.parse import quote

from api4be import create_app
app = create_app()

resource_path = 'tests/resources'


def test_collections_route():
    with app.test_client() as c:
        response = c.get('/bimapi/gim/collections')
        json_response = response.get_json()
        assert json_response == [
          {
            'collection@bim.navigationLink': 'http://localhost/bimapi/gim/collections/pim',
            'id': 'pim',
            'name': 'pim',
            'title': 'pim'
          }
        ]


def test_items_route():
    with app.test_client() as c:
        route = '/bimapi/gim/collections/pim/items'
        response = c.get(route)
        json_response = response.get_json()
        with open(resource_path + quote(route) + '.json', 'r') as file:
            ground_truth = json.load(file)
            assert json_response == ground_truth


def test_item_duplex_groundlevel_route():
    with app.test_client() as c:
        route = '/bimapi/gim/collections/pim/items/duplex:7b7032cc-b822-417b-9aea-6429f95d6512'
        response = c.get(route)
        json_response = response.get_json()
        with open(resource_path + quote(route) + '.json', 'r') as file:
            ground_truth = json.load(file)
            assert json_response == ground_truth


def test_item_duplex_groundlevel_composed_route():
    with app.test_client() as c:
        route = '/bimapi/gim/collections/pim/items/duplex:7b7032cc-b822-417b-9aea-6429f95d6512?composed=false'
        response = c.get(route)
        json_response = response.get_json()
        with open(resource_path + quote(route) + '.json', 'r') as file:
            ground_truth = json.load(file)
            assert json_response == ground_truth
