"""
===================================================
  PAINT – Extended from nerdparadise.com/programming/pygame/part6
  Extra features added:
    • Draw rectangle (drag to size)
    • Draw circle (drag to size)
    • Eraser tool
    • Color selection palette
===================================================
"""

import pygame
import math

# ================================================================
#  CONSTANTS
# ================================================================
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

# Tool IDs
TOOL_PEN       = "pen"
TOOL_ERASER    = "eraser"
TOOL_RECTANGLE = "rect"
TOOL_CIRCLE    = "circle"

# UI colours
TOOLBAR_BG      = (45,  45,  45)
TOOLBAR_BORDER  = (80,  80,  80)
SELECTED_BORDER = (255, 220, 0)    # golden highlight for selected button/colour
BTN_NORMAL      = (70,  70,  70)
BTN_HOVER       = (100, 100, 100)
WHITE           = (255, 255, 255)
BLACK           = (0,   0,   0)


# ================================================================
#  HELPER FUNCTIONS
# ================================================================

def clamp(val, lo, hi):
    """Clamp val to the range [lo, hi]."""
    return max(lo, min(hi, val))


def on_canvas(pos):
    """Return True if the pixel position is inside the canvas area."""
    x, y = pos
    return CANVAS_X <= x < CANVAS_X + CANVAS_W and 0 <= y < CANVAS_H


def canvas_pos(pos):
    """Convert screen position to canvas-relative position."""
    return (pos[0] - CANVAS_X, pos[1] - CANVAS_Y)


# ================================================================
#  BUTTON CLASS  – simple clickable rectangle with label
# ================================================================
class Button:
    def __init__(self, rect, label, tool_id, font):
        self.rect    = pygame.Rect(rect)
        self.label   = label
        self.tool_id = tool_id
        self.font    = font

    def draw(self, surface, selected, mouse_pos):
        hovered = self.rect.collidepoint(mouse_pos)
        # Background colour
        color = BTN_HOVER if hovered else BTN_NORMAL
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        # Highlight when selected
        border_c = SELECTED_BORDER if selected else TOOLBAR_BORDER
        pygame.draw.rect(surface, border_c, self.rect, 2, border_radius=5)
        # Label
        text_surf = self.font.render(self.label, True, WHITE)
        tx = self.rect.centerx - text_surf.get_width() // 2
        ty = self.rect.centery - text_surf.get_height() // 2
        surface.blit(text_surf, (tx, ty))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


# ================================================================
#  PYGAME SETUP
# ================================================================
pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Paint")
clock  = pygame.time.Clock()

font_ui = pygame.font.SysFont("Consolas", 13, bold=True)

# --- Canvas surface – we draw here, then blit to the screen ---
canvas = pygame.Surface((CANVAS_W, CANVAS_H))
canvas.fill(WHITE)   # start with a white blank canvas


# ================================================================
#  TOOLBAR LAYOUT
# ================================================================
SWATCH_SIZE = 26     # colour swatch size
SWATCH_PAD  = 6      # padding between swatches
SWATCHES_PER_ROW = 4

# Compute swatch grid positions
def swatch_rect(index):
    """Return (x, y, w, h) for the colour swatch at the given palette index."""
    col = index % SWATCHES_PER_ROW
    row = index // SWATCHES_PER_ROW
    x   = 6 + col * (SWATCH_SIZE + SWATCH_PAD)
    y   = 260 + row * (SWATCH_SIZE + SWATCH_PAD)
    return pygame.Rect(x, y, SWATCH_SIZE, SWATCH_SIZE)

# Tool buttons
buttons = [
    Button((10, 10,  TOOLBAR_W - 20, 34), "Pen",      TOOL_PEN,       font_ui),
    Button((10, 52,  TOOLBAR_W - 20, 34), "Eraser",   TOOL_ERASER,    font_ui),
    Button((10, 94,  TOOLBAR_W - 20, 34), "Rect",     TOOL_RECTANGLE, font_ui),
    Button((10, 136, TOOLBAR_W - 20, 34), "Circle",   TOOL_CIRCLE,    font_ui),
]

# Brush-size slider (just two shortcut buttons here for simplicity)
size_label_rect = pygame.Rect(10, 185, TOOLBAR_W - 20, 20)
btn_size_minus  = Button((10,  208, 50, 28), "  -",  None, font_ui)
btn_size_plus   = Button((70,  208, 50, 28), "  +",  None, font_ui)


