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
from urllib.parse import urlencode, unquote, quote

from api4be import create_app
app = create_app()

resource_path = 'tests/resources'


def test_collections_route():
    with app.test_client() as c:
        response = c.get('/bimapi/bim/collections')
        json_response = response.get_json()
        assert json_response == [
          {
            'collection@bim.navigationLink': 'http://localhost/bimapi/bim/collections/pim',
            'id': 'pim',
            'name': 'pim',
            'title': 'pim'
          }
        ]


def test_projects_route():
    with app.test_client() as c:
        response = c.get('/bimapi/bim/collections/pim/projects')
        json_response = response.get_json()
        assert json_response == [
          {
            'collection@bim.navigationLink': 'http://localhost/bimapi/bim/collections/pim',
            'geometry@bim.navigationLink': 'http://localhost/bimapi/bim/collections/pim/projects/duplex/geometry',
            'georef@bim.navigationLink': 'http://localhost/bimapi/bim/collections/pim/projects/duplex/georef',
            'id': 'duplex',
            'ifcproject@bim.navigationLink': 'http://localhost/bimapi/bim/collections/pim/projects/duplex/ifcitems/7b7032cc-b822-417b-9aea-642906a29bd5',
            'name': 'duplex',
            'project@bim.navigationLink': 'http://localhost/bimapi/bim/collections/pim/projects/duplex',
            'project@gim.navigationLink': 'http://localhost/bimapi/gim/collections/pim/items/duplex',
            'title': '0001',
            'tree@bim.navigationLink': 'http://localhost/bimapi/bim/collections/pim/projects/duplex/tree'
          }
        ]


def test_project_duplex_route():
    with app.test_client() as c:
        route = '/bimapi/bim/collections/pim/projects/duplex'
        response = c.get(route)
        json_response = response.get_json()
        with open(resource_path + route + '.json', 'r') as file:
            ground_truth = json.load(file)
            assert json_response == ground_truth


def test_project_duplex_geometry_route():
    with app.test_client() as c:
        route = '/bimapi/bim/collections/pim/projects/duplex/geometry'
        response = c.get(route)
        json_response = response.get_json()
        with open(resource_path + route + '.json', 'r') as file:
            ground_truth = json.load(file)
            assert json_response == ground_truth


def test_project_duplex_geometry_composed_route():
    with app.test_client() as c:
        route = '/bimapi/bim/collections/pim/projects/duplex/geometry?composed=true'
        response = c.get(route)
        json_response = response.get_json()
        with open(resource_path + quote(route) + '.json', 'r') as file:
            ground_truth = json.load(file)
            assert json_response == ground_truth


def test_project_duplex_georef_route():
    with app.test_client() as c:
        route = '/bimapi/bim/collections/pim/projects/duplex/georef'
        response = c.get(route)
        json_response = response.get_json()
        with open(resource_path + route + '.json', 'r') as file:
            ground_truth = json.load(file)
            assert json_response == ground_truth


def test_project_duplex_tree_route():
    with app.test_client() as c:
        route = '/bimapi/bim/collections/pim/projects/duplex/tree'
        response = c.get(route)
        json_response = response.get_json()
        with open(resource_path + route + '.json', 'r') as file:
            ground_truth = json.load(file)
            assert json_response == ground_truth


def test_project_duplex_groundlevel_ifcjson_route():
    with app.test_client() as c:
        route = '/bimapi/bim/collections/pim/projects/duplex/ifcitems/7b7032cc-b822-417b-9aea-6429f95d6512'
        response = c.get(route)
        json_response = response.get_json()
        with open(resource_path + route + '.json', 'r') as file:
            ground_truth = json.load(file)
            assert json_response == ground_truth


def test_project_duplex_groundlevel_geometry_route():
    with app.test_client() as c:
        route = '/bimapi/bim/collections/pim/projects/duplex/ifcitems/7b7032cc-b822-417b-9aea-6429f95d6512/geometry'
        response = c.get(route)
        json_response = response.get_json()
        with open(resource_path + route + '.json', 'r') as file:
            ground_truth = json.load(file)
            assert json_response == ground_truth


def test_project_duplex_groundlevel_geometry_composed_route():
    with app.test_client() as c:
        route = '/bimapi/bim/collections/pim/projects/duplex/ifcitems/7b7032cc-b822-417b-9aea-6429f95d6512/geometry?composed=true'
        response = c.get(route)
        json_response = response.get_json()
        with open(resource_path + quote(route) + '.json', 'r') as file:
            ground_truth = json.load(file)
            assert json_response == ground_truth


def test_project_duplex_groundlevel_psets_route():
    with app.test_client() as c:
        route = '/bimapi/bim/collections/pim/projects/duplex/ifcitems/7b7032cc-b822-417b-9aea-6429f95d6512/psets'
        response = c.get(route)
        json_response = response.get_json()
        with open(resource_path + route + '.json', 'r') as file:
            ground_truth = json.load(file)
            assert json_response == ground_truth


def test_project_duplex_door_ifcjson_route():
    with app.test_client() as c:
        route = '/bimapi/bim/collections/pim/projects/duplex/ifcitems/7606d7eb-508f-40ce-a522-9b526ddc7201'
        response = c.get(route)
        json_response = response.get_json()
        with open(resource_path + route + '.json', 'r') as file:
            ground_truth = json.load(file)
            assert json_response == ground_truth


def test_project_duplex_door_geometry_route():
    with app.test_client() as c:
        route = '/bimapi/bim/collections/pim/projects/duplex/ifcitems/7606d7eb-508f-40ce-a522-9b526ddc7201/geometry'
        response = c.get(route)
        json_response = response.get_json()
        with open(resource_path + route + '.json', 'r') as file:
            ground_truth = json.load(file)
            assert json_response == ground_truth


def test_project_duplex_door_psets_route():
    with app.test_client() as c:
        route = '/bimapi/bim/collections/pim/projects/duplex/ifcitems/7606d7eb-508f-40ce-a522-9b526ddc7201/psets'
        response = c.get(route)
        json_response = response.get_json()
        with open(resource_path + route + '.json', 'r') as file:
            ground_truth = json.load(file)
            assert json_response == ground_truth

