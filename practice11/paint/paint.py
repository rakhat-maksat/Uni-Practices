import pygame
import math

#  CONSTANTS
SCREEN_W    = 900
SCREEN_H    = 650
TOOLBAR_W   = 130     # width of the left toolbar panel
CANVAS_X    = TOOLBAR_W
CANVAS_Y    = 0
CANVAS_W    = SCREEN_W - TOOLBAR_W
CANVAS_H    = SCREEN_H

# --- Colour Palette ---
PALETTE = [
    (0,   0,   0),      # Black
    (255, 255, 255),    # White
    (200, 0,   0),      # Red
    (0,   180, 0),      # Green
    (0,   0,   220),    # Blue
    (255, 165, 0),      # Orange
    (255, 255, 0),      # Yellow
    (128, 0,   128),    # Purple
    (0,   200, 200),    # Cyan
    (255, 20,  147),    # Pink
    (139, 69,  19),     # Brown
    (128, 128, 128),    # Gray
]

# Tool IDs – each string uniquely identifies one drawing mode
TOOL_PEN       = "pen"
TOOL_ERASER    = "eraser"
TOOL_RECTANGLE = "rect"
TOOL_SQUARE    = "square"
TOOL_CIRCLE    = "circle"
TOOL_RIGHT_TRI = "right_tri"
TOOL_EQ_TRI    = "eq_tri"
TOOL_RHOMBUS   = "rhombus"

# UI colours
TOOLBAR_BG      = (45,  45,  45)   # dark background for the toolbar panel
TOOLBAR_BORDER  = (80,  80,  80)   # subtle separator lines
SELECTED_BORDER = (255, 220, 0)    # golden highlight for selected button / colour
BTN_NORMAL      = (70,  70,  70)   # default button background
BTN_HOVER       = (100, 100, 100)  # button background when the mouse hovers over it
WHITE           = (255, 255, 255)
BLACK           = (0,   0,   0)


#  HELPER FUNCTIONS

def clamp(val, lo, hi):
    """Clamp val to the range [lo, hi]."""
    return max(lo, min(hi, val))


def on_canvas(pos):
    """Return True if the screen pixel position sits inside the drawable canvas area."""
    x, y = pos
    return CANVAS_X <= x < CANVAS_X + CANVAS_W and 0 <= y < CANVAS_H


def canvas_pos(pos):
    """Convert a screen-space (x, y) position to canvas-relative coordinates."""
    return (pos[0] - CANVAS_X, pos[1] - CANVAS_Y)


#  BUTTON CLASS  – simple clickable rectangle with a text label

class Button:
    def __init__(self, rect, label, tool_id, font):
        # rect     – (x, y, w, h) defining the button's position on screen
        # label    – text drawn in the centre of the button
        # tool_id  – the TOOL_* constant this button activates (or None for utility buttons)
        # font     – pygame.Font used to render the label
        self.rect    = pygame.Rect(rect)
        self.label   = label
        self.tool_id = tool_id
        self.font    = font

    def draw(self, surface, selected, mouse_pos):
        """Render the button; highlight it if it is the currently selected tool."""
        hovered  = self.rect.collidepoint(mouse_pos)
        bg_color = BTN_HOVER if hovered else BTN_NORMAL
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=5)

        # Draw a golden border when this tool is active, grey otherwise
        border_c = SELECTED_BORDER if selected else TOOLBAR_BORDER
        pygame.draw.rect(surface, border_c, self.rect, 2, border_radius=5)

        # Centre the label text inside the button
        text_surf = self.font.render(self.label, True, WHITE)
        tx = self.rect.centerx - text_surf.get_width() // 2
        ty = self.rect.centery - text_surf.get_height() // 2
        surface.blit(text_surf, (tx, ty))

    def is_clicked(self, pos):
        """Return True if the given screen position lands inside this button."""
        return self.rect.collidepoint(pos)


#  PYGAME SETUP

pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Paint")
clock   = pygame.time.Clock()
font_ui = pygame.font.SysFont("Consolas", 13, bold=True)

# The canvas is a separate Surface we draw onto, then blit to the screen each frame.
# This lets us overlay drag previews without permanently altering the drawing.
canvas = pygame.Surface((CANVAS_W, CANVAS_H))
canvas.fill(WHITE)   # start with a blank white canvas


#  TOOLBAR LAYOUT

SWATCH_SIZE     = 26   # pixel width/height of each colour swatch
SWATCH_PAD      = 6    # gap between swatches
SWATCHES_PER_ROW = 4


def swatch_rect(index):
    """Return a pygame.Rect for the colour swatch at the given palette index."""
    col = index % SWATCHES_PER_ROW
    row = index // SWATCHES_PER_ROW
    x   = 6 + col * (SWATCH_SIZE + SWATCH_PAD)
    # Push swatches down far enough to fit all tool buttons + size controls + gap
    y   = 410 + row * (SWATCH_SIZE + SWATCH_PAD)
    return pygame.Rect(x, y, SWATCH_SIZE, SWATCH_SIZE)


# Tool buttons – listed in display order from top to bottom.
# Each button is 110 px wide and 34 px tall with a 42 px pitch.
buttons = [
    Button((10,  10,  TOOLBAR_W - 20, 34), "Pen",      TOOL_PEN,       font_ui),
    Button((10,  52,  TOOLBAR_W - 20, 34), "Eraser",   TOOL_ERASER,    font_ui),
    Button((10,  94,  TOOLBAR_W - 20, 34), "Rect",     TOOL_RECTANGLE, font_ui),
    Button((10, 136,  TOOLBAR_W - 20, 34), "Square",   TOOL_SQUARE,    font_ui),
    Button((10, 178,  TOOLBAR_W - 20, 34), "Circle",   TOOL_CIRCLE,    font_ui),
    Button((10, 220,  TOOLBAR_W - 20, 34), "R.Tri",    TOOL_RIGHT_TRI, font_ui),
    Button((10, 262,  TOOLBAR_W - 20, 34), "Eq.Tri",   TOOL_EQ_TRI,    font_ui),
    Button((10, 304,  TOOLBAR_W - 20, 34), "Rhombus",  TOOL_RHOMBUS,   font_ui),
]

# Brush-size controls sit below the tool buttons
btn_size_minus = Button((10,  356, 50, 28), "  -", None, font_ui)
btn_size_plus  = Button((70,  356, 50, 28), "  +", None, font_ui)


#  GAME STATE  (mutable globals changed by the event loop)

current_tool  = TOOL_PEN
current_color = BLACK
brush_radius  = 8      # radius for pen strokes and eraser

# Shape-drag state: set when the user presses the mouse button and
# cleared when they release it.
drag_start = None   # canvas-relative point where the drag began
dragging   = False  # True while the left mouse button is held for a shape tool

# Remembers the previous mouse position so freehand lines stay smooth
prev_pos = None


#  DRAWING HELPERS

def draw_line_between(surface, p1, p2, color, radius):
    """
    Draw a smooth thick stroke between two canvas points.
    Achieved by placing filled circles at each integer step along the segment,
    which avoids visible gaps when the mouse moves quickly.
    """
    dx = p1[0] - p2[0]
    dy = p1[1] - p2[1]
    steps = max(abs(dx), abs(dy), 1)   # at least one iteration
    for i in range(steps):
        t = i / steps
        x = int((1 - t) * p1[0] + t * p2[0])
        y = int((1 - t) * p1[1] + t * p2[1])
        pygame.draw.circle(surface, color, (x, y), radius)


def _rect_from_drag(start, end):
    """Return a pygame.Rect that spans from start to end regardless of drag direction."""
    return pygame.Rect(
        min(start[0], end[0]),
        min(start[1], end[1]),
        abs(end[0] - start[0]),
        abs(end[1] - start[1]),
    )