# ================================================================
#  GAME STATE
# ================================================================
current_tool  = TOOL_PEN
current_color = BLACK
brush_radius  = 8        # pen / eraser brush size

# For drag-drawing shapes:
drag_start    = None     # canvas-relative start point of the drag
dragging      = False    # currently dragging a shape?

# Track freehand pen points between frames
prev_pos = None


# ================================================================
#  DRAWING HELPERS
# ================================================================

def draw_line_between(surface, p1, p2, color, radius):
    """Draw a smooth thick line by filling circles along the line."""
    dx = p1[0] - p2[0]
    dy = p1[1] - p2[1]
    iterations = max(abs(dx), abs(dy), 1)
    for i in range(iterations):
        t = i / iterations
        x = int((1 - t) * p1[0] + t * p2[0])
        y = int((1 - t) * p1[1] + t * p2[1])
        pygame.draw.circle(surface, color, (x, y), radius)


def draw_ghost_shape(surface, tool, start, end, color, radius):
    """
    Draw a preview 'ghost' (outline) of the shape being dragged.
    This is blitted on top of the canvas each frame while dragging.
    """
    if tool == TOOL_RECTANGLE:
        rect = pygame.Rect(
            min(start[0], end[0]),
            min(start[1], end[1]),
            abs(end[0] - start[0]),
            abs(end[1] - start[1]),
        )
        pygame.draw.rect(surface, color, rect, 2)

    elif tool == TOOL_CIRCLE:
        cx = (start[0] + end[0]) // 2
        cy = (start[1] + end[1]) // 2
        r  = int(math.hypot(end[0] - start[0], end[1] - start[1]) / 2)
        if r > 0:
            pygame.draw.circle(surface, color, (cx, cy), r, 2)


def commit_shape(canvas, tool, start, end, color, radius):
    """Permanently draw the final shape onto the canvas surface."""
    if tool == TOOL_RECTANGLE:
        rect = pygame.Rect(
            min(start[0], end[0]),
            min(start[1], end[1]),
            abs(end[0] - start[0]),
            abs(end[1] - start[1]),
        )
        pygame.draw.rect(canvas, color, rect, 2)

    elif tool == TOOL_CIRCLE:
        cx = (start[0] + end[0]) // 2
        cy = (start[1] + end[1]) // 2
        r  = int(math.hypot(end[0] - start[0], end[1] - start[1]) / 2)
        if r > 0:
            pygame.draw.circle(canvas, color, (cx, cy), r, 2)


# ================================================================
#  TOOLBAR DRAWING
# ================================================================

def draw_toolbar(surface, mouse_pos):
    """Draw the entire left-side toolbar panel."""
    # Panel background
    pygame.draw.rect(surface, TOOLBAR_BG, (0, 0, TOOLBAR_W, SCREEN_H))
    pygame.draw.line(surface, TOOLBAR_BORDER, (TOOLBAR_W, 0), (TOOLBAR_W, SCREEN_H), 2)

    # Tool buttons
    for btn in buttons:
        btn.draw(surface, btn.tool_id == current_tool, mouse_pos)

    # Brush size label + buttons
    size_label = font_ui.render(f"Size: {brush_radius}", True, WHITE)
    surface.blit(size_label, (10, 187))
    btn_size_minus.draw(surface, False, mouse_pos)
    btn_size_plus.draw(surface,  False, mouse_pos)

    # "Colors" heading
    col_heading = font_ui.render("Colors:", True, WHITE)
    surface.blit(col_heading, (10, 242))

    # Colour swatches
    for i, color in enumerate(PALETTE):
        rect = swatch_rect(i)
        pygame.draw.rect(surface, color, rect, border_radius=4)
        # Highlight the currently selected colour
        if color == current_color:
            pygame.draw.rect(surface, SELECTED_BORDER, rect, 3, border_radius=4)
        else:
            pygame.draw.rect(surface, TOOLBAR_BORDER,  rect, 1, border_radius=4)

    # Show current colour swatch at bottom of toolbar
    current_col_y = SCREEN_H - 70
    label = font_ui.render("Active:", True, WHITE)
    surface.blit(label, (10, current_col_y))
    pygame.draw.rect(surface, current_color,  (10, current_col_y + 20, TOOLBAR_W - 20, 36), border_radius=5)
    pygame.draw.rect(surface, SELECTED_BORDER,(10, current_col_y + 20, TOOLBAR_W - 20, 36), 2, border_radius=5)


