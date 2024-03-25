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
        color="mistyrose",
        font_size=9,
        font_size_to_width_ratio=0.65,
        opacity=0.3,
    ):
        self.color = color
        self.position = position
        self.text = text
        self.font_size = font_size
        self.opacity = opacity

        self.padding_x, self.padding_y = 10, 20
        text_x, text_y = self.position

        # write the text
        text_list = text.split("\n")
        n_longest_line = 0
        for on_line, line in enumerate(text_list):
            text_drawn = drawing.text(
                line,
                insert=(text_x, text_y + (on_line * font_size)),
                font_size=f"{font_size}px",
            )
            drawing.add(text_drawn)
            len_line = len(line)
            if n_longest_line < len_line:
                n_longest_line = len_line

        n_lines = on_line + 2

        # fit a rectangle around the text
        self.rect_len_x, self.rect_len_y = (
            n_longest_line * (font_size * font_size_to_width_ratio)
        ), (n_lines * font_size) + self.padding_y / 2

        self.rect_pos_x, self.rect_pos_y = (
            text_x - self.padding_x,
            text_y - self.padding_y,
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
