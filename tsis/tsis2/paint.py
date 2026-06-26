import pygame
import datetime

from tools import (
    # Tool IDs
    TOOL_PEN, TOOL_LINE, TOOL_ERASER,
    TOOL_RECTANGLE, TOOL_SQUARE, TOOL_CIRCLE,
    TOOL_RIGHT_TRI, TOOL_EQ_TRI, TOOL_RHOMBUS,
    TOOL_FILL, TOOL_TEXT,
    # Brush-size key map
    BRUSH_SIZES,
    # Drawing functions
    draw_stroke, draw_ghost_shape, commit_shape,
    flood_fill,
    # Text session
    TextSession,
)

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------
SCREEN_W   = 960
SCREEN_H   = 680
TOOLBAR_W  = 140
CANVAS_X   = TOOLBAR_W
CANVAS_Y   = 0
CANVAS_W   = SCREEN_W - TOOLBAR_W
CANVAS_H   = SCREEN_H

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# UI colours
# ---------------------------------------------------------------------------
TOOLBAR_BG      = (30,  30,  38)
TOOLBAR_BORDER  = (70,  70,  80)
SELECTED_BORDER = (255, 210, 0)
BTN_NORMAL      = (55,  55,  68)
BTN_HOVER       = (85,  85, 105)
SECTION_LABEL   = (140, 140, 165)
WHITE           = (255, 255, 255)
BLACK           = (0,   0,   0)

# ---------------------------------------------------------------------------
# Button class
# ---------------------------------------------------------------------------

class Button:
    def __init__(self, rect, label, tool_id, font):
        self.rect    = pygame.Rect(rect)
        self.label   = label
        self.tool_id = tool_id
        self.font    = font

    def draw(self, surface, selected, mouse_pos):
        hovered  = self.rect.collidepoint(mouse_pos)
        bg_color = BTN_HOVER if hovered else BTN_NORMAL
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=6)
        border_c = SELECTED_BORDER if selected else TOOLBAR_BORDER
        border_w = 2
        pygame.draw.rect(surface, border_c, self.rect, border_w, border_radius=6)
        text_surf = self.font.render(self.label, True, WHITE)
        tx = self.rect.centerx - text_surf.get_width()  // 2
        ty = self.rect.centery - text_surf.get_height() // 2
        surface.blit(text_surf, (tx, ty))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def on_canvas(pos):
    x, y = pos
    return CANVAS_X <= x < CANVAS_X + CANVAS_W and 0 <= y < CANVAS_H


def canvas_pos(pos):
    return (pos[0] - CANVAS_X, pos[1] - CANVAS_Y)


def section_label(surface, font, text, y, color=SECTION_LABEL):
    surf = font.render(text, True, color)
    surface.blit(surf, (10, y))


# ---------------------------------------------------------------------------
# Toolbar layout
# ---------------------------------------------------------------------------
SWATCH_SIZE      = 24
SWATCH_PAD       = 5
SWATCHES_PER_ROW = 4

# Y-position where the colour palette grid starts
PALETTE_Y = 480


def swatch_rect(index):
    col = index % SWATCHES_PER_ROW
    row = index // SWATCHES_PER_ROW
    x   = 8 + col * (SWATCH_SIZE + SWATCH_PAD)
    y   = PALETTE_Y + row * (SWATCH_SIZE + SWATCH_PAD)
    return pygame.Rect(x, y, SWATCH_SIZE, SWATCH_SIZE)


# ---------------------------------------------------------------------------
# Pygame init
# ---------------------------------------------------------------------------
pygame.init()
screen  = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Paint – TSIS 2")
clock   = pygame.time.Clock()
font_ui = pygame.font.SysFont("Consolas", 12, bold=True)
font_canvas = pygame.font.SysFont("Arial", 22)   # used by the text tool

canvas = pygame.Surface((CANVAS_W, CANVAS_H))
canvas.fill(WHITE)

# ---------------------------------------------------------------------------
# Build tool buttons  (two columns for a compact layout)
# ---------------------------------------------------------------------------
BW = 60    # button width
BH = 32    # button height
PAD = 8    # horizontal gap between the two columns
LEFT_X  = 6
RIGHT_X = LEFT_X + BW + PAD
ROW_H   = 38   # vertical pitch


