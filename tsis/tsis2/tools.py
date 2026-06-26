import pygame
import math
from collections import deque

# ---------------------------------------------------------------------------
# Tool ID constants – every drawing mode has a unique string identifier
# ---------------------------------------------------------------------------
TOOL_PEN       = "pen"
TOOL_LINE      = "line"
TOOL_ERASER    = "eraser"
TOOL_RECTANGLE = "rect"
TOOL_SQUARE    = "square"
TOOL_CIRCLE    = "circle"
TOOL_RIGHT_TRI = "right_tri"
TOOL_EQ_TRI    = "eq_tri"
TOOL_RHOMBUS   = "rhombus"
TOOL_FILL      = "fill"
TOOL_TEXT      = "text"

# Brush size presets (keyboard shortcuts 1 / 2 / 3)
BRUSH_SIZES = {
    pygame.K_1: 2,
    pygame.K_2: 5,
    pygame.K_3: 10,
}

WHITE = (255, 255, 255)


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def rect_from_drag(start, end):
    """Return a pygame.Rect spanning start→end regardless of drag direction."""
    return pygame.Rect(
        min(start[0], end[0]),
        min(start[1], end[1]),
        abs(end[0] - start[0]),
        abs(end[1] - start[1]),
    )


def square_end(start, end):
    """Force the drag end so the bounding box becomes a square."""
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    side = min(abs(dx), abs(dy))
    sx = 1 if dx >= 0 else -1
    sy = 1 if dy >= 0 else -1
    return (start[0] + sx * side, start[1] + sy * side)


def right_tri_points(start, end):
    """
    Three vertices of a right-angle triangle.
    Right angle sits at *start*; legs are axis-aligned.
    """
    ax, ay = start
    bx, by = end
    return [(ax, ay), (bx, ay), (ax, by)]


def eq_tri_points(start, end):
    """
    Three vertices of an equilateral triangle.
    Base = start → (end[0], start[1]); apex centred above/below.
    """
    ax, ay = start
    bx, by = end
    base      = bx - ax
    height    = abs(base) * math.sqrt(3) / 2
    direction = -1 if by < ay else 1
    apex_x    = ax + base // 2
    apex_y    = int(ay + direction * height)
    return [(ax, ay), (bx, ay), (apex_x, apex_y)]


def rhombus_points(start, end):
    """Four vertices of a rhombus (midpoints of the bounding-box sides)."""
    x0, y0 = min(start[0], end[0]), min(start[1], end[1])
    x1, y1 = max(start[0], end[0]), max(start[1], end[1])
    mx, my  = (x0 + x1) // 2, (y0 + y1) // 2
    return [(mx, y0), (x1, my), (mx, y1), (x0, my)]


# ---------------------------------------------------------------------------
# Stroke helper
# ---------------------------------------------------------------------------

def draw_stroke(surface, p1, p2, color, radius):
    """
    Draw a smooth thick stroke between two canvas points using filled circles
    so there are no gaps even when the mouse moves quickly.
    """
    dx    = p1[0] - p2[0]
    dy    = p1[1] - p2[1]
    steps = max(abs(dx), abs(dy), 1)
    for i in range(steps):
        t = i / steps
        x = int((1 - t) * p1[0] + t * p2[0])
        y = int((1 - t) * p1[1] + t * p2[1])
        pygame.draw.circle(surface, color, (x, y), radius)


# ---------------------------------------------------------------------------
# Shape ghost (live preview while dragging)
# ---------------------------------------------------------------------------

def draw_ghost_shape(surface, tool, start, end, color, thickness):
    """Render a temporary outline preview – never touches the real canvas."""
    if tool == TOOL_RECTANGLE:
        pygame.draw.rect(surface, color, rect_from_drag(start, end), thickness)

    elif tool == TOOL_SQUARE:
        pygame.draw.rect(surface, color, rect_from_drag(start, square_end(start, end)), thickness)

    elif tool == TOOL_CIRCLE:
        cx = (start[0] + end[0]) // 2
        cy = (start[1] + end[1]) // 2
        r  = int(math.hypot(end[0] - start[0], end[1] - start[1]) / 2)
        if r > 0:
            pygame.draw.circle(surface, color, (cx, cy), r, thickness)

    elif tool == TOOL_RIGHT_TRI:
        pygame.draw.polygon(surface, color, right_tri_points(start, end), thickness)

    elif tool == TOOL_EQ_TRI:
        pygame.draw.polygon(surface, color, eq_tri_points(start, end), thickness)

    elif tool == TOOL_RHOMBUS:
        pygame.draw.polygon(surface, color, rhombus_points(start, end), thickness)

    elif tool == TOOL_LINE:
        pygame.draw.line(surface, color, start, end, thickness)


