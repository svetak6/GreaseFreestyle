# rebuild from scratch
bl_info = {
    "name": "Grease Freestyle R",
    "author": "Andrew Maslennikov",
    "version": (0, 0, 2),
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
from mathutils import Vector, Matrix

from freestyle.types import (
    Operators,
    StrokeShader,
    StrokeVertex
)
#from freestyle.functions import CurveMaterialF0D

import parameter_editor

# get the exact scene dimensions of rendered image
def render_height(scene):
    return int(scene.render.resolution_y * scene.render.resolution_percentage / 100)
def render_width(scene):
    return int(scene.render.resolution_x * scene.render.resolution_percentage / 100)
def render_dimensions(scene):
    return render_width(scene), render_height(scene)


def get_grease_pencil_data(gpencil_data_name='init_GPencil') -> bpy.types.GreasePencil:
    """
    Get active GreasePencil(ID) or create a new one.
    :param gpencil_data_name:
    :return:
    """
    gpencil_data = bpy.data.grease_pencils.new(gpencil_data_name)

    # for debugging purposes
    print("get_grease_pencil_data")
    return gpencil_data

def get_grease_pencil_layer(gpencil_layer_name='init_GP_Layer') -> bpy.types.GPencilLayer:
    """
    Get active grease pencil layer or create a new one.
    :param gpencil_layer_name:
    :return:
    """

    gpencil_data = get_grease_pencil_data()
    gpencil_layer = gpencil_data.layers.new(gpencil_layer_name, set_active=True)
    # for debugging purposes
    print("get_grease_pencil_layer")

    return gpencil_data, gpencil_layer

def frame_from_frame_number(layer, current_frame):
    """Get a reference to the current frame if it exists, else False"""

    # for debugging purposes
    print("frame_from_frame_number")

    return next((frame for frame in layer.frames if frame.frame_number == current_frame), False)

def get_gpencil_frame(scene, fs_lineset_name):
    """Creates a new GPencil frame (if needed) to store the Freestyle result"""

    # for debugging purposes
    print("get_gpencil_frame start")

    gpencil_data, gpencil_layer = get_grease_pencil_layer(gpencil_layer_name=fs_lineset_name)

    print("get_gpencil_frame start2")
    # ??? layer.frames.get(..., ...) ???
    frame = frame_from_frame_number(gpencil_layer, scene.frame_current) \
            or gpencil_layer.frames.new(scene.frame_current)

    # for debugging purposes
    print("get_gpencil_frame end")

    return gpencil_data, frame


def freestyle_to_gpencil_strokes(fstrokes_map, frame, lineset):
    """Convert freestyle strokes to grease pencil ones"""
    mat = bpy.context.scene.camera.matrix_local.copy()

    fstrokesList = [fstroke for fstroke in fstrokes_map]

    gpstrokesList = []
    gppointsList =[]
    print("01")

    #    for fstroke in fstrokes_map:
    for fstroke in range(len(fstrokesList)):

        # for debugging purposes
        print("freestyle_to_gpencil_strokes for_loop start")

        gpstroke = frame.strokes.new()
        print("02")

        #gpstroke.display_mode = options.draw_mode
        gpstroke.display_mode = '3DSPACE'
        print("03")

        ##!! set THICKNESS and ALPHA of stroke from StrokeAttribute for this StrokeVertex
        # the max width gets pressure 1.0. Smaller widths get a pressure 0 <= x < 1
        base_width = functools.reduce(max,
                                      (sum(svert.attribute.thickness) for svert in fstrokesList[fstroke]),
                                      lineset.linestyle.thickness)
        print("04")
        # set the default (pressure == 1) width for the gpstroke
        gpstroke.line_width = base_width
        print("05")

        width, height = render_dimensions(bpy.context.scene)
        print("06")
        #            for svert, point in zip (fstroke, gpstroke.points):
        for svert in fstrokesList[fstroke]:
            print("07_")
            gpstroke.points.add(count=1, pressure=1, strength=1)
            print("08_")
            x = svert.point[0]
            z = svert.point[1]

            gpoint = gpstroke.points[-1]
            print("09_")
            gpoint.co.x = x / width * 100
            gpoint.co.z = z / height * 100
            print("10_")

            ## TODO: GPencilSculptSettings.lock_axis
            #                point_co = Vector(( abs(x / width), abs(y / height), 0.0 )) * 10

            gppointsList.append(gpoint)
            print("11")

        gpstrokesList.append(gpstroke)

        # for debugging purposes
        print("freestyle_to_gpencil_strokes for_loop end")

    print("12")


def freestyle_to_gpencil_frame(scene, lineset, fsstrokes_map):
    """
    Transfer freestyle strokes to new frame
    :param scene:
    :param lineset:
    :param fsstrokes_map:
    :return: GreasePencil(ID) with drawn frame
    """
    # for debugging purposes
    print("freestyle_to_gpencil_frame start")

    fs_lineset_name = "FS {}".format(lineset.name)
    gpencil_data, frame = get_gpencil_frame(scene, fs_lineset_name)

    # TODO: make options with props?

    freestyle_to_gpencil_strokes(fsstrokes_map, frame, lineset)

    # for debugging purposes
    print("freestyle_to_gpencil_frame end")

    return gpencil_data

def get_grease_pencil_material(gpencil_materia_name='init_GP_Material') -> bpy.types.MaterialGPencilStyle:
    # Make new material
    gpencil_material = bpy.data.materials.new(gpencil_materia_name)

    # Make material suitable for grease pencil
    if not gpencil_material.is_grease_pencil:
        bpy.data.materials.create_gpencil_data(gpencil_material)
        # Set color
        gpencil_material.grease_pencil.color = (0, 0, 0, 1)

    # for debugging purposes
    print("get_grease_pencil_material")

    return gpencil_material

def get_object(gpencil_data, gpencil_obj_name='init_GPencil') -> bpy.types.Object:
    """
    Return active grease pencil object or create new one.
    Append material to object.
    :param gpencil_data:
    :param gpencil_obj_name:
    :return:
    """
    # for debugging purposes
    print("get_object start")

    obj = bpy.data.objects.new(gpencil_obj_name, gpencil_data)

    # Assign the material to the grease pencil for drawing
    gpencil_material = get_grease_pencil_material()
    # Append material to GP object
    obj.data.materials.append(gpencil_material)

    # for debugging purposes
    print("get_object end")

    return obj


def freestyle_to_object(scene, lineset, fsstrokes_map):
    """
    Append GreasePencil(ID) data-block to Object(ID).
    Link object to active Collection(ID).
    :param scene:
    :param lineset:
    :param fsstrokes_map:
    :return:
    """
    # for debugging purposes
    print("freestyle_to_object start")

    gpencil_data = freestyle_to_gpencil_frame(scene, lineset, fsstrokes_map)
    obj = get_object(gpencil_data)
    bpy.context.scene.collection.objects.link(obj)

    # for debugging purposes
    print("freestyle_to_object end")

class StrokeCollector(StrokeShader):
    def __init__(self):
        StrokeShader.__init__(self)
        self.viewmap = []

    def shade(self, stroke):
        self.viewmap.append(stroke)

class Callbacks():
    @classmethod
    def poll(cls, scene, linestyle):
# uncomment when options done
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

        fstrokes_map = cls.shader.viewmap
        freestyle_to_object(scene, lineset, fstrokes_map)

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