def make_buttons():
    rows = [
        ("Pen",     TOOL_PEN,       LEFT_X),
        ("Line",    TOOL_LINE,      RIGHT_X),
        ("Eraser",  TOOL_ERASER,    LEFT_X),
        ("Fill",    TOOL_FILL,      RIGHT_X),
        ("Rect",    TOOL_RECTANGLE, LEFT_X),
        ("Square",  TOOL_SQUARE,    RIGHT_X),
        ("Circle",  TOOL_CIRCLE,    LEFT_X),
        ("R.Tri",   TOOL_RIGHT_TRI, RIGHT_X),
        ("Eq.Tri",  TOOL_EQ_TRI,    LEFT_X),
        ("Rhombus", TOOL_RHOMBUS,   RIGHT_X),
        ("Text",    TOOL_TEXT,      LEFT_X),
    ]
    btns = []
    row_idx = 0
    col_seen = {LEFT_X: 0, RIGHT_X: 0}  # track row per column

    # layout in pairs
    pairs = [
        ("Pen",     TOOL_PEN,       "Line",    TOOL_LINE),
        ("Eraser",  TOOL_ERASER,    "Fill",    TOOL_FILL),
        ("Rect",    TOOL_RECTANGLE, "Square",  TOOL_SQUARE),
        ("Circle",  TOOL_CIRCLE,    "R.Tri",   TOOL_RIGHT_TRI),
        ("Eq.Tri",  TOOL_EQ_TRI,    "Rhombus", TOOL_RHOMBUS),
        ("Text",    TOOL_TEXT,      None,      None),
    ]
    y = 14
    for l_lbl, l_id, r_lbl, r_id in pairs:
        btns.append(Button((LEFT_X,  y, BW, BH), l_lbl, l_id,  font_ui))
        if r_lbl:
            btns.append(Button((RIGHT_X, y, BW, BH), r_lbl, r_id, font_ui))
        y += ROW_H
    return btns, y   # return next free y


buttons, next_y = make_buttons()

# Brush-size section
SIZE_Y = next_y + 6
btn_size_minus = Button((LEFT_X,          SIZE_Y + 20, BW, 28), "−", None, font_ui)
btn_size_plus  = Button((RIGHT_X,         SIZE_Y + 20, BW, 28), "+", None, font_ui)

# Shortcut buttons for sizes 1/2/3
SIZE_BTN_Y = SIZE_Y + 56
btn_sz1 = Button((LEFT_X,             SIZE_BTN_Y, 36, 26), "S", None, font_ui)
btn_sz2 = Button((LEFT_X + 38,        SIZE_BTN_Y, 36, 26), "M", None, font_ui)
btn_sz3 = Button((LEFT_X + 76,        SIZE_BTN_Y, 36, 26), "L", None, font_ui)

SIZE_PRESETS = {id(btn_sz1): 2, id(btn_sz2): 5, id(btn_sz3): 10}


# ---------------------------------------------------------------------------
# Toolbar rendering
# ---------------------------------------------------------------------------