# ---------------------------------------------------------------------------
# Shape commit (permanently write to the canvas surface)
# ---------------------------------------------------------------------------

def commit_shape(canvas_surf, tool, start, end, color, thickness):
    """Finalise a shape onto the canvas when the mouse button is released."""
    if tool == TOOL_RECTANGLE:
        pygame.draw.rect(canvas_surf, color, rect_from_drag(start, end), thickness)

    elif tool == TOOL_SQUARE:
        pygame.draw.rect(canvas_surf, color, rect_from_drag(start, square_end(start, end)), thickness)

    elif tool == TOOL_CIRCLE:
        cx = (start[0] + end[0]) // 2
        cy = (start[1] + end[1]) // 2
        r  = int(math.hypot(end[0] - start[0], end[1] - start[1]) / 2)
        if r > 0:
            pygame.draw.circle(canvas_surf, color, (cx, cy), r, thickness)

    elif tool == TOOL_RIGHT_TRI:
        pygame.draw.polygon(canvas_surf, color, right_tri_points(start, end), thickness)

    elif tool == TOOL_EQ_TRI:
        pygame.draw.polygon(canvas_surf, color, eq_tri_points(start, end), thickness)

    elif tool == TOOL_RHOMBUS:
        pygame.draw.polygon(canvas_surf, color, rhombus_points(start, end), thickness)

    elif tool == TOOL_LINE:
        pygame.draw.line(canvas_surf, color, start, end, thickness)


# ---------------------------------------------------------------------------
# 3.3  Flood-fill  (BFS over canvas pixels)
# ---------------------------------------------------------------------------

def flood_fill(canvas_surf, start_pos, fill_color):
    """
    BFS flood-fill starting at *start_pos* (canvas-relative).
    Replaces all connected pixels that share the exact same colour as the
    pixel at *start_pos* with *fill_color*.

    Uses pygame.Surface.get_at() / set_at() as required by the task spec.
    """
    x0, y0   = int(start_pos[0]), int(start_pos[1])
    w, h     = canvas_surf.get_size()

    # Guard: position must be inside the canvas
    if not (0 <= x0 < w and 0 <= y0 < h):
        return

    target_color = canvas_surf.get_at((x0, y0))[:3]   # ignore alpha
    fill_rgb     = fill_color[:3]

    # Nothing to do if target already has the fill colour
    if target_color == fill_rgb:
        return

    # Lock the surface for fast pixel access
    canvas_surf.lock()

    visited = set()
    queue   = deque()
    queue.append((x0, y0))
    visited.add((x0, y0))

    while queue:
        cx, cy = queue.popleft()
        canvas_surf.set_at((cx, cy), fill_rgb)

        for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
            if (nx, ny) not in visited and 0 <= nx < w and 0 <= ny < h:
                if canvas_surf.get_at((nx, ny))[:3] == target_color:
                    visited.add((nx, ny))
                    queue.append((nx, ny))

    canvas_surf.unlock()


# ---------------------------------------------------------------------------
# 3.5  Text session state
# ---------------------------------------------------------------------------

class TextSession:
    """
    Manages a single in-progress text-placement operation.

    Lifecycle:
        1. User clicks canvas  → TextSession(pos, font)
        2. User types          → session.add_char(char)
        3. User presses Enter  → session.commit(canvas_surf, color)
        4. User presses Escape → discard the session
    """

    def __init__(self, pos, font):
        self.pos    = pos      # (x, y) on the canvas where text begins
        self.font   = font
        self.text   = ""
        self.active = True

    def add_char(self, char):
        self.text += char

    def backspace(self):
        self.text = self.text[:-1]

    def commit(self, canvas_surf, color):
        """Render the typed text permanently onto *canvas_surf*."""
        if self.text:
            surf = self.font.render(self.text, True, color)
            canvas_surf.blit(surf, self.pos)
        self.active = False

    def cancel(self):
        self.active = False

    def draw_cursor(self, surface, canvas_offset, color):
        """
        Draw a blinking text cursor and the in-progress text onto *surface*
        (the screen, not the canvas) so the text appears live while typing.
        """
        ox, oy = canvas_offset
        sx     = self.pos[0] + ox
        sy     = self.pos[1] + oy

        # Render live preview text
        if self.text:
            preview = self.font.render(self.text, True, color)
            surface.blit(preview, (sx, sy))

        # Simple blinking cursor (toggles every 500 ms)
        if pygame.time.get_ticks() % 1000 < 500:
            text_w = self.font.size(self.text)[0]
            cur_x  = sx + text_w
            cur_h  = self.font.get_height()
            pygame.draw.line(surface, color, (cur_x, sy), (cur_x, sy + cur_h), 2)