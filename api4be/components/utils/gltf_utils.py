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

import base64
import json
import logging
import traceback

import numpy as np
import pygltflib

from api4be.components.utils.geom_utils import get_shape_of_ifc_element
from api4be.components.utils.guid_utils import get_guids
from api4be.components.utils.logging_utils import print_ifc_element

logger = logging.getLogger()

def get_gltf_of_ifc_element(element, params):
    try:
        shape = get_shape_of_ifc_element(element)
    except Exception as e:
        traceback.print_exception(type(e), e, e.__traceback__)
        logger.error(e)
        logger.error('Error in getting shape of element: ' + print_ifc_element(element))
        return {}

    grouped_verts = [shape['vertices'][x:x + 3] for x in range(0, len(shape['vertices']), 3)]

    # gltf uses  X, Z, -Y instead of X, Y, Z
    grouped_verts = [[vert[0], vert[2], -1 * vert[1]] for vert in grouped_verts]
    grouped_faces = [[shape['faces'][i], shape['faces'][i + 1], shape['faces'][i + 2]] for i in
                     range(0, len(shape['faces']), 3)]

    meshes = []
    accessors = []
    materials = []
    buffer_views = []
    buffers = []
    binary_blob = None

    # First introduce default material if faces without defined material (-1 in materials_ids)
    if -1 in shape['material_ids']:
        new_material_id = max(shape['material_ids']) + 1
        shape['material_ids'] = [new_material_id if i == -1 else i for i in shape['material_ids']]
        # add default material
        shape['materials'].append(
            {
                'name': 'default',
                'diffuse': [0.9686, 0.9686, 0.9686],
                'transparency': None
            }
        )

    #  loop over materials
    for mat_idx, material in enumerate(shape['materials']):

        # First the material
        base_color = [1.0, 1.0, 1.0, 1.0]
        alpha_mode = pygltflib.OPAQUE

        if material['diffuse'] is not None:
            base_color[0] = material['diffuse'].r()
            base_color[1] = material['diffuse'].g()
            base_color[2] = material['diffuse'].b()
        if material['transparency'] is not None:
            base_color[3] = base_color[3] - material['transparency']
            if material['transparency'] > 1.e-9:
                alpha_mode = pygltflib.BLEND

        materials.append(pygltflib.Material(
            name=material['name'],
            pbrMetallicRoughness=pygltflib.PbrMetallicRoughness(
                baseColorFactor=base_color,
                metallicFactor=0,
                roughnessFactor=0.5
            ),
            doubleSided=True,
            alphaMode=alpha_mode
        ))

        # Second meshes
        matching_meshes = np.array([i for i, x in enumerate(shape['material_ids']) if x == mat_idx])
        last_elements_in_list = (matching_meshes[:-1] != (matching_meshes[1:] - 1)).tolist()
        last_elements_in_list.append(True)
        ends = [i + 1 for i, x in enumerate(last_elements_in_list) if x]
        meshes_of_current_material = []
        prev = 0
        for end in ends:
            meshes_of_current_material.append(matching_meshes[prev:end])
            prev = end

        for current_mesh in meshes_of_current_material:
            mesh_faces = np.array([grouped_faces[idx] for idx in current_mesh])
            mapping = np.unique(mesh_faces.flatten())  # pts indeces of current mesh
            mesh_points = np.array(
                [grouped_verts[idx] for idx in mapping],
                dtype='float32'
            )
            mesh_faces = np.array(
                [[np.where(mapping == v1)[0][0], np.where(mapping == v2)[0][0], np.where(mapping == v3)[0][0]] for
                 (v1, v2, v3) in mesh_faces],
                dtype='uint32'
            )

            triangles_binary_blob = mesh_faces.flatten().tobytes()
            points_binary_blob = mesh_points.tobytes()

            meshes.append(
                pygltflib.Primitive(
                    attributes=pygltflib.Attributes(POSITION=len(accessors) + 1),
                    indices=len(accessors),
                    material=mat_idx
                )
            )

            # Accessor for indices
            accessors.append(
                pygltflib.Accessor(
                    bufferView=len(buffer_views),
                    componentType=pygltflib.UNSIGNED_INT,
                    count=mesh_faces.size,
                    type=pygltflib.SCALAR,
                    max=[int(mesh_faces.max())],
                    min=[int(mesh_faces.min())],
                )
            )
            # Accessor for position
            accessors.append(pygltflib.Accessor(
                bufferView=len(buffer_views) + 1,
                componentType=pygltflib.FLOAT,
                count=len(mesh_points),
                type=pygltflib.VEC3,
                max=mesh_points.max(axis=0).tolist(),
                min=mesh_points.min(axis=0).tolist(),
            ))

            buffer_views.append(
                pygltflib.BufferView(
                    buffer=0,
                    byteLength=len(triangles_binary_blob),
                    byteOffset=0 if binary_blob is None else len(binary_blob),
                    target=pygltflib.ELEMENT_ARRAY_BUFFER,
                )
            )
            if binary_blob is None:
                binary_blob = triangles_binary_blob
            else:
                binary_blob += triangles_binary_blob
            buffer_views.append(
                pygltflib.BufferView(
                    buffer=0,
                    byteOffset=len(binary_blob),
                    byteLength=len(points_binary_blob),
                    target=pygltflib.ARRAY_BUFFER,
                )
            )
            binary_blob += points_binary_blob

    # add buffer
    data = base64.b64encode(binary_blob).decode('utf-8')
    buffers.append(
        pygltflib.Buffer(
            byteLength=len(binary_blob),
            uri=f'{pygltflib.DATA_URI_HEADER}{data}'
        )
    )

    node = pygltflib.Node(mesh=0)

    gltf = pygltflib.GLTF2(
        scene=0,
        scenes=[pygltflib.Scene(nodes=[0])],
        nodes=[node],
        meshes=[pygltflib.Mesh(
            primitives=meshes
        )],
        accessors=accessors,
        bufferViews=buffer_views,
        buffers=buffers,
        materials=materials
    )

    gltf.set_binary_blob(binary_blob)
    gltf.convert_buffers(pygltflib.BufferFormat.DATAURI)

    return gltf


