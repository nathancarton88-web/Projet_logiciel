import pygame

from entity import Entity
from keylistener import KeyListener
from screen import Screen
from change import Change


class Player(Entity):
    def __init__(self, keylistener: KeyListener, screen: Screen, x: int, y: int):
        super().__init__(keylistener, screen, x, y)
        self.pokedollars: int = 0

        self.spritesheet_bike: pygame.image = pygame.image.load(
            "C:/Users/natha/PycharmProjects/PythonProject1/assets/sprite/hero_01_white_f_cycle_wheel.png"
        )

        self.change: list[Change] | None = None
        self.collisions: list[pygame.Rect] | None = None
        self.change_map: Change | None = None

        # ── Nouveau : déclencheur de mini-jeu ─────────────────────────────────
        # Si le joueur est à portée d'une porte de jeu, contient l'id du jeu
        # (ex: "tetris", "snake"…). Sinon None.
        self.nearby_game: str | None = None

    # ═════════════════════════════════════════════════════════════════════════

    def update(self) -> None:
        self.check_input()
        self.check_move()
        super().update()

    # ─── Déplacement ──────────────────────────────────────────────────────────

    def check_move(self) -> None:
        # Réinitialise la détection de proximité à chaque frame
        self.nearby_game = None

        if self.animation_walk is False:
            temp_hitbox = self.hitbox.copy()

            if self.keylistener.key_pressed(pygame.K_LEFT):
                temp_hitbox.x -= 16
                if not self.check_collisions(temp_hitbox):
                    self._check_triggers(temp_hitbox)
                    self.move_left()
                else:
                    self.direction = "left"

            elif self.keylistener.key_pressed(pygame.K_RIGHT):
                temp_hitbox.x += 16
                if not self.check_collisions(temp_hitbox):
                    self._check_triggers(temp_hitbox)
                    self.move_right()
                else:
                    self.direction = "right"

            elif self.keylistener.key_pressed(pygame.K_UP):
                temp_hitbox.y -= 16
                if not self.check_collisions(temp_hitbox):
                    self._check_triggers(temp_hitbox)
                    self.move_up()
                else:
                    self.direction = "up"

            elif self.keylistener.key_pressed(pygame.K_DOWN):
                temp_hitbox.y += 16
                if not self.check_collisions(temp_hitbox):
                    self._check_triggers(temp_hitbox)
                    self.move_down()
                else:
                    self.direction = "down"

            else:
                # Même immobile, vérifie la proximité (hitbox actuelle élargie)
                probe = self.hitbox.inflate(8, 8)
                self._check_proximity(probe)

    # ─── Détection des zones déclencheurs ────────────────────────────────────

    def _check_triggers(self, temp_hitbox: pygame.Rect) -> None:
        """Appelé pendant le mouvement : dispatch switch-map vs jeu."""
        if self.change:
            for trigger in self.change:
                if trigger.check_collision(temp_hitbox):
                    if trigger.type == "switch":
                        self.change_map = trigger
                    elif trigger.type == "game":
                        # On ne lance pas directement : on signale la proximité
                        # La touche E dans Game._handle_event() déclenchera le lancement
                        self.nearby_game = trigger.name  # ex: "tetris"

    def _check_proximity(self, probe: pygame.Rect) -> None:
        """Détecte les portes de jeu à portée même sans déplacement actif."""
        if self.change:
            for trigger in self.change:
                if trigger.type == "game" and trigger.check_collision(probe):
                    self.nearby_game = trigger.name
                    return

    # ─── Gestion des listes de déclencheurs / collisions ─────────────────────

    def add_switchs(self, change: list[Change]) -> None:
        self.change = change

    def add_collisions(self, collisions: list[pygame.Rect]) -> None:
        self.collisions = collisions

    def check_collisions(self, temp_hitbox: pygame.Rect) -> bool:
        for collision in self.collisions:
            if temp_hitbox.colliderect(collision):
                return True
        return False

    # ─── Vélo ─────────────────────────────────────────────────────────────────

    def check_input(self) -> None:
        if self.keylistener.key_pressed(pygame.K_b):
            self.switch_bike()

    def switch_bike(self, deactive: bool = False) -> None:
        if self.speed == 1 and not deactive:
            self.speed = 2
            self.all_images = self.get_all_images(self.spritesheet_bike)
        else:
            self.speed = 1
            self.all_images = self.get_all_images(self.spritesheet)
        self.keylistener.remove_key(pygame.K_b)
