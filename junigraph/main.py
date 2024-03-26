"""Script to generate visual representation of junifer pipeline from YAML."""

from argparse import ArgumentParser, ArgumentTypeError
from pathlib import Path

import svgwrite
import yaml

from .io import load_yaml_file
from .presets import Connector, TextBox
from .strfmt import truncate_path


def restricted_float(x):
    """Restrict floats to range between 0 and 1."""
    x = float(x)
    if x < 0.0 or x > 1.0:
        raise ArgumentTypeError("%r not in range [0.0, 1.0]" % (x,))
    return x


def parse_args():
    """Parse the arguments of the script."""
    parser = ArgumentParser(
        description=(
            "Create an SVG file of a visual representation "
            "of a junifer pipeline specification."
        )
    )
    parser.add_argument(
        "yaml",
        help="Path to yaml file with junifer pipeline specification.",
        type=Path,
    )
    parser.add_argument("svg", help="Path to output svg.", type=Path)
    parser.add_argument(
        "-fs", "--fontsize", help="Fontsize for text.", type=int, default=7
    )
    parser.add_argument(
        "-c",
        "--color",
        help="Background color of the text boxes.",
        default="mistyrose",
    )
    parser.add_argument(
        "-o",
        "--opacity",
        help="Opacity of the text boxes. Should be between 0 and 1.",
        default=0.3,
    )
    parser.add_argument(
        "--width",
        help="Width of the canvas. Unit is determined by '-u, --unit' option.",
        default=700,
        type=int,
    )
    parser.add_argument(
        "--height",
        help="Height of the canvas. Unit is determined by '-u, --unit' option.",
        default=354,
        type=int,
    )
    parser.add_argument(
        "-u",
        "--unit",
        help=(
            "Unit of width and height parameters."
            " For simplicity it is limited to 'mm' and px."
        ),
        type=str,
        choices=["mm", "px"],
        default="px",
    )
    parser.add_argument(
        "-hs",
        "--horizontal_space",
        help=(
            "Proportion of the canvas width that should be dedicated to"
            " creating space between boxes (float between 0 and 1)."
        ),
        default=0.07,
        type=restricted_float,
    )
    parser.add_argument(
        "-spml",
        "--storage_path_max_length",
        help="Truncate the storage path to a maximum length.",
        type=int,
        default=None,
    )
    parser.add_argument(
        "-mp",
        "--marker_padding",
        help="Vertical Spacing between markers (px).",
        type=int,
        default=5,
    )
    parser.add_argument(
        "-kc",
        "--key-color",
        help=(
            "Color of keys in YAML key: value pairs. "
            "Must be an SVG color string."
        ),
        default="darkgreen",
    )
    parser.add_argument(
        "-vc",
        "--value-color",
        help=(
            "Color of values in YAML key: value pairs. "
            "Must be an SVG color string."
        ),
        default="navy",
    )
    return parser.parse_args()


def create_marker_boxes(
    drawing,
    markers,
    script_args,
    x,
    starting_y,
    reference_text_box_for_markers,
):
    """Draw TextBox object for each marker.

    Parameters
    ----------
    drawing : svgwrite.Drawing
        Drawing to which to add the TextBoxes.
    markers : dict
        Dict containing the marker information.
    script_args :
        Arguments to this script.
    x : int or float
        x coordinate of the marker TextBoxes
    starting_y : int or float
        y coordinate at which to start drawing TextBoxes.
    reference_text_box_for_markers : .presets.TextBox
        TextBox that comes immediately before markers in the pipeline.

    """
    length_longest_marker_box = 0

    marker_boxes = []
    put_next = "below"

    if len(markers) % 2 != 0:
        origin = "center_left"
        current_marker_y = starting_y
    else:
        origin = "bottom_left"
        current_marker_y = starting_y - (script_args.marker_padding / 2)

    for i, marker in enumerate(markers):
        # format the marker text
        marker_text = yaml.safe_dump(marker, width=1, sort_keys=False)

        # create a marker text box
        text_box_marker = TextBox(
            drawing,
            marker_text,
            position=(x, current_marker_y),
            origin=origin,
            font_size=script_args.fontsize,
            color=script_args.color,
            opacity=script_args.opacity,
            key_color=script_args.key_color,
            value_color=script_args.value_color,
        )

        # connect either datagrabber or preprocessing box to current marker
        _ = Connector(drawing, reference_text_box_for_markers, text_box_marker)

        # update the origin of the next text box
        if put_next == "below":
            origin = "top_left"
        elif put_next == "above":
            origin = "bottom_left"

        # update the y coordinate depending whether the next box is going above
        # or below, also update the current lower and upper ends
        if put_next == "below":
            if i == 0:
                lower_end = (
                    text_box_marker.rect_pos_y + text_box_marker.rect_len_y
                )

            upper_end = text_box_marker.rect_pos_y

            current_marker_y = lower_end + script_args.marker_padding
            put_next = "above"

        elif put_next == "above":
            lower_end = text_box_marker.rect_pos_y + text_box_marker.rect_len_y

            current_marker_y = upper_end - script_args.marker_padding
            put_next = "below"

        marker_boxes.append(text_box_marker)
        if text_box_marker.rect_len_x > length_longest_marker_box:
            length_longest_marker_box = text_box_marker.rect_len_x

    return marker_boxes, length_longest_marker_box