def get_gltf_of_ifc_elements(elements, params):
    gltfs = []
    for element in elements:
        guids = get_guids(element.GlobalId)
        gltfs.append([guids['json_guid'], get_gltf_of_ifc_element(element, params)])

    if len(gltfs) == 0:
        return pygltflib.GLTF2()


    nodes = []
    nodes.append(pygltflib.Node(mesh=0, name=gltfs[0][0]))

    materials = gltfs[0][1].materials.copy()
    accessors = gltfs[0][1].accessors.copy()
    buffer_views = gltfs[0][1].bufferViews.copy()
    buffers = gltfs[0][1].buffers.copy()
    meshes = [pygltflib.Mesh(primitives=gltfs[0][1].meshes[0].primitives.copy())]

    for idx in range(1, len(gltfs)):

        # check for no gltf
        if gltfs[idx][1] == {}:
            logger.debug('GLTF representation is missing for element: ' + gltfs[idx][0])
            continue

        nodes.append(pygltflib.Node(mesh=idx, name=gltfs[idx][0]))

        len_materials = len(materials)
        len_accessors = len(accessors)
        len_buffers = len(buffers)

        materials.extend(gltfs[idx][1].materials)

        accessors2 = gltfs[idx][1].accessors.copy()
        for accessor2 in accessors2:
            accessor2.bufferView += len_accessors
        accessors.extend(accessors2)

        buffer_views2 = gltfs[idx][1].bufferViews.copy()
        for buffer_view2 in buffer_views2:
            buffer_view2.buffer += len_buffers
        buffer_views.extend(buffer_views2)

        buffers.extend(gltfs[idx][1].buffers)

        meshes2 = gltfs[idx][1].meshes[0].primitives.copy()
        for mesh2 in meshes2:
            mesh2.attributes.POSITION += len_accessors
            mesh2.indices += len_accessors
            mesh2.material += len_materials
        meshes.append(pygltflib.Mesh(primitives=meshes2))

    gltf = pygltflib.GLTF2(
        scene=0,
        scenes=[pygltflib.Scene(nodes=list(range(0, len(gltfs))))],
        nodes=nodes,
        meshes=meshes,
        accessors=accessors,
        bufferViews=buffer_views,
        buffers=buffers,
        materials=materials
    )
    return gltf


def get_json_serialized_gltf_of_ifc_element(element, params):
    gltf = get_gltf_of_ifc_element(element, params)
    return json.loads(gltf.gltf_to_json())


def get_json_serialized_gltf_of_ifc_elements(elements, params):
    gltf = get_gltf_of_ifc_elements(elements, params)
    return json.loads(gltf.gltf_to_json())