def _square_end(start, end):
    """
    Given a drag start and current end point, return a new end point that
    forces the bounding box to be a square (equal width and height).
    The side length is the smaller of dx and dy so the square fits inside
    the bounding box the user has drawn.
    """
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    side = min(abs(dx), abs(dy))           # use the shorter dimension
    # Preserve the sign of the drag direction
    sx = 1 if dx >= 0 else -1
    sy = 1 if dy >= 0 else -1
    return (start[0] + sx * side, start[1] + sy * side)


def _right_tri_points(start, end):
    """
    Return the three vertices of a right-angle triangle.
    • The right angle is at start.
    • The two legs are axis-aligned (one horizontal, one vertical).
    Layout:
        start ──────── (end[0], start[1])
          |           /
          |         /
        (start[0], end[1])
    """
    ax, ay = start
    bx, by = end
    return [(ax, ay), (bx, ay), (ax, by)]


def _eq_tri_points(start, end):
    """
    Return the three vertices of an equilateral triangle.
    The base is the horizontal segment from start to (end[0], start[1]).
    The apex is centred above (or below) the base at height = base * √3/2.
    The vertical direction matches the drag direction (up if end.y < start.y).
    """
    ax, ay = start
    bx, by = end
    base   = bx - ax                              # signed base length (can be negative)
    height = abs(base) * math.sqrt(3) / 2        # always positive
    # Place the apex on the same side as the drag direction
    direction = -1 if by < ay else 1
    apex_x = ax + base // 2
    apex_y = int(ay + direction * height)
    return [(ax, ay), (bx, ay), (apex_x, apex_y)]


def _rhombus_points(start, end):
    """
    Return the four vertices of a rhombus whose bounding box spans start→end.
    The four points are the midpoints of each side of that bounding box:
        top, right, bottom, left
    """
    x0, y0 = min(start[0], end[0]), min(start[1], end[1])
    x1, y1 = max(start[0], end[0]), max(start[1], end[1])
    mx, my = (x0 + x1) // 2, (y0 + y1) // 2   # centre of the bounding box
    return [(mx, y0), (x1, my), (mx, y1), (x0, my)]


def draw_ghost_shape(surface, tool, start, end, color, radius):
    """
    Draw a temporary outline preview of the shape being dragged.
    This is rendered onto a copy of the canvas each frame and is
    never written to the permanent canvas surface.
    """
    if tool == TOOL_RECTANGLE:
        pygame.draw.rect(surface, color, _rect_from_drag(start, end), 2)

    elif tool == TOOL_SQUARE:
        sq_end = _square_end(start, end)
        pygame.draw.rect(surface, color, _rect_from_drag(start, sq_end), 2)

    elif tool == TOOL_CIRCLE:
        cx = (start[0] + end[0]) // 2
        cy = (start[1] + end[1]) // 2
        r  = int(math.hypot(end[0] - start[0], end[1] - start[1]) / 2)
        if r > 0:
            pygame.draw.circle(surface, color, (cx, cy), r, 2)

    elif tool == TOOL_RIGHT_TRI:
        pts = _right_tri_points(start, end)
        pygame.draw.polygon(surface, color, pts, 2)

    elif tool == TOOL_EQ_TRI:
        pts = _eq_tri_points(start, end)
        pygame.draw.polygon(surface, color, pts, 2)

    elif tool == TOOL_RHOMBUS:
        pts = _rhombus_points(start, end)
        pygame.draw.polygon(surface, color, pts, 2)


