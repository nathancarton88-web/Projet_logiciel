"""
game.py  (version fusionnée)
────────────────────────────
Machine à états :
    MAP       → balade sur la carte TMX
    FADE_IN   → fondu noir vers le mini-jeu
    GAME      → mini-jeu actif
    FADE_OUT  → fondu noir pour quitter le mini-jeu
    FADE_BACK → fondu retour vers la carte
"""

import pygame
from keylistener import KeyListener
from map import Map
from player import Player
from screen import Screen
from jeux.tetris import Tetris
from jeux.pacman import Pacman
from jeux.snake import SnakeNeon
from jeux.space_invader import SpaceInvaders
from save_manager import write_save, skin_by_id
from entity import Entity, MODE_WALK, MODE_BIKE, MODE_RUN, MODE_SURF
import json, os

# ── Constantes affichage mini-jeux ────────────────────────────────────────────
GW, GH = 700, 500
GX, GY = 290, 110

BLANC = (255, 255, 255)
CYAN  = (0, 255, 255)
GRIS  = (100, 100, 120)

try:
    font_ui  = pygame.font.SysFont("Segoe UI", 26, bold=True)
    font_hud = pygame.font.SysFont("Consolas", 20)
except Exception:
    font_ui  = pygame.font.Font(None, 30)
    font_hud = pygame.font.Font(None, 22)

# ── Registre des mini-jeux ────────────────────────────────────────────────────
GAME_REGISTRY = {
    "tetris": {"class": Tetris,        "label": "Tetris Forever",  "color": (130,  0, 255)},
    "pacman": {"class": Pacman,        "label": "Pac-Man Neon",    "color": (255, 215,   0)},
    "snake":  {"class": SnakeNeon,     "label": "Snake Neon",      "color": (  0, 170,  80)},
    "space":  {"class": SpaceInvaders, "label": "Space Invaders",  "color": ( 35,  80, 200)},
}
NEEDS_DT = {"tetris", "snake", "space"}

# ── Musiques ──────────────────────────────────────────────────────────────────
MUSIC = {
    "map":    "assets/music/map.ogg",      # musique de la carte
    "tetris": "assets/music/tetris.ogg",   # musique pendant Tetris
    "pacman": "assets/music/pacman.ogg",
    "snake":  "assets/music/snake.ogg",
    "space":  "assets/music/space.ogg",
}


def _play_music(key: str, volume: float = 0.4):
    path = MUSIC.get(key, MUSIC.get("map", ""))
    try:
        if path and os.path.exists(path):
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(-1)
        else:
            pygame.mixer.music.stop()
    except Exception as e:
        print(f"[game] Musique '{key}' non chargée : {e}")


