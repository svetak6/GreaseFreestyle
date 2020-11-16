# rebuild from scratch
bl_info = {
    "name": "Grease Freestyle R",
    "author": "Folkert de Vries, Andrew Maslennikov",
    "version": (0, 0, 1),
    "blender": (2, 83, 0),
    "location": "Properties > Render > Grease Freestyle",
    "description": "Exports Freestyle's stylized strokes to Grease Pencil sketch",
    "warning": "Alpha version",
    "wiki_url": "",
    "category": "Render",
}

import bpy
import functools
import collections

from bpy.props import (
    BoolProperty,
    EnumProperty,
    PointerProperty,
)

# TODO: fix * module referencies

from freestyle.types import (
    Operators,
    StrokeShader,
    StrokeVertex
)
#from freestyle.functions import CurveMaterialF0D

from mathutils import Vector, Matrix

import parameter_editor



class StrokeCollector(StrokeShader):
    def __init__(self):
        StrokeShader.__init__(self)
        self.viewmap = []

    def shade(self, stroke):
        self.viewmap.append(stroke)

class Callbacks:
    @classmethod
    def poll(cls, scene, linestyle):
#        return scene.render.use_freestyle and scene.freestyle_gpencil_export.use_freestyle_gpencil_export
        return True

    @classmethod
    def modifier_post(cls, scene, layer, lineset):
        if not cls.poll(scene, lineset.linestyle):
            return []

        cls.shader = StrokeCollector()
        return [cls.shader]

    @classmethod
    def lineset_post(cls, scene, layer, lineset):
        if not cls.poll(scene, lineset.linestyle):
            return []

        strokes = cls.shader.viewmap

        #
        print("\nA List of strokes in viewmap:")
        print(strokes)

        print("\nStroke:")
        print(strokes[0])

        print("\nStroke ID:")
        print(strokes[0].id)

        print("\nMedium type (enumeration):")
        print(strokes[0].medium_type)

        print("\nLength of a stroke:")
        print(len(strokes[0]))

        print("\nAddress of a StrokeVertex:")
        print(strokeVertex for strokeVertex in strokes[0])

        for strokeVertex in strokes[0]:
            print("\nStrokeVertex:")
            print(strokeVertex)
            print(strokeVertex.point)
            print(strokeVertex.attribute.thickness)
            print(strokeVertex.attribute.visible)


#        freestyle_to_strokes(scene, lineset, strokes)


############################################################

def register():

    # manipulate shaders list
    parameter_editor.callbacks_modifiers_post.append(Callbacks.modifier_post)
    parameter_editor.callbacks_lineset_post.append(Callbacks.lineset_post)

def unregister():

    # manipulate shaders list
    parameter_editor.callbacks_modifiers_post.remove(Callbacks.modifier_post)
    parameter_editor.callbacks_lineset_post.remove(Callbacks.lineset_post)

if __name__ == '__main__':
    register()

