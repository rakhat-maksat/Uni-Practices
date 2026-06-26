import pygame
import sys
from pygame.locals import *

from persistence import load_settings, save_settings, save_score
from ui import (
    main_menu,
    username_screen,
    settings_screen,
    leaderboard_screen,
    game_over_screen,
)
from racer import run_game

# ==================== INIT ====================
pygame.init()
pygame.display.set_caption("Racer")

SCREEN_WIDTH  = 400
SCREEN_HEIGHT = 600
surf = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# ==================== MAIN LOOP ====================
def main():
    settings = load_settings()
    username = None

    while True:
        choice = main_menu(surf)

        if choice == "quit":
            pygame.quit()
            sys.exit()

        elif choice == "leaderboard":
            leaderboard_screen(surf)

        elif choice == "settings":
            settings = settings_screen(surf, settings)

        elif choice == "play":
            # Ask for name if not set
            if username is None:
                username = username_screen(surf)

            while True:
                result = run_game(surf, settings, username)

                # Save score
                save_score(
                    name=username,
                    score=result["score"],
                    distance=result["distance"],
                    coins=result["coins"]
                )

                # Game Over screen
                action = game_over_screen(
                    surf,
                    score=result["score"],
                    distance=result["distance"],
                    coins=result["coins"]
                )

                if action == "retry":
                    continue          # play again with same name
                elif action == "menu":
                    break             # back to main menu
                else:
                    pygame.quit()
                    sys.exit()


if __name__ == "__main__":
    main()