class Game:
    def __init__(self, save_data: dict):
        pygame.init()
        pygame.mixer.init()

        self.save_data = save_data          # dict complet de la sauvegarde

        # ── Écran ─────────────────────────────────────────────────────────────
        self.screen = Screen()

        # ── Résoudre le skin ──────────────────────────────────────────────────
        skin = skin_by_id(save_data.get("skin", ""))
        # On injecte les chemins dans les classes Entity/Player via attributs de classe

        from entity import Entity
        Entity.SKIN_WALK = skin["walk"]
        Entity.SKIN_BIKE = skin["bike"]
        Entity.SKIN_RUN = skin["run"]
        Entity.SKIN_SURF = skin["surf"]

        # ── Carte & joueur ────────────────────────────────────────────────────
        px, py   = save_data.get("position", [512, 288])
        map_name = save_data.get("map",      "map_0")

        self.keylistener = KeyListener()
        self.player      = Player(self.keylistener, self.screen, px, py)
        self.map         = Map(self.screen, initial_map=map_name)
        self.map.add_player(self.player)

        # ── État ──────────────────────────────────────────────────────────────
        self.state      = "MAP"
        self.fade_alpha = 0
        self.fade_speed = 12

        # ── Mini-jeu ──────────────────────────────────────────────────────────
        self.current_game    = None
        self.current_game_id = None

        # ── Prompt E ─────────────────────────────────────────────────────────
        self.prompt_alpha = 0
        self.prompt_dir   = 1

        # ── Musique carte ─────────────────────────────────────────────────────
        _play_music("map")

        # ── Sauvegarde auto toutes les 30 s ───────────────────────────────────
        self._autosave_timer = 0

        # ── Flag retour menu principal ────────────────────────────────────────
        self._return_to_main_menu = False

    # ══════════════════════════════════════════════════════════════════════════
    # Boucle principale
    # ══════════════════════════════════════════════════════════════════════════
    def run(self) -> None:
        while True:
            dt = self.screen.clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._save_position()
                    pygame.quit()
                    return
                self._handle_event(event)

            self._update(dt)
            self._draw()
            self.screen.update()

            if self._return_to_main_menu:
                return  # remonte dans main2.py qui relancera le menu

            # Auto-save toutes les 30 secondes
            self._autosave_timer += dt
            if self._autosave_timer >= 30_000:
                self._autosave_timer = 0
                self._save_position()

    # ══════════════════════════════════════════════════════════════════════════
    # Sauvegarde
    # ══════════════════════════════════════════════════════════════════════════
    def _save_position(self):
        """Met à jour position + map dans save_data puis écrit sur disque."""
        pos  = [int(self.player.position.x), int(self.player.position.y)]
        mmap = self.map.current_map.name if self.map.current_map else "map_0"
        self.save_data["position"]   = pos
        self.save_data["map"]        = mmap
        self.save_data["highscores"] = self.save_data.get("highscores", {})
        write_save(self.save_data)

    def _update_highscore(self, game_id: str, score: int):
        hs = self.save_data.setdefault("highscores", {})
        if score > hs.get(game_id, 0):
            hs[game_id] = score
            write_save(self.save_data)

    # ══════════════════════════════════════════════════════════════════════════
    # Événements
    # ══════════════════════════════════════════════════════════════════════════
    def _handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN:
            k = event.key

            # ── Menu ingame (touche M ou START) ───────────────────────────────
            if self.state == "MAP" and k == pygame.K_m:
                if self.player.show_menu:
                    self.player.close_menu()
                else:
                    self.player._highscores = self.save_data.get("highscores", {})
                    self.player.open_menu()
                return

            # Navigation dans le menu ingame
            if self.state == "MAP" and self.player.show_menu:
                if k == pygame.K_ESCAPE:
                    self.player.close_menu()
                elif k == pygame.K_UP:
                    self.player.menu_up()
                elif k == pygame.K_DOWN:
                    self.player.menu_down()
                elif k == pygame.K_RETURN:
                    action = self.player.menu_confirm()
                    if action == "quit_menu":
                        self._save_position()
                        self._return_to_main_menu = True
                return

            # ── Mini-jeu : Échap ──────────────────────────────────────────────
            if self.state == "GAME" and k == pygame.K_ESCAPE:
                self._start_fade_out()
                return

            # ── Entrer dans un jeu : E ────────────────────────────────────────
            if self.state == "MAP" and k == pygame.K_e:
                if self.player.nearby_game:
                    self._start_fade_in(self.player.nearby_game)
                return

            # ── Inputs mini-jeu ───────────────────────────────────────────────
            if self.state == "GAME":
                self._handle_game_input(event)
                return

            # ── Inputs carte (R, S, B, flèche) ─────────────────────────────
            if self.state == "MAP":
                # Touches toggle — gérées ici directement
                if k == pygame.K_b:
                    if self.player.mode == MODE_BIKE:
                        self.player.switch_walk()
                    else:
                        self.player.switch_bike()
                elif k == pygame.K_r:
                    if self.player.mode == MODE_RUN:
                        self.player.switch_walk()
                    else:
                        self.player.switch_run()
                elif k == pygame.K_s:
                    if self.player.mode == MODE_SURF:
                        self.player.switch_walk()
                    elif self.player._on_water:
                        self.player.switch_surf()
                else:
                    self.keylistener.add_key(k)  # flèches et autres touches maintenues

        elif event.type == pygame.KEYUP:
            if self.state == "MAP":
                self.keylistener.remove_key(event.key)

    # ══════════════════════════════════════════════════════════════════════════
    # Mise à jour
    # ══════════════════════════════════════════════════════════════════════════
    def _update(self, dt: int) -> None:

        if self.state == "MAP":
            self.map.update()
            if self.player.nearby_game:
                self.prompt_alpha = min(255, self.prompt_alpha + self.prompt_dir * 4)
                if self.prompt_alpha >= 255 or self.prompt_alpha <= 0:
                    self.prompt_dir *= -1
            else:
                self.prompt_alpha = 0

        elif self.state == "FADE_IN":
            self.fade_alpha = min(255, self.fade_alpha + self.fade_speed)
            if self.fade_alpha >= 255:
                self._launch_game(self._pending_game_id)
                self.state = "GAME"

        elif self.state == "GAME":
            g = self.current_game
            if g:
                if self.current_game_id in NEEDS_DT:
                    g.update(dt)
                else:
                    g.update()
                if g.game_over:
                    self._update_highscore(self.current_game_id, g.score)

        elif self.state == "FADE_OUT":
            self.fade_alpha = min(255, self.fade_alpha + self.fade_speed)
            if self.fade_alpha >= 255:
                self.current_game    = None
                self.current_game_id = None
                self.state      = "FADE_BACK"
                self.fade_alpha = 255
                _play_music("map")      # ← reprend la musique de la carte

        elif self.state == "FADE_BACK":
            self.fade_alpha = max(0, self.fade_alpha - self.fade_speed)
            if self.fade_alpha <= 0:
                self.state = "MAP"
                self._save_position()   # ← sauvegarde à chaque retour sur la carte

    # ══════════════════════════════════════════════════════════════════════════
    # Rendu
    # ══════════════════════════════════════════════════════════════════════════
    def _draw(self) -> None:
        display = self.screen.get_display()

        if self.state in ("MAP", "FADE_IN", "FADE_BACK"):
            if self.state != "MAP":
                self.map.update()
            if self.state == "MAP" and self.player.nearby_game:
                self._draw_prompt(display)
            # Menu ingame
            if self.state == "MAP" and self.player.show_menu:
                self.player.draw_ingame_menu(display,
                    self.save_data.get("highscores", {}))
            if self.state in ("FADE_IN", "FADE_BACK"):
                ov = pygame.Surface(display.get_size(), pygame.SRCALPHA)
                ov.fill((0, 0, 0, self.fade_alpha))
                display.blit(ov, (0, 0))

        elif self.state in ("GAME", "FADE_OUT"):
            inner = pygame.Surface((GW, GH))
            inner.fill((5, 5, 10))
            if self.current_game:
                self.current_game.draw(inner)

            display.fill((15, 15, 20))
            pygame.draw.rect(display, (40, 40, 50),
                             (GX - 4, GY - 4, GW + 8, GH + 8), border_radius=6)
            display.blit(inner, (GX, GY))

            if self.current_game_id in GAME_REGISTRY:
                info = GAME_REGISTRY[self.current_game_id]
                lbl  = font_ui.render(info["label"], True, info["color"])
                display.blit(lbl, (GX, GY - 36))
                hs   = self.save_data.get("highscores", {}).get(self.current_game_id, 0)
                hs_t = font_hud.render(f"BEST : {hs}", True, (200, 200, 100))
                display.blit(hs_t, (GX + GW - hs_t.get_width(), GY - 30))
                esc_t = font_hud.render("[ Echap ] Retour à la carte", True, GRIS)
                display.blit(esc_t, (GX, GY + GH + 8))
                # Nom du joueur
                pn = font_hud.render(
                    f"Joueur : {self.save_data.get('player_name', '?')}", True, GRIS)
                display.blit(pn, (GX, GY + GH + 28))

            if self.state == "FADE_OUT":
                ov = pygame.Surface((GW, GH), pygame.SRCALPHA)
                ov.fill((0, 0, 0, self.fade_alpha))
                display.blit(ov, (GX, GY))

    def _draw_prompt(self, display) -> None:
        txt  = font_hud.render("[ E ]  pour Jouer", True, BLANC)
        surf = pygame.Surface((txt.get_width() + 16, txt.get_height() + 10), pygame.SRCALPHA)
        safe_alpha = max(0, min(255, int(self.prompt_alpha)))

        surf.fill((20, 20, 30, safe_alpha))
        surf.blit(txt, (8, 5))
        display.blit(surf, (self.screen.get_size()[0] // 2 - surf.get_width() // 2, 20))

    # ══════════════════════════════════════════════════════════════════════════
    # Transitions
    # ══════════════════════════════════════════════════════════════════════════
    def _start_fade_in(self, game_id: str) -> None:
        self._pending_game_id = game_id
        self.fade_alpha = 0
        self.state = "FADE_IN"
        self.keylistener.clear()

    def _start_fade_out(self) -> None:
        self.fade_alpha = 0
        self.state = "FADE_OUT"

    def _launch_game(self, game_id: str) -> None:
        info = GAME_REGISTRY.get(game_id)
        if not info:
            self.state = "MAP"
            return
        self.current_game    = info["class"]()
        self.current_game_id = game_id
        _play_music(game_id)            # ← musique spécifique au jeu

    # ══════════════════════════════════════════════════════════════════════════
    # Inputs mini-jeux
    # ══════════════════════════════════════════════════════════════════════════
    def _handle_game_input(self, event) -> None:
        g   = self.current_game
        gid = self.current_game_id
        if not g or not gid:
            return

        if gid == "tetris":
            t = g
            if event.key == pygame.K_LEFT  and not t.collide(dx=-1): t.cur['x'] -= 1
            if event.key == pygame.K_RIGHT and not t.collide(dx=1):  t.cur['x'] += 1
            if event.key == pygame.K_DOWN  and not t.collide(dy=1):  t.cur['y'] += 1
            if event.key == pygame.K_UP:
                rot = t.rotate(t.cur['shape'])
                if not t.collide(shape=rot): t.cur['shape'] = rot
            if event.key == pygame.K_SPACE:
                t.cur['y'] = t.ghost_y(); t._lock()

        elif gid == "pacman":
            if event.key == pygame.K_UP:    g.next_dir = [0, -1]
            if event.key == pygame.K_DOWN:  g.next_dir = [0,  1]
            if event.key == pygame.K_LEFT:  g.next_dir = [-1,  0]
            if event.key == pygame.K_RIGHT: g.next_dir = [1,   0]

        elif gid == "snake":
            if event.key == pygame.K_UP:    g.set_dir((0, -1))
            if event.key == pygame.K_DOWN:  g.set_dir((0,  1))
            if event.key == pygame.K_LEFT:  g.set_dir((-1,  0))
            if event.key == pygame.K_RIGHT: g.set_dir((1,   0))

        elif gid == "space":
            if event.key == pygame.K_SPACE: g.shoot()
