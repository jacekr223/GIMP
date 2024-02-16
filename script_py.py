#!/usr/bin/env python
from gimpfu import *
import math
import random

def scale_layer_to_selection(image, layer, x1, y1, x2, y2):
    new_width = x2 - x1
    new_height = y2 - y1
    pdb.gimp_layer_scale(layer, new_width, new_height, True)

def inpainting(image, layer, weight_multiplier, randomize_directions):
    width, height = image.width, image.height
    def in_bounds(x, y):
        return 0 <= x < width and 0 <= y < height
    def weight_func(dist):
        return weight_multiplier / (dist + 1e-5)

    non_empty, x1, y1, x2, y2 = pdb.gimp_selection_bounds(image)
    while non_empty:
        for x in range(int(x1), int(x2)):
            for y in range(int(y1), int(y2)):
                if pdb.gimp_selection_value(image, x, y):
                    surrounding_colors = []
                    weights = []
                    directions = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if dx != 0 or dy != 0]
                    if not randomize_directions:
                        directions.sort(key=lambda d: -weight_func(math.sqrt(d[0]**2 + d[1]**2)))
                    for dx, dy in directions:
                        nx, ny = x + dx, y + dy
                        if in_bounds(nx, ny) and not pdb.gimp_selection_value(image, nx, ny):
                            surrounding_colors.append(layer.get_pixel(nx, ny))
                            weights.append(weight_func(math.sqrt(dx*dx + dy*dy)))
                    if surrounding_colors:
                        total_weight = sum(weights)
                        avg_color = [sum(w * c for w, c in zip(weights, channel)) / total_weight for channel in zip(*surrounding_colors)]
                        layer.set_pixel(x, y, tuple(map(int, avg_color)))
        layer.update(0, 0, width, height)
        pdb.gimp_selection_shrink(image, 1)
        non_empty, x1, y1, x2, y2 = pdb.gimp_selection_bounds(image)

def blurring(image, layer, weight_multiplier, randomize_directions, blur_strength):
    width, height = image.width, image.height
    
    def in_bounds(x, y):
        return 0 <= x < width and 0 <= y < height
    
    def weight_func(dist):
        return weight_multiplier / ((dist / blur_strength) + 1e-5)
    
    non_empty, x1, y1, x2, y2 = pdb.gimp_selection_bounds(image)
    while non_empty:
        for x in range(int(x1), int(x2)):
            for y in range(int(y1), int(y2)):
                if pdb.gimp_selection_value(image, x, y):
                    surrounding_colors = []
                    weights = []
                    for dx in range(-1, 2):
                        for dy in range(-1, 2):
                            nx, ny = x + dx, y + dy
                            if in_bounds(nx, ny):
                                surrounding_colors.append(layer.get_pixel(nx, ny))
                                weights.append(weight_func(math.sqrt(dx*dx + dy*dy)))

                    total_weight = sum(weights)
                    avg_color = [sum(w * c for w, c in zip(weights, channel)) / total_weight for channel in zip(*surrounding_colors)]
                    layer.set_pixel(x, y, tuple(map(int, avg_color)))

        layer.update(0, 0, width, height)
        pdb.gimp_selection_shrink(image, 1)
        non_empty, x1, y1, x2, y2 = pdb.gimp_selection_bounds(image)


def clone_texture(image, layer, weight_multiplier, randomize_directions, texture_image, texture_file_path):
    try:
        if texture_file_path:
            texture_image = pdb.gimp_file_load(texture_file_path, texture_file_path)
        
        # Check if the image has layers
        if not texture_image.layers:
            pdb.gimp_message("The texture image has no layers!")
            return

        texture_layer = texture_image.layers[0]

        non_empty, x1, y1, x2, y2 = pdb.gimp_selection_bounds(image)
        if non_empty:
            scale_layer_to_selection(texture_image, texture_layer, x1, y1, x2, y2)
            pdb.gimp_edit_copy(texture_layer)
            floating_sel = pdb.gimp_edit_paste(layer, False)
            pdb.gimp_floating_sel_anchor(floating_sel)
    except Exception as e:
        pdb.gimp_message("Error in clone_texture: " + str(e))

register(
    "python_fu_fill",
    "Fill From",
    "Fill the selected area",
    "User",
    "User",
    "2023",
    "Fill From",
    "*",
    [
        (PF_IMAGE, "image", "Input image", None),
        (PF_DRAWABLE, "layer", "Input drawable", None),
        (PF_SLIDER, "weight_multiplier", "Direction Weight Multiplier", 1.0, (0.1, 10.0, 0.1)),
        (PF_TOGGLE, "randomize_directions", "Randomize Directions", True),
        (PF_OPTION, "processing_mode", "Processing Mode", 0, ["Inpainting", "Blurring", "Clone Texture"]),
        (PF_SLIDER, "blur_strength", "Blur Strength", 1.0, (0.1, 10.0, 0.1)),
        (PF_IMAGE, "texture_image", "Texture Image", None),
        (PF_FILE, "texture_file_path", "Texture File Path", ""),
    ],
    [],
    lambda image, layer, weight_multiplier, randomize_directions, processing_mode, blur_strength, texture_image, texture_file_path: (
        inpainting(image, layer, weight_multiplier, randomize_directions) if processing_mode == 0 else
        blurring(image, layer, weight_multiplier, randomize_directions, blur_strength) if processing_mode == 1 else
        clone_texture(image, layer, weight_multiplier, randomize_directions, texture_image, texture_file_path) if processing_mode == 2 else
        None
    ),
    menu="<Image>/Filters/Misc"
)

main()
