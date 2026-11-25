"""Shared source PBR parameters and metre-based UV mapping for Blender."""
import bpy
import json
import pathlib
from functools import lru_cache

ROOT = pathlib.Path(__file__).resolve().parents[1]
MAPS = ROOT / "assets/materials"
SURFACES = json.loads((ROOT / "design/material-library.json").read_text())
BY_KEY = {key: (name, spec) for name, spec in SURFACES.items() for key in spec["keys"]}


@lru_cache
def image(name, channel):
    result = bpy.data.images.load(str(MAPS / f"{name}-{channel}.jpg"), check_existing=True)
    result.colorspace_settings.name = "sRGB" if channel == "color" else "Non-Color"
    return result


def apply_shader(material, key, rgb):
    name, spec = BY_KEY[key]
    tree = material.node_tree
    bsdf = tree.nodes.get("Principled BSDF")

    def tex(channel):
        n = tree.nodes.new("ShaderNodeTexImage")
        n.image = image(name, channel)
        n.label = f"{name} {channel}"
        return n

    colour = tree.nodes.new("ShaderNodeMixRGB")
    colour.blend_type = "MULTIPLY"
    colour.inputs[0].default_value = 1
    colour.inputs[2].default_value = (*rgb(spec["tint"].lstrip("#")), 1)
    tree.links.new(tex("color").outputs["Color"], colour.inputs[1])
    tree.links.new(colour.outputs[0], bsdf.inputs["Base Color"])
    rough = tree.nodes.new("ShaderNodeMapRange")
    rough.inputs["To Min"].default_value, rough.inputs["To Max"].default_value = spec["roughness"]
    tree.links.new(tex("roughness").outputs["Color"], rough.inputs["Value"])
    tree.links.new(rough.outputs[0], bsdf.inputs["Roughness"])
    normal = tree.nodes.new("ShaderNodeNormalMap")
    normal.inputs["Strength"].default_value = spec["normal"]
    tree.links.new(tex("normal").outputs["Color"], normal.inputs["Color"])
    tree.links.new(normal.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Coat Weight"].default_value = spec["coat"]
    bsdf.inputs["Coat Roughness"].default_value = .21


def map_uv(obj, key):
    """Project dominant faces in model units; keep walnut grain lengthwise."""
    name, spec = BY_KEY[key]
    du, dv = spec["metres"]
    mesh = obj.data
    layer = mesh.uv_layers.active or mesh.uv_layers.new()
    offset = ((obj.location.x * .53 + obj.location.y * .19) % 1) if name != "stone" else 0
    for face in mesh.polygons:
        axis = max(range(3), key=lambda i: abs(face.normal[i]))
        for idx in face.loop_indices:
            p = mesh.vertices[mesh.loops[idx].vertex_index].co
            if axis == 2:
                a, b = (p.y, p.x) if name == "walnut" else (p.x,p.y)
            else:
                a, b = (p[1-axis], p.z)
            layer.data[idx].uv = (a / du + offset, b / dv)


def strip_for_glb():
    """Browser streams shared maps separately so GLB geometry stays reusable."""
    for material in bpy.data.materials:
        if material.name not in BY_KEY or not material.node_tree:
            continue
        shader = material.node_tree.nodes.get("Principled BSDF")
        for socket in ("Base Color", "Roughness", "Normal"):
            for link in list(shader.inputs[socket].links):
                material.node_tree.links.remove(link)
