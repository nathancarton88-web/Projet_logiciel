import pygame
from menu import MainMenu
from game import Game


def main():
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("l'ile des minis jeux")

    # Boucle menu → jeu → menu (si retour volontaire)
    while True:
        menu      = MainMenu(screen)
        save_data = menu.run()
        if save_data is None:
            break
        game = Game(save_data)
        game.run()
        # Si game.run() retourne, c'est soit fermeture fenêtre soit retour menu
        # → on repart au début de la boucle while

    pygame.quit()


if __name__ == "__main__":
    main()
