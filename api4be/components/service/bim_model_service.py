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

from api4be.components.repositories.ifc_file_repository import IfcFileRepository

logger = logging.getLogger()


class BimModelService:

    def __init__(self):
        self.ifc_file_repository = IfcFileRepository()

    def get_collections_names(self):
        return self.ifc_file_repository.get_collections().keys()

    def get_projects_of_collection(self, collection_name,):
        return self.ifc_file_repository.get_collection(collection_name)

    def get_project(self, collection_name, project_name):
        return self.ifc_file_repository.get_project(collection_name, project_name)

    def get_ifc_model_of_project(self, collection_name, project_name):
        return self.ifc_file_repository.get_ifc_model(collection_name, project_name)

    def get_ifc_model_of_project_copy(self, collection_name, project_name):
        return self.ifc_file_repository.get_ifc_model_from_file(collection_name, project_name)

    def get_ifc_filepath(self, collection_name, project_name):
        return self.ifc_file_repository.get_ifc_filepath(collection_name, project_name)

    def get_ifc_spatial_tree_of_project(self, collection_name, project_name):
        return self.ifc_file_repository.get_ifc_spatial_tree(collection_name, project_name)

    def get_georef_of_project(self, collection_name, project_name):
        return self.ifc_file_repository.get_georef(collection_name, project_name)

    def get_geojson_of_project(self, collection_name, project_name):
        return self.ifc_file_repository.get_geojson_geometry(collection_name, project_name)