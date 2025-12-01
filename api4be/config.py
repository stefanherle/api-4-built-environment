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

import os
from os import path
from dotenv import load_dotenv


basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))

FLASK_DEBUG = os.getenv('FLASK_DEBUG', True)
API_ADDRESS = os.getenv('API_ADDRESS', 'http://localhost:5000')
API_PATH = os.getenv('API_PATH','/bimapi')
REL_URI = os.getenv('REL_URI', False)
CACHE_TYPE = os.getenv('CACHE_TYPE', 'SimpleCache')
CACHE_DIR = os.getenv('CACHE_DIR','cache')
CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', 0))