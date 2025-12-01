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

import logging, os

from flask_cors import CORS

import api4be.config
from api4be.components.cache import cache
from api4be.components.repositories.ifc_file_repository import IfcFileRepository
from flask import Flask, render_template

from api4be.components.routes import bim
from api4be.components.routes import gim

def create_app(serving_path=os.path.join(os.path.dirname(__file__), "data"), collections=None):

    app = Flask(__name__)
    CORS(app)
    app.config.from_pyfile('config.py')
    logging.basicConfig(format='[%(levelname)s] %(asctime)s %(funcName)s: %(message)s', datefmt='%Y-%m-%dT%H:%M:%S%z',
                        level=logging.DEBUG)
    app.url_map.strict_slashes = False

    ifc_file_repository = IfcFileRepository.init_ifc_file_repository(serving_path, collections=collections)

    app.register_blueprint(bim, url_prefix=config.API_PATH)
    app.register_blueprint(gim, url_prefix=config.API_PATH)
    cache.init_app(app)

    @app.route('/')
    def landing_page():
        return render_template('index.html', api_address=config.API_ADDRESS + config.API_PATH)

    return app