def main():
    """Run the main program."""
    args = parse_args()
    pipeline_spec = load_yaml_file(args.yaml)

    markers = pipeline_spec["markers"]

    if args.storage_path_max_length is not None:
        pipeline_spec["storage"]["uri"] = truncate_path(
            pipeline_spec["storage"]["uri"], args.storage_path_max_length
        )

    # initialise all the global text objects (i.e. all except markers)

    datagrabber_text = yaml.safe_dump(
        pipeline_spec["datagrabber"], width=1, sort_keys=False
    )
    preprocessing_text = yaml.safe_dump(
        pipeline_spec.get("preprocess", "no_preprocess"),
        width=1,
        sort_keys=False,
    )
    storage_text = yaml.safe_dump(
        pipeline_spec["storage"], width=1, sort_keys=False
    )

    # set up some starting default parameters
    # these can be improved in the future or be made more configurable
    # but for now i think they constitute a reasonable default
    px_to_other_unit = {
        "mm": 3.543307,
        "px": 1,
    }
    unit = px_to_other_unit[args.unit]

    # center the first text box on the canvas
    initial_x, initial_y = 10, (args.height * unit) / 2

    # distances between boxes are determined using this simple heuristic:
    # at most there will be 4 columns of boxes, they should take roughly take
    # 80% of the width, whereas distances between take should take altogether
    # take 20% of the width, there will be at most 3 distances
    # so take 20% of the width and divide it by three
    # again, its just a heuristic, there may be a better way
    text_box_distance_total = (args.width * unit) * args.horizontal_space
    text_box_distance_preprocess = text_box_distance_total * 0.3
    text_box_distance_markers = (
        text_box_distance_total - text_box_distance_preprocess
    )

    # initialise the drawing
    dwg = svgwrite.Drawing(
        filename=args.svg,
        size=(f"{args.width}{args.unit}", f"{args.height}{args.unit}"),
        profile="tiny",
        debug=False,
    )

    # create a datagrabber textbox
    text_box_datagrabber = TextBox(
        dwg,
        datagrabber_text,
        position=(
            initial_x,
            initial_y,
        ),
        font_size=args.fontsize,
        color=args.color,
        opacity=args.opacity,
        key_color=args.key_color,
        value_color=args.value_color,
    )

    if "no_preprocess" not in preprocessing_text:
        # create a preprocessing textbox
        text_x_preproc = (
            initial_x
            + text_box_datagrabber.rect_len_x
            + text_box_distance_preprocess
        )
        text_box_preprocessing = TextBox(
            dwg,
            preprocessing_text,
            position=(
                text_x_preproc,
                initial_y,
            ),
            font_size=args.fontsize,
            color=args.color,
            opacity=args.opacity,
            key_color=args.key_color,
            value_color=args.value_color,
        )
        _ = Connector(dwg, text_box_datagrabber, text_box_preprocessing)

        current_marker_x = (
            text_box_preprocessing.rect_pos_x
            + text_box_preprocessing.rect_len_x
            + text_box_distance_markers
        )
        reference_text_box_for_markers = text_box_preprocessing
    else:
        reference_text_box_for_markers = text_box_datagrabber
        current_marker_x = (
            text_box_datagrabber.rect_pos_x
            + text_box_datagrabber.rect_len_x
            + text_box_distance_markers
        )

    # create the marker text boxes
    marker_boxes, length_longest_marker_box = create_marker_boxes(
        dwg,
        markers,
        args,
        current_marker_x,
        initial_y,
        reference_text_box_for_markers,
    )

    # create a storage text box
    text_box_storage = TextBox(
        dwg,
        storage_text,
        position=(
            marker_boxes[-1].rect_pos_x
            + length_longest_marker_box
            + text_box_distance_markers,
            initial_y,
        ),
        font_size=args.fontsize,
        font_size_to_width_ratio=0.5,  # tends to be smaller due to slashes
        color=args.color,
        opacity=args.opacity,
        key_color=args.key_color,
        value_color=args.value_color,
    )

    for marker_box in marker_boxes:
        marker_box.drawn.attribs["width"] = length_longest_marker_box

        _ = Connector(dwg, marker_box, text_box_storage)

    dwg.save()
