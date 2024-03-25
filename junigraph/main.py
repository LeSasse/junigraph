import yaml
from argparse import ArgumentParser
from pathlib import Path
from pprint import pformat
import svgwrite
from .presets import TextBox, Connector
from .io import load_yaml_file


def parse_args():
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
        "-f",
        "--format",
        help="Format to stringify the yaml objects.",
        choices=["yaml", "json"],
        default="yaml",
    )
    parser.add_argument(
        "-fs", "--fontsize", help="Fontsize for text.", type=int, default=10
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
    return parser.parse_args()


def main():
    args = parse_args()
    pipeline_spec = load_yaml_file(args.yaml)

    markers = pipeline_spec["markers"]
    # initialise all the global text objects (i.e. all except markers)
    if args.format == "json":
        datagrabber_text = pformat(pipeline_spec["datagrabber"], width=1)
        preprocessing_text = pformat(
            pipeline_spec.get("preprocess", "no_preprocess"), width=1
        )
        storage_text = pformat(pipeline_spec["storage"], width=1)
    elif args.format == "yaml":
        datagrabber_text = yaml.dump(pipeline_spec["datagrabber"], width=1)
        preprocessing_text = yaml.dump(
            pipeline_spec.get("preprocess", "no_preprocess"), width=1
        )
        storage_text = yaml.dump(pipeline_spec["storage"], width=1)

    # set up some starting default parameters
    # these can be improved in the future or be made more configurable
    # but for now i think they constitute a reasonable default
    initial_x, initial_y = 50, 1000 / 2
    upper_padding = 50

    initial_size_x, initial_size_y = 800, 1000
    padding_arrow = 10
    arrow_length = 40
    marker_padding = 10

    # initialise the drawing
    dwg = svgwrite.Drawing(
        filename=args.svg,
        size=(f"{initial_size_x}px", f"{initial_size_y}px"),
        profile="tiny",
        debug=True,
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
    )

    if "no_preprocess" not in preprocessing_text:
        # create a preprocessing textbox
        text_x_preproc = (
            initial_x
            + text_box_datagrabber.rect_len_x
            + (2 * padding_arrow)
            + arrow_length
        )
        text_box_preprocessing = TextBox(
            dwg,
            preprocessing_text,
            position=(
                text_x_preproc,
                initial_y - text_box_datagrabber.rect_len_y / 2,
            ),
            font_size=args.fontsize,
            color=args.color,
            opacity=args.opacity,
        )
        _ = Connector(dwg, text_box_datagrabber, text_box_preprocessing)

        current_marker_x = (
            text_box_preprocessing.rect_pos_x
            + text_box_preprocessing.rect_len_x
            + 1.5 * arrow_length
            + (3 * padding_arrow)
        )
        reference_text_box_for_markers = text_box_preprocessing
    else:
        reference_text_box_for_markers = text_box_datagrabber
        current_marker_x = (
            text_box_datagrabber.rect_pos_x
            + text_box_datagrabber.rect_len_x
            + 1.5 * arrow_length
            + (3 * padding_arrow)
        )

    # create the marker text boxes
    current_marker_y = upper_padding
    length_longest_marker_box = 0

    marker_boxes = []
    full_document_size_y = 2 * upper_padding
    for i, marker in enumerate(markers):
        # format the marker text
        if args.format == "yaml":
            marker_text = yaml.dump(marker, width=1)
        elif args.format == "json":
            marker_text = pformat(marker, width=1)

        # create a marker text box
        text_box_marker = TextBox(
            dwg,
            marker_text,
            position=(current_marker_x, current_marker_y),
            font_size=args.fontsize,
            color=args.color,
            opacity=args.opacity,
        )
        # connect either datagrabber or preprocessing box to current marker
        _ = Connector(dwg, reference_text_box_for_markers, text_box_marker)

        # update the position for the next marker in line
        current_marker_y += (
            marker_padding
            # + text_box_marker.rect_pos_y
            + text_box_marker.rect_len_y
        )
        # update the full document height to respect the markers
        full_document_size_y += marker_padding + text_box_marker.rect_len_y
        marker_boxes.append(text_box_marker)
        if text_box_marker.rect_len_x > length_longest_marker_box:
            length_longest_marker_box = text_box_marker.rect_len_x

    # create a storage text box
    text_box_storage = TextBox(
        dwg,
        storage_text,
        position=(
            text_box_marker.rect_pos_x
            + length_longest_marker_box
            + 1.5 * arrow_length
            + 3 * padding_arrow,
            initial_y,
        ),
        font_size=args.fontsize,
        font_size_to_width_ratio=0.5,  # tends to be smaller due to slashes
        color=args.color,
        opacity=args.opacity,
    )

    for marker_box in marker_boxes:
        marker_box.drawn.attribs["width"] = length_longest_marker_box

        _ = Connector(dwg, marker_box, text_box_storage)

    if "no_preprocess" not in preprocessing_text:
        full_document_size_x = (
            initial_x * 2
            + text_box_datagrabber.rect_len_x
            + text_box_preprocessing.rect_len_x
            + length_longest_marker_box
            + (6 * arrow_length)
            + (10 * padding_arrow)
            + text_box_storage.rect_len_x
        )
    else:
        full_document_size_x = (
            initial_x * 2
            + text_box_datagrabber.rect_len_x
            + length_longest_marker_box
            + (6 * arrow_length)
            + (10 * padding_arrow)
            + text_box_storage.rect_len_x
        )

    dwg.attribs["width"] = full_document_size_x
    dwg.attribs["height"] = full_document_size_y
    dwg.save()