# ================================================================
#  MAIN LOOP
# ================================================================

def main():
    global current_tool, current_color, brush_radius
    global drag_start, dragging, prev_pos

    running = True
    while running:

        mouse_pos    = pygame.mouse.get_pos()
        mouse_on_canvas = on_canvas(mouse_pos)

        # -------------------------------------------------------
        # EVENT HANDLING
        # -------------------------------------------------------
        for event in pygame.event.get():

            # --- Quit ---
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                # Ctrl+W / Alt+F4 / Escape → quit
                pressed = pygame.key.get_pressed()
                if (event.key == pygame.K_w and (pressed[pygame.K_LCTRL] or pressed[pygame.K_RCTRL])):
                    running = False
                if event.key == pygame.K_ESCAPE:
                    running = False
                # C → clear canvas
                if event.key == pygame.K_c:
                    canvas.fill(WHITE)

            # --- Mouse button DOWN ---
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

                # Click on a tool button?
                for btn in buttons:
                    if btn.is_clicked(mouse_pos):
                        current_tool = btn.tool_id

                # Click on a colour swatch?
                for i, color in enumerate(PALETTE):
                    if swatch_rect(i).collidepoint(mouse_pos):
                        current_color = color

                # Click on size buttons?
                if btn_size_minus.is_clicked(mouse_pos):
                    brush_radius = max(1, brush_radius - 2)
                if btn_size_plus.is_clicked(mouse_pos):
                    brush_radius = min(60, brush_radius + 2)

                # Start drawing on the canvas
                if mouse_on_canvas:
                    cp = canvas_pos(mouse_pos)
                    if current_tool in (TOOL_RECTANGLE, TOOL_CIRCLE):
                        # Begin drag for shape tools
                        drag_start = cp
                        dragging   = True
                    elif current_tool == TOOL_PEN:
                        # Start a freehand stroke
                        pygame.draw.circle(canvas, current_color, cp, brush_radius)
                        prev_pos = cp
                    elif current_tool == TOOL_ERASER:
                        # Erase (paint white)
                        pygame.draw.circle(canvas, WHITE, cp, brush_radius)
                        prev_pos = cp

            # --- Mouse button UP ---
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if dragging and drag_start is not None and mouse_on_canvas:
                    # Commit the shape permanently to the canvas
                    commit_shape(canvas, current_tool, drag_start, canvas_pos(mouse_pos),
                                 current_color, brush_radius)
                dragging   = False
                drag_start = None
                prev_pos   = None

            # --- Mouse MOTION ---
            if event.type == pygame.MOUSEMOTION:
                if pygame.mouse.get_pressed()[0] and mouse_on_canvas:
                    cp = canvas_pos(mouse_pos)
                    if current_tool == TOOL_PEN and prev_pos is not None:
                        draw_line_between(canvas, prev_pos, cp, current_color, brush_radius)
                        prev_pos = cp
                    elif current_tool == TOOL_ERASER and prev_pos is not None:
                        draw_line_between(canvas, prev_pos, cp, WHITE, brush_radius)
                        prev_pos = cp

        # -------------------------------------------------------
        # DRAWING
        # -------------------------------------------------------
        screen.fill((30, 30, 30))

        # Draw the canvas (copy it so we can overlay the ghost shape without dirtying it)
        screen.blit(canvas, (CANVAS_X, CANVAS_Y))

        # Draw ghost preview of the shape being dragged
        if dragging and drag_start is not None:
            preview = canvas.copy()
            current_mouse_canvas = canvas_pos(mouse_pos)
            draw_ghost_shape(preview, current_tool, drag_start, current_mouse_canvas,
                             current_color, brush_radius)
            screen.blit(preview, (CANVAS_X, CANVAS_Y))

        # Draw cursor crosshair / eraser indicator on the canvas
        if mouse_on_canvas:
            cp = mouse_pos
            if current_tool == TOOL_ERASER:
                pygame.draw.circle(screen, (180, 180, 180), cp, brush_radius, 1)
            elif current_tool == TOOL_PEN:
                pygame.draw.circle(screen, current_color, cp, brush_radius, 1)

        # Draw toolbar on top
        draw_toolbar(screen, mouse_pos)

        # Keyboard shortcut hint at the bottom of the toolbar
        hint = font_ui.render("C = clear", True, (150, 150, 150))
        screen.blit(hint, (10, SCREEN_H - 18))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


main()