def commit_shape(canvas_surf, tool, start, end, color, radius):
    """
    Permanently draw the finished shape onto the canvas surface.
    Called once when the user releases the mouse button.
    """
    if tool == TOOL_RECTANGLE:
        pygame.draw.rect(canvas_surf, color, _rect_from_drag(start, end), 2)

    elif tool == TOOL_SQUARE:
        sq_end = _square_end(start, end)
        pygame.draw.rect(canvas_surf, color, _rect_from_drag(start, sq_end), 2)

    elif tool == TOOL_CIRCLE:
        cx = (start[0] + end[0]) // 2
        cy = (start[1] + end[1]) // 2
        r  = int(math.hypot(end[0] - start[0], end[1] - start[1]) / 2)
        if r > 0:
            pygame.draw.circle(canvas_surf, color, (cx, cy), r, 2)

    elif tool == TOOL_RIGHT_TRI:
        pts = _right_tri_points(start, end)
        pygame.draw.polygon(canvas_surf, color, pts, 2)

    elif tool == TOOL_EQ_TRI:
        pts = _eq_tri_points(start, end)
        pygame.draw.polygon(canvas_surf, color, pts, 2)

    elif tool == TOOL_RHOMBUS:
        pts = _rhombus_points(start, end)
        pygame.draw.polygon(canvas_surf, color, pts, 2)


#  TOOLBAR DRAWING

def draw_toolbar(surface, mouse_pos):
    """Render the full left-side toolbar: buttons, size controls, palette, active colour."""
    # Solid dark background for the toolbar panel
    pygame.draw.rect(surface, TOOLBAR_BG, (0, 0, TOOLBAR_W, SCREEN_H))
    # Right-edge separator line
    pygame.draw.line(surface, TOOLBAR_BORDER, (TOOLBAR_W, 0), (TOOLBAR_W, SCREEN_H), 2)

    # Draw each tool button; pass whether it is the active tool for highlight logic
    for btn in buttons:
        btn.draw(surface, btn.tool_id == current_tool, mouse_pos)

    # Brush-size row: label + minus/plus buttons
    size_label = font_ui.render(f"Size: {brush_radius}", True, WHITE)
    surface.blit(size_label, (10, 340))   # 14 px above the buttons
    btn_size_minus.draw(surface, False, mouse_pos)
    btn_size_plus.draw(surface,  False, mouse_pos)

    # "Colors:" heading above the swatch grid
    col_heading = font_ui.render("Colors:", True, WHITE)
    surface.blit(col_heading, (10, 394))

    # Colour swatches – one per palette entry
    for i, color in enumerate(PALETTE):
        rect = swatch_rect(i)
        pygame.draw.rect(surface, color, rect, border_radius=4)
        # Golden border for the active colour; subtle grey for the others
        border_c = SELECTED_BORDER if color == current_color else TOOLBAR_BORDER
        border_w = 3 if color == current_color else 1
        pygame.draw.rect(surface, border_c, rect, border_w, border_radius=4)

    # Active-colour preview block at the very bottom of the toolbar
    current_col_y = SCREEN_H - 70
    label = font_ui.render("Active:", True, WHITE)
    surface.blit(label, (10, current_col_y))
    pygame.draw.rect(surface, current_color,   (10, current_col_y + 20, TOOLBAR_W - 20, 36), border_radius=5)
    pygame.draw.rect(surface, SELECTED_BORDER, (10, current_col_y + 20, TOOLBAR_W - 20, 36), 2, border_radius=5)


#  MAIN LOOP

