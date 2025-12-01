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

class IfcSpatialTree:

    def __init__(self, name, ifc_model):
        self.ifc_model = ifc_model
        self.root = SpatialTreeNode(name, 'File', name)
        self.reload_tree()

    def add_object_in_tree(self, ifc_object, parent_item):
        tree_item = SpatialTreeNode(ifc_object.Name, ifc_object.is_a(), ifc_object.GlobalId)
        parent_item.add_child(tree_item)
        if hasattr(ifc_object, 'ContainsElements'):
            for rel in ifc_object.ContainsElements:
                for element in rel.RelatedElements:
                    self.add_object_in_tree(element, tree_item)
        if hasattr(ifc_object, 'IsDecomposedBy'):
            for rel in ifc_object.IsDecomposedBy:
                for related_object in rel.RelatedObjects:
                    self.add_object_in_tree(related_object, tree_item)

    def reload_tree(self):
        self.root.children = []
        for item in self.ifc_model.by_type('IfcProject'):
            self.add_object_in_tree(item, self.root)

    def as_dict(self):
        return self.root.as_dict()


class SpatialTreeNode:
    def __init__(self, name, type, globalId):
        self.name = name
        self.type = type
        self.globalId = globalId
        self.children = []

    def add_child(self, child):
        self.children.append(child)

    def as_dict(self):
        return {
            'name': self.name,
            'type': self.type,
            'globalId': self.globalId,
            'data': [child.as_dict() for child in self.children if isinstance(child, SpatialTreeNode)]
        }
