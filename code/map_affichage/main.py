"""
main2.py — Point d'entrée du jeu fusionné.

Ordre de démarrage :
    1. pygame.init()
    2. Menu principal  (choix du joueur / nouveau / skin)
    3. Game.run()      (carte + mini-jeux)
"""

import pygame
from menu import MainMenu
from game import Game


def main():
    pygame.init()
    pygame.mixer.init()

    # Crée la fenêtre une seule fois (1280×720)
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Mon Jeu")

    # ── Menu ──────────────────────────────────────────────────────────────────
    menu      = MainMenu(screen)
    save_data = menu.run()          # bloque jusqu'au choix du joueur

    if save_data is None:           # l'utilisateur a fermé la fenêtre
        pygame.quit()
        return

    # ── Jeu ───────────────────────────────────────────────────────────────────
    game = Game(save_data)
    game.run()

    pygame.quit()


if __name__ == "__main__":
    main()