def main():
    global current_tool, current_color, brush_radius
    global drag_start, dragging, prev_pos

    running = True
    while running:
        mouse_pos       = pygame.mouse.get_pos()
        mouse_on_canvas = on_canvas(mouse_pos)

        # EVENT HANDLING
        for event in pygame.event.get():

            # ── Quit ────────────────────────────────────────────
            if event.type == pygame.QUIT:
                running = False

            # ── Keyboard shortcuts ──────────────────────────────
            if event.type == pygame.KEYDOWN:
                pressed = pygame.key.get_pressed()
                # Ctrl+W or Escape → exit
                if event.key == pygame.K_w and (pressed[pygame.K_LCTRL] or pressed[pygame.K_RCTRL]):
                    running = False
                if event.key == pygame.K_ESCAPE:
                    running = False
                # C → clear canvas to white
                if event.key == pygame.K_c:
                    canvas.fill(WHITE)

            # ── Mouse button DOWN ────────────────────────────────
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

                # Check tool buttons
                for btn in buttons:
                    if btn.is_clicked(mouse_pos):
                        current_tool = btn.tool_id

                # Check colour swatches
                for i, color in enumerate(PALETTE):
                    if swatch_rect(i).collidepoint(mouse_pos):
                        current_color = color

                # Check brush-size buttons
                if btn_size_minus.is_clicked(mouse_pos):
                    brush_radius = max(1, brush_radius - 2)
                if btn_size_plus.is_clicked(mouse_pos):
                    brush_radius = min(60, brush_radius + 2)

                # Begin drawing on the canvas
                if mouse_on_canvas:
                    cp = canvas_pos(mouse_pos)

                    if current_tool in (TOOL_RECTANGLE, TOOL_SQUARE, TOOL_CIRCLE,
                                        TOOL_RIGHT_TRI, TOOL_EQ_TRI, TOOL_RHOMBUS):
                        # All shape tools: record the drag start point
                        drag_start = cp
                        dragging   = True

                    elif current_tool == TOOL_PEN:
                        # Freehand: place an initial dot and remember the position
                        pygame.draw.circle(canvas, current_color, cp, brush_radius)
                        prev_pos = cp

                    elif current_tool == TOOL_ERASER:
                        # Eraser: paint white over the canvas
                        pygame.draw.circle(canvas, WHITE, cp, brush_radius)
                        prev_pos = cp

            # ── Mouse button UP ──────────────────────────────────
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if dragging and drag_start is not None and mouse_on_canvas:
                    # Commit the completed shape to the permanent canvas
                    commit_shape(canvas, current_tool, drag_start,
                                 canvas_pos(mouse_pos), current_color, brush_radius)
                # Reset drag state regardless of where the mouse was released
                dragging   = False
                drag_start = None
                prev_pos   = None

            # ── Mouse MOTION ─────────────────────────────────────
            if event.type == pygame.MOUSEMOTION:
                if pygame.mouse.get_pressed()[0] and mouse_on_canvas:
                    cp = canvas_pos(mouse_pos)

                    if current_tool == TOOL_PEN and prev_pos is not None:
                        # Fill in the stroke between the last position and now
                        draw_line_between(canvas, prev_pos, cp, current_color, brush_radius)
                        prev_pos = cp

                    elif current_tool == TOOL_ERASER and prev_pos is not None:
                        # Same as pen but paints white (erase)
                        draw_line_between(canvas, prev_pos, cp, WHITE, brush_radius)
                        prev_pos = cp

        # RENDERING
        screen.fill((30, 30, 30))   # dark background behind the canvas

        # Blit the canvas onto the screen (offset by the toolbar width)
        screen.blit(canvas, (CANVAS_X, CANVAS_Y))

        # While a shape drag is in progress, draw a live preview:
        # Copy the canvas so we can add the ghost outline without modifying the real data.
        if dragging and drag_start is not None:
            preview = canvas.copy()
            draw_ghost_shape(preview, current_tool, drag_start,
                             canvas_pos(mouse_pos), current_color, brush_radius)
            screen.blit(preview, (CANVAS_X, CANVAS_Y))

        # Draw a cursor indicator on the canvas for pen / eraser
        if mouse_on_canvas:
            if current_tool == TOOL_ERASER:
                # Grey circle shows the eraser radius
                pygame.draw.circle(screen, (180, 180, 180), mouse_pos, brush_radius, 1)
            elif current_tool == TOOL_PEN:
                # Coloured circle shows the pen radius
                pygame.draw.circle(screen, current_color, mouse_pos, brush_radius, 1)

        # Draw the toolbar panel on top of everything else
        draw_toolbar(screen, mouse_pos)

        # Keyboard hint in the very bottom-left corner
        hint = font_ui.render("C = clear", True, (150, 150, 150))
        screen.blit(hint, (10, SCREEN_H - 18))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


main()