def draw_toolbar(surface, mouse_pos, current_tool, current_color, brush_size):
    pygame.draw.rect(surface, TOOLBAR_BG, (0, 0, TOOLBAR_W, SCREEN_H))
    pygame.draw.line(surface, TOOLBAR_BORDER, (TOOLBAR_W - 1, 0), (TOOLBAR_W - 1, SCREEN_H), 2)

    # -- Tool buttons --
    section_label(surface, font_ui, "TOOLS", 2)
    for btn in buttons:
        btn.draw(surface, btn.tool_id == current_tool, mouse_pos)

    # -- Brush size --
    section_label(surface, font_ui, "SIZE", SIZE_Y)
    size_val = font_ui.render(f"{brush_size} px", True, WHITE)
    surface.blit(size_val, (TOOLBAR_W // 2 - size_val.get_width() // 2, SIZE_Y + 2))
    btn_size_minus.draw(surface, False, mouse_pos)
    btn_size_plus.draw(surface,  False, mouse_pos)

    # S / M / L preset shortcuts
    section_label(surface, font_ui, "1=S 2=M 3=L", SIZE_BTN_Y - 14)
    btn_sz1.draw(surface, brush_size == 2,  mouse_pos)
    btn_sz2.draw(surface, brush_size == 5,  mouse_pos)
    btn_sz3.draw(surface, brush_size == 10, mouse_pos)

    # -- Colour palette --
    section_label(surface, font_ui, "COLORS", PALETTE_Y - 14)
    for i, color in enumerate(PALETTE):
        rect = swatch_rect(i)
        pygame.draw.rect(surface, color, rect, border_radius=3)
        is_sel   = (color == current_color)
        border_c = SELECTED_BORDER if is_sel else TOOLBAR_BORDER
        border_w = 3 if is_sel else 1
        pygame.draw.rect(surface, border_c, rect, border_w, border_radius=3)

    # -- Active colour preview --
    prev_y = SCREEN_H - 52
    section_label(surface, font_ui, "ACTIVE", prev_y)
    pygame.draw.rect(surface, current_color,   (8, prev_y + 14, TOOLBAR_W - 16, 28), border_radius=5)
    pygame.draw.rect(surface, SELECTED_BORDER, (8, prev_y + 14, TOOLBAR_W - 16, 28), 2,  border_radius=5)


# ---------------------------------------------------------------------------
# Save canvas  (3.4)
# ---------------------------------------------------------------------------

def save_canvas(canvas_surf):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename  = f"canvas_{timestamp}.png"
    pygame.image.save(canvas_surf, filename)
    print(f"[Save] Canvas saved as {filename}")
    return filename


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main():
    global canvas

    current_tool  = TOOL_PEN
    current_color = BLACK
    brush_size    = 5          # thickness / radius in pixels

    # Drag state (shapes + line tool)
    drag_start = None
    dragging   = False

    # Pencil / eraser continuity
    prev_pos = None

    # Text session (None when the text tool is idle)
    text_session = None

    # Small on-screen flash message after saving
    save_msg      = ""
    save_msg_time = 0

    running = True
    while running:
        mouse_pos       = pygame.mouse.get_pos()
        mouse_on_canvas = on_canvas(mouse_pos)

        # ── EVENT LOOP ───────────────────────────────────────────────────────
        for event in pygame.event.get():

            # Quit
            if event.type == pygame.QUIT:
                running = False

            # ── Keyboard ────────────────────────────────────────────────────
            if event.type == pygame.KEYDOWN:
                pressed = pygame.key.get_pressed()

                # Text-tool input  (intercept all keys while typing)
                if text_session and text_session.active:
                    if event.key == pygame.K_RETURN:
                        text_session.commit(canvas, current_color)
                        text_session = None
                    elif event.key == pygame.K_ESCAPE:
                        text_session.cancel()
                        text_session = None
                    elif event.key == pygame.K_BACKSPACE:
                        text_session.backspace()
                    else:
                        # Only printable characters
                        if event.unicode and event.unicode.isprintable():
                            text_session.add_char(event.unicode)
                    # While typing, don't process other shortcuts
                    continue

                # Ctrl+S  → save  (3.4)
                ctrl = pressed[pygame.K_LCTRL] or pressed[pygame.K_RCTRL]
                if event.key == pygame.K_s and ctrl:
                    fn = save_canvas(canvas)
                    save_msg      = f"Saved: {fn}"
                    save_msg_time = pygame.time.get_ticks()

                # Ctrl+W / Escape → quit
                if (event.key == pygame.K_w and ctrl) or event.key == pygame.K_ESCAPE:
                    running = False

                # C → clear canvas
                if event.key == pygame.K_c:
                    canvas.fill(WHITE)

                # 1 / 2 / 3 → brush size presets  (3.2)
                if event.key in BRUSH_SIZES:
                    brush_size = BRUSH_SIZES[event.key]

            # ── Mouse button DOWN ────────────────────────────────────────────
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

                # Cancel active text session if clicking outside canvas
                if text_session and text_session.active and not mouse_on_canvas:
                    text_session.cancel()
                    text_session = None

                # Tool buttons
                for btn in buttons:
                    if btn.is_clicked(mouse_pos):
                        current_tool = btn.tool_id
                        # Cancel text session when switching tools
                        if text_session:
                            text_session.cancel()
                            text_session = None

                # Colour swatches
                for i, color in enumerate(PALETTE):
                    if swatch_rect(i).collidepoint(mouse_pos):
                        current_color = color

                # Size +/−
                if btn_size_minus.is_clicked(mouse_pos):
                    brush_size = max(1, brush_size - 1)
                if btn_size_plus.is_clicked(mouse_pos):
                    brush_size = min(60, brush_size + 1)

                # Size preset buttons
                for btn_sz in (btn_sz1, btn_sz2, btn_sz3):
                    if btn_sz.is_clicked(mouse_pos):
                        brush_size = SIZE_PRESETS[id(btn_sz)]

                # Canvas interactions
                if mouse_on_canvas:
                    cp = canvas_pos(mouse_pos)

                    # Shape / line tools start a drag
                    if current_tool in (TOOL_RECTANGLE, TOOL_SQUARE, TOOL_CIRCLE,
                                        TOOL_RIGHT_TRI, TOOL_EQ_TRI, TOOL_RHOMBUS,
                                        TOOL_LINE):
                        drag_start = cp
                        dragging   = True

                    # Pen – initial dot
                    elif current_tool == TOOL_PEN:
                        pygame.draw.circle(canvas, current_color, cp, brush_size)
                        prev_pos = cp

                    # Eraser – initial dot
                    elif current_tool == TOOL_ERASER:
                        pygame.draw.circle(canvas, WHITE, cp, brush_size)
                        prev_pos = cp

                    # Flood fill (3.3)
                    elif current_tool == TOOL_FILL:
                        flood_fill(canvas, cp, current_color)

                    # Text tool – start a new session (3.5)
                    elif current_tool == TOOL_TEXT:
                        # Commit any existing session first
                        if text_session and text_session.active:
                            text_session.commit(canvas, current_color)
                        text_session = TextSession(cp, font_canvas)

            # ── Mouse button UP ──────────────────────────────────────────────
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if dragging and drag_start is not None:
                    end = canvas_pos(mouse_pos)
                    # Clamp end to canvas bounds so shapes stay inside
                    end = (
                        max(0, min(CANVAS_W - 1, end[0])),
                        max(0, min(CANVAS_H - 1, end[1])),
                    )
                    commit_shape(canvas, current_tool, drag_start, end,
                                 current_color, brush_size)
                dragging   = False
                drag_start = None
                prev_pos   = None

            # ── Mouse MOTION ─────────────────────────────────────────────────
            if event.type == pygame.MOUSEMOTION:
                if pygame.mouse.get_pressed()[0] and mouse_on_canvas:
                    cp = canvas_pos(mouse_pos)

                    if current_tool == TOOL_PEN and prev_pos is not None:
                        draw_stroke(canvas, prev_pos, cp, current_color, brush_size)
                        prev_pos = cp

                    elif current_tool == TOOL_ERASER and prev_pos is not None:
                        draw_stroke(canvas, prev_pos, cp, WHITE, brush_size)
                        prev_pos = cp

        # ── RENDERING ────────────────────────────────────────────────────────
        screen.fill((20, 20, 28))

        # Blit canvas
        screen.blit(canvas, (CANVAS_X, CANVAS_Y))

        # Ghost preview for shape / line drags
        if dragging and drag_start is not None:
            preview = canvas.copy()
            draw_ghost_shape(preview, current_tool, drag_start,
                             canvas_pos(mouse_pos), current_color, brush_size)
            screen.blit(preview, (CANVAS_X, CANVAS_Y))

        # Cursor indicator
        if mouse_on_canvas:
            if current_tool == TOOL_ERASER:
                pygame.draw.circle(screen, (180, 180, 180), mouse_pos, brush_size, 1)
            elif current_tool == TOOL_PEN:
                pygame.draw.circle(screen, current_color, mouse_pos, brush_size, 1)
            elif current_tool == TOOL_FILL:
                # Simple crosshair for the fill tool
                pygame.draw.line(screen, current_color,
                                 (mouse_pos[0] - 8, mouse_pos[1]),
                                 (mouse_pos[0] + 8, mouse_pos[1]), 1)
                pygame.draw.line(screen, current_color,
                                 (mouse_pos[0], mouse_pos[1] - 8),
                                 (mouse_pos[0], mouse_pos[1] + 8), 1)

        # Live text preview (3.5)
        if text_session and text_session.active:
            text_session.draw_cursor(screen, (CANVAS_X, CANVAS_Y), current_color)

        # Toolbar
        draw_toolbar(screen, mouse_pos, current_tool, current_color, brush_size)

        # Keyboard hint strip
        hints = font_ui.render("C=Clear  1/2/3=Size  Ctrl+S=Save  Esc=Quit", True, (90, 90, 110))
        screen.blit(hints, (CANVAS_X + 6, SCREEN_H - 16))

        # Save flash message
        if save_msg and pygame.time.get_ticks() - save_msg_time < 3000:
            msg_surf = font_ui.render(save_msg, True, (80, 220, 80))
            screen.blit(msg_surf, (CANVAS_X + 6, 6))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()