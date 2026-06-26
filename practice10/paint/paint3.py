import pygame

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Mini Paint")
    clock = pygame.time.Clock()

    radius = 10
    color = (0, 0, 255)
    mode = "brush"

    drawing = False
    start_pos = None

    canvas = pygame.Surface(screen.get_size())
    canvas.fill((0, 0, 0))

    while True:
        pressed = pygame.key.get_pressed()

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return

                # цвета
                if event.key == pygame.K_r:
                    color = (255, 0, 0)
                elif event.key == pygame.K_g:
                    color = (0, 255, 0)
                elif event.key == pygame.K_b:
                    color = (0, 0, 255)

                # режимы
                elif event.key == pygame.K_1:
                    mode = "brush"
                elif event.key == pygame.K_2:
                    mode = "rectangle"
                elif event.key == pygame.K_3:
                    mode = "circle"
                elif event.key == pygame.K_e:
                    mode = "eraser"

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    drawing = True
                    start_pos = event.pos

                elif event.button == 3:
                    radius = max(1, radius - 2)

                elif event.button == 4:
                    radius = min(100, radius + 2)

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    drawing = False

                    end_pos = event.pos

                    if mode == "rectangle":
                        draw_rect(canvas, color, start_pos, end_pos, radius)

                    elif mode == "circle":
                        draw_circle(canvas, color, start_pos, end_pos, radius)

            if event.type == pygame.MOUSEMOTION:
                if drawing:
                    if mode == "brush":
                        pygame.draw.circle(canvas, color, event.pos, radius)

                    elif mode == "eraser":
                        pygame.draw.circle(canvas, (0, 0, 0), event.pos, radius)

        screen.fill((30, 30, 30))
        screen.blit(canvas, (0, 0))

        # предпросмотр фигур
        if drawing and start_pos:
            current_pos = pygame.mouse.get_pos()

            if mode == "rectangle":
                preview_rect(screen, color, start_pos, current_pos, radius)

            elif mode == "circle":
                preview_circle(screen, color, start_pos, current_pos, radius)

        pygame.display.flip()
        clock.tick(60)


def draw_rect(surface, color, start, end, width):
    rect = pygame.Rect(start, (end[0] - start[0], end[1] - start[1]))
    pygame.draw.rect(surface, color, rect, width)


def preview_rect(screen, color, start, end, width):
    rect = pygame.Rect(start, (end[0] - start[0], end[1] - start[1]))
    pygame.draw.rect(screen, color, rect, width)


def draw_circle(surface, color, start, end, width):
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    radius = int((dx**2 + dy**2) ** 0.5)
    pygame.draw.circle(surface, color, start, radius, width)


def preview_circle(screen, color, start, end, width):
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    radius = int((dx**2 + dy**2) ** 0.5)
    pygame.draw.circle(screen, color, start, radius, width)


main()