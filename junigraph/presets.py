"""Define some basic objects to draw into the SVG."""

import svgwrite
from pygments import lex
from pygments.lexers import YamlLexer
from pygments.token import Token


class Arrow:
    def __init__(
        self,
        drawing,
        position,
        length=40,
        line_thickness=0.9,
        color="black",
        direction="right",
    ):
        """Draw an Arrow.

        Parameters
        ----------
        drawing : svgwrite.Drawing
            Drawing to which to add the Arrow.
        position : tuple
            (x, y) coordinates
        length : int or float
            Length of the Arrow.
        line_thickness : int or float
            Thickness of the lines.
        color : str
            Color of the lines.
        direction : str
            {"right"}. Direction in which the Arrow points.

        """
        if direction != "right":
            raise NotImplementedError(
                "Directions other than right are not implemented yet."
            )

        self.direction = direction
        self.position = position
        self.length = length
        self.color = color
        self.line_thickness = line_thickness
        x, y = position

        # Draw arrow symbol
        arrow_group = drawing.g()
        arrow_group.add(
            drawing.line(
                (x, y),
                (x + self.length, y),
                stroke=self.color,
                stroke_width=line_thickness,
            )
        )
        arrow_group.add(
            drawing.line(
                (x + self.length - 0.3, y),
                (x + self.length - 5, y + 5),
                stroke=self.color,
                stroke_width=self.line_thickness,
            )
        )
        arrow_group.add(
            drawing.line(
                (x + self.length - 0.3, y),
                (x + self.length - 5, y - 5),
                stroke=self.color,
                stroke_width=self.line_thickness,
            )
        )

        drawing.add(arrow_group)


class TextBox:
    def __init__(
        self,
        drawing,
        text,
        position,
        origin="center_left",
        color="mistyrose",
        font_size=9,
        font_size_to_width_ratio=0.65,
        opacity=0.3,
        key_color="darkgreen",
        value_color="navy",
    ):
        """Draw a rectangle with some (YAML) text in it.

        Parameters
        ----------
        drawing : svgwrite.Drawing
            Drawing to which to add the TextBoxes
        text : str
            Text to display.
        position : tuple
            (x, y) coordinates
        origin : str
            {"center_left", "top_left", "bottom_left"}. Where to start drawing
            the box.
        color : str
            Background color of the box.
        font_size : int
            Font size.
        font_size_to_width_ratio : float
            Ratio that determines the width of characters
            depending on the font size.
        opacity : float
            Opacity of the background.
        key_color : str
            Color of (YAML) keys.
        value_color : str
            Color of (YAML) values.

        """
        self.color = color
        self.position = position
        self.text = text
        self.font_size = font_size
        self.opacity = opacity

        self.padding_x, self.padding_y = font_size, font_size * 2

        # examine the properties of the text
        # this needs to be done before determining box coordinates depending
        # on the origin. Therefore we need to loop over the text twice.
        # Once for those properties, then for the writing
        text_list = text.split("\n")
        n_longest_line = 0
        n_lines = len(text_list)
        for line in text_list:
            len_line = len(line)
            if n_longest_line < len_line:
                n_longest_line = len_line

        # fit a rectangle around the text
        self.rect_len_x, self.rect_len_y = (
            n_longest_line * (font_size * font_size_to_width_ratio)
        ), (n_lines * font_size) + self.padding_y

        if origin == "center_left":
            rect_x, rect_y = self.position
            rect_y = rect_y - (self.rect_len_y / 2)
        elif origin == "top_left":
            rect_x, rect_y = self.position
        elif origin == "bottom_left":
            rect_x, rect_y = self.position
            rect_y -= self.rect_len_y

        for on_line, line in enumerate(text_list):
            lexed = lex(line, YamlLexer())  # , SvgFormatter(outencoding=""))

            text = drawing.text(
                "",
                insert=(
                    rect_x + self.padding_x,
                    rect_y + self.padding_y + (on_line * font_size),
                ),
                font_size=f"{font_size}px",
            )

            for kind, content in lexed:
                extra = {}

                if kind == Token.Name.Tag:
                    extra = {"fill": key_color}
                elif kind == Token.Literal.Scalar.Plain:
                    extra = {"fill": value_color}

                tspan = svgwrite.text.TSpan(text=content, **extra)
                text.add(tspan)

            drawing.add(text)

        self.rect_pos_x, self.rect_pos_y = (
            rect_x,
            rect_y,
        )

        self.drawn = drawing.rect(
            insert=(self.rect_pos_x, self.rect_pos_y),
            size=(self.rect_len_x, self.rect_len_y),
            fill=self.color,
            stroke="black",
            fill_opacity=self.opacity,
            rx=10,
            ry=10,
        )
        drawing.add(self.drawn)


class Connector:
    def __init__(self, drawing, textbox_a, textbox_b):
        """Draw a connector between two textboxes.

        Parameters
        ----------
        drawing : svgwrite.drawing
            Drawing to which to add the connectors.
        textbox_a : .presets.TextBox
            Textbox A.
        textbox_b : .presets.TextBox
            TextBox B.

        """
        self.textbox_a = textbox_a
        self.textbox_b = textbox_b

        _connector = drawing.line(
            (
                self.textbox_a.rect_pos_x
                + self.textbox_a.drawn.attribs["width"],
                self.textbox_a.rect_pos_y
                + textbox_a.drawn.attribs["height"] / 2,
            ),
            (
                self.textbox_b.rect_pos_x,
                self.textbox_b.rect_pos_y
                + self.textbox_b.drawn.attribs["height"] / 2,
            ),
            stroke="black",
        )
        drawing.add(_connector)
