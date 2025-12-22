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
import os
import shutil
import logging

import ifcopenshell

from api4be.components.serializer import bim_deserializer, gim_serializer
from api4be.components.utils.georef_utils import check_georef_options
from api4be.components.models.spatial_tree import IfcSpatialTree
from api4be.components.utils.guid_utils import get_guids
from api4be import config

ifc_file_repository = None

logger = logging.getLogger()


class IfcFileRepository(object):
    collections = {}
    serving_path = None
    tmp_path = None

    def __new__(cls):
        """
        Overwrite new method to create service singleton
        """
        if not hasattr(cls, 'instance'):
            cls.instance = super(IfcFileRepository, cls).__new__(cls)
        return cls.instance

    @staticmethod
    def init_ifc_file_repository(serving_path, collections=None):
        """
        Initializes a new Ifc models service for the serving path
        """
        logger.info('init models')
        ifc_file_repository = IfcFileRepository()
        ifc_file_repository.serving_path = serving_path
        ifc_file_repository.tmp_path = 'tmp'
        for collection_folder in os.listdir(serving_path):
            if os.path.isdir(os.path.join(serving_path, collection_folder)) and (collections is None or collection_folder in collections):
                for project_file in os.listdir(os.path.join(serving_path, collection_folder)):
                    if os.path.isfile(os.path.join(serving_path, collection_folder, project_file)) and project_file.endswith('.ifc'):
                        ifc_file_repository.__insert_model(os.path.join(serving_path, collection_folder), project_file, collection_folder)
        ifc_file_repository.print_models()
        return ifc_file_repository

    def __insert_model(self, collection_path, project_file, collection_name):
        """
        Helper function for initialization to load single models and insert into service
        """
        logger.debug(str(os.path.join(collection_path, project_file)))
        ifc_model = ifcopenshell.open(str(os.path.join(collection_path, project_file)))
        self.insert_ifc_model(project_file.split('.')[0], ifc_model, collection_path, collection_name)

    def insert_ifc_model(self, project_name, model, collection_path, collection_name):
        """
        Insert a new models into the collection into the service (into the collection dict)
        """

        ####################################
        # Compute the spatial tree of the models
        ####################################

        ifc_path = os.path.join(collection_path, project_name + '.ifc')
        tree = IfcSpatialTree(project_name, model)

        ####################################
        # Load IfcProject
        ####################################

        ifc_project = model.by_type('IfcProject')[0]
        ifc_project_ids = get_guids(ifc_project.GlobalId)
        project_title = ifc_project.Name

        ####################################
        # Compute georeferenced footprint
        ####################################

        # get georeferenced parameters
        geojson = None
        georef_params = check_georef_options(model)

        # generate geojson if not exists
        geojson_path = os.path.join(collection_path, project_name + '.json')
        if not os.path.exists(geojson_path):
            geojson = gim_serializer.geojson_geometry_of_composed_element(model, ifc_project, gtype=config.DEFAULT_FOOTPRINT_TYPE, georef=georef_params)

            with open(geojson_path, 'w') as fp:
                json.dump(geojson, fp)
        else:
            with open(geojson_path, 'r') as fp:
                geojson = json.load(fp)

        model_object = {
            'id': project_name,
            'name': project_name,
            'title': project_title,
            'model': model,
            'ifc_project_guid': ifc_project_ids,
            'tree': tree,
            'path': ifc_path,
            'geojson_geometry': geojson,
            'georef': georef_params
        }

        ####################################
        # Add models to collection
        ####################################

        if collection_name not in self.collections:
            self.collections[collection_name] = {}
        self.collections[collection_name][project_name] = model_object

    ####################################
    # Getter for projects and collections
    ####################################

    def get_collections(self):
        return self.collections

    def get_collection(self, collection_name):
        return self.collections[collection_name]

    def get_project(self, collection_name, project_name):
        if collection_name in self.collections:
            return self.collections[collection_name][project_name]

    def get_ifc_model(self, collection_name, project_name):
        if collection_name in self.collections:
            return self.collections[collection_name][project_name]['model']

    def get_ifc_model_from_file(self, collection_name, project_name):
        if collection_name in self.collections:
            return ifcopenshell.open(self.collections[collection_name][project_name]['path'])

    def get_ifc_project_id(self, collection_name, project_name):
        return self.collections[collection_name][project_name]['ifc_project_guid']

    def get_ifc_spatial_tree(self, collection_name, project_name):
        if collection_name in self.collections:
            return self.collections[collection_name][project_name]['tree']

    def get_ifc_filepath(self, collection_name, project_name):
        if collection_name in self.collections:
            return self.collections[collection_name][project_name]['path']

    def get_geojson_geometry(self, collection_name, project_name):
        if collection_name in self.collections:
            return self.collections[collection_name][project_name]['geojson_geometry']

    def get_georef(self, collection_name, project_name):
        if collection_name in self.collections:
            return self.collections[collection_name][project_name]['georef']

    def commit_model(self, project_name, collection_name='default', reload_tree=False):
        if collection_name in self.collections:
            self.collections[collection_name][project_name]['model'].write(self.collections[collection_name][project_name]['path'])
            if reload_tree:
                self.collections[collection_name][project_name]['tree'].reload_tree()

    def print_models(self):
        """
        Logs all models
        """
        for key in self.collections.keys():
            logger.info('Loaded collection \"' + key + '\": ' + str(list(self.collections[key].keys())))

    ####################################
    # Modify collections and projects
    ####################################

    def create_collection(self, collection_name):
        collection_path = os.path.join(self.serving_path, collection_name)
        if not os.path.exists(collection_path):
            os.makedirs(os.path.join(collection_path))
            self.collections[collection_name] = {}

    def delete_collection(self, collection_name):
        collection_path = os.path.join(self.serving_path, collection_name)
        shutil.rmtree(collection_path)
        del self.collections[collection_name]

    def create_project_from_ifcjson(self, ifc_json_input, project_name, collection_name='default'):
        tmp_model_path = os.path.join(self.tmp_path, project_name + '.json')
        with open(tmp_model_path, 'w') as f:
            json.dump(ifc_json_input, f)

        model = bim_deserializer.ifcjson_2_model(tmp_model_path)
        output_path = str(os.path.join(self.serving_path, collection_name, project_name + '.ifc'))
        model.write(output_path)
        ifc_model = ifcopenshell.open(output_path)
        os.remove(tmp_model_path)
        self.insert_ifc_model(project_name, ifc_model, os.path.join(self.serving_path, collection_name), collection_name)

    def create_project_from_ifcbytes(self, ifc_bytes, project_name, collection_name='default'):
        ifc_model_path = os.path.join(self.serving_path, collection_name, project_name + '.ifc')
        with open(ifc_model_path, 'wb') as f:
            f.write(ifc_bytes)
        ifc_model = ifcopenshell.open(ifc_model_path)
        self.insert_ifc_model(project_name, ifc_model, os.path.join(self.serving_path, collection_name), collection_name)

    def delete_project(self, project_name, collection_name='default'):
        # os.remove(self.collections[collection][name]['svg'])
        os.remove(self.collections[collection_name][project_name]['path'])
        del self.collections[collection_name][project_name]
