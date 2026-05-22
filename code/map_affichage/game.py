import pygame
from keylistener import KeyListener
from map import Map
from player import Player
from screen import Screen
from jeux.tetris import Tetris
from jeux.pacman import Pacman
from jeux.snake import SnakeNeon
from jeux.space_invader import SpaceInvaders
import json, os

# ─── Highscores ──────────────────────────────────────────────────────────────
_HS_FILE = "scores.json"

def load_hs():
    try:
        if os.path.exists(_HS_FILE):
            with open(_HS_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return {"tetris": 0, "pacman": 0, "snake": 0, "space": 0}

def save_hs(d):
    try:
        with open(_HS_FILE, "w") as f:
            json.dump(d, f)
    except Exception:
        pass


# ─── Constantes affichage jeu ─────────────────────────────────────────────────
# La zone de jeu interne (700×500) est centrée dans la fenêtre 1280×720
GW, GH   = 700, 500   # dimensions de la surface interne des mini-jeux
GX, GY   = 290, 110   # position de cette surface sur l'écran principal

NOIR = (0, 0, 0)
BLANC = (255, 255, 255)
CYAN  = (0, 255, 255)

try:
    font_ui = pygame.font.SysFont("Segoe UI", 26, bold=True)
    font_hud = pygame.font.SysFont("Consolas", 20)
except Exception:
    font_ui = pygame.font.Font(None, 30)
    font_hud = pygame.font.Font(None, 22)


# ─── Jeux disponibles ─────────────────────────────────────────────────────────
GAME_REGISTRY = {
    "tetris": {"class": Tetris,        "label": "Tetris Forever",  "color": (130, 0, 255)},
    "pacman": {"class": Pacman,        "label": "Pac-Man Neon",    "color": (255, 215, 0)},
    "snake":  {"class": SnakeNeon,     "label": "Snake Neon",      "color": (0, 170, 80)},
    "space":  {"class": SpaceInvaders, "label": "Space Invaders",  "color": (35, 80, 200)},
}

# Jeux dont update() attend un argument dt
NEEDS_DT = {"tetris", "snake", "space"}


class Game:
    """
    Machine à états principale :
        MAP   → le joueur se balade sur la carte
        FADE  → transition (fondu) entre la carte et un jeu
        GAME  → un mini-jeu est actif
    """

    def __init__(self):
        pygame.init()

        # ── Carte & joueur ────────────────────────────────────────────────────
        self.screen     = Screen()
        self.map        = Map(self.screen)
        self.keylistener= KeyListener()
        self.player     = Player(self.keylistener, self.screen, 512, 288)
        self.map.add_player(self.player)

        # ── État global ───────────────────────────────────────────────────────
        self.state      = "MAP"      # "MAP" | "FADE_IN" | "GAME" | "FADE_OUT"
        self.fade_alpha = 0          # 0..255
        self.fade_dir   = 1          # +1 = assombrir, -1 = éclaircir
        self.fade_speed = 12

        # ── Mini-jeu courant ──────────────────────────────────────────────────
        self.current_game    = None
        self.current_game_id = None
        self.highscores      = load_hs()

        # ── Overlay de fondu (réutilisé) ──────────────────────────────────────
        self.fade_surf = pygame.Surface((GW, GH), pygame.SRCALPHA)

        # ── Indicateur d'interaction (pression E) ─────────────────────────────
        self.prompt_alpha = 0
        self.prompt_dir   = 1

    # ═════════════════════════════════════════════════════════════════════════
    # Boucle principale
    # ═════════════════════════════════════════════════════════════════════════
    def run(self) -> None:
        running = True
        while running:
            dt = self.screen.clock.tick(60)

            # ── Événements ────────────────────────────────────────────────────
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    save_hs(self.highscores)
                    pygame.quit()
                    return
                self._handle_event(event, dt)

            # ── Logique ───────────────────────────────────────────────────────
            self._update(dt)

            # ── Rendu ─────────────────────────────────────────────────────────
            self._draw()
            self.screen.update()

    # ═════════════════════════════════════════════════════════════════════════
    # Gestion des événements
    # ═════════════════════════════════════════════════════════════════════════
    def _handle_event(self, event, dt) -> None:
        if event.type == pygame.KEYDOWN:

            # Quitter un mini-jeu (Échap)
            if self.state == "GAME" and event.key == pygame.K_ESCAPE:
                self._start_fade_out()
                return

            # Entrée dans un bâtiment (touche E près d'une porte)
            if self.state == "MAP" and event.key == pygame.K_e:
                if self.player.nearby_game:
                    self._start_fade_in(self.player.nearby_game)
                return

            # Entrées du mini-jeu actif
            if self.state == "GAME":
                self._handle_game_input(event)
                return

            # Entrées carte
            if self.state == "MAP":
                self.keylistener.add_key(event.key)

        elif event.type == pygame.KEYUP:
            if self.state == "MAP":
                self.keylistener.remove_key(event.key)

    # ═════════════════════════════════════════════════════════════════════════
    # Mise à jour
    # ═════════════════════════════════════════════════════════════════════════
    def _update(self, dt: int) -> None:

        if self.state == "MAP":
            self.map.update()
            # Vérifier si le joueur a aussi déclenché une transition de map
            if self.player.change_map and self.player.step >= 8:
                # laissé à Map.update(), on ne fait rien de spécial ici
                pass
            # Animer le prompt "Appuie sur E"
            if self.player.nearby_game:
                self.prompt_alpha += self.prompt_dir * 4
                if self.prompt_alpha >= 255 or self.prompt_alpha <= 0:
                    self.prompt_dir *= -1
                self.prompt_alpha = max(0, min(255, self.prompt_alpha))
            else:
                self.prompt_alpha = 0

        elif self.state == "FADE_IN":
            # Fondu vers le noir → puis lancer le jeu
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
                # Sauvegarde du highscore si game over
                if g.game_over:
                    key = self.current_game_id
                    if g.score > self.highscores.get(key, 0):
                        self.highscores[key] = g.score
                        save_hs(self.highscores)

        elif self.state == "FADE_OUT":
            # Fondu vers le noir → puis retour à la carte
            self.fade_alpha = min(255, self.fade_alpha + self.fade_speed)
            if self.fade_alpha >= 255:
                self.current_game    = None
                self.current_game_id = None
                self.state = "FADE_BACK"
                self.fade_alpha = 255

        elif self.state == "FADE_BACK":
            # Fondu depuis le noir → carte visible
            self.fade_alpha = max(0, self.fade_alpha - self.fade_speed)
            if self.fade_alpha <= 0:
                self.state = "MAP"

    # ═════════════════════════════════════════════════════════════════════════
    # Rendu
    # ═════════════════════════════════════════════════════════════════════════
    def _draw(self) -> None:
        display = self.screen.get_display()

        if self.state in ("MAP", "FADE_IN", "FADE_BACK"):
            # La carte se dessine normalement via map.update()
            # (map.update() draw sur screen.get_display())
            if self.state != "MAP":
                self.map.update()   # redessine la carte pendant la transition

            # Prompt "Appuie sur E"
            if self.state == "MAP" and self.player.nearby_game:
                self._draw_prompt(display)

            # Fondu par-dessus la carte
            if self.state in ("FADE_IN", "FADE_BACK"):
                ov = pygame.Surface(display.get_size(), pygame.SRCALPHA)
                ov.fill((0, 0, 0, self.fade_alpha))
                display.blit(ov, (0, 0))

        elif self.state in ("GAME", "FADE_OUT"):
            # Surface interne du mini-jeu
            inner = pygame.Surface((GW, GH))
            inner.fill((5, 5, 10))

            if self.current_game:
                self.current_game.draw(inner)

            # Bord décoratif autour de la fenêtre de jeu
            display.fill((15, 15, 20))
            pygame.draw.rect(display, (40, 40, 50), (GX - 4, GY - 4, GW + 8, GH + 8), border_radius=6)
            display.blit(inner, (GX, GY))

            # HUD : nom du jeu + highscore + touche Échap
            if self.current_game_id and self.current_game_id in GAME_REGISTRY:
                info = GAME_REGISTRY[self.current_game_id]
                lbl  = font_ui.render(info["label"], True, info["color"])
                display.blit(lbl, (GX, GY - 36))
                hs   = self.highscores.get(self.current_game_id, 0)
                hs_t = font_hud.render(f"BEST : {hs}", True, (200, 200, 100))
                display.blit(hs_t, (GX + GW - hs_t.get_width(), GY - 30))
                esc_t = font_hud.render("[ Échap ] Retour à la carte", True, (100, 100, 120))
                display.blit(esc_t, (GX, GY + GH + 8))

            # Fondu de sortie
            if self.state == "FADE_OUT":
                ov = pygame.Surface((GW, GH), pygame.SRCALPHA)
                ov.fill((0, 0, 0, self.fade_alpha))
                display.blit(ov, (GX, GY))

    def _draw_prompt(self, display) -> None:
        """Bulle 'E' qui pulse au-dessus du joueur pour indiquer une porte de jeu."""
        txt = font_hud.render("[ E ] Jouer", True, BLANC)
        surf = pygame.Surface((txt.get_width() + 16, txt.get_height() + 10), pygame.SRCALPHA)
        surf.fill((20, 20, 30, self.prompt_alpha))
        surf.blit(txt, (8, 5))
        # Position : au-dessus du joueur (coordonnées écran = position carte + offset caméra)
        # On l'affiche en haut de l'écran pour simplifier (sans accès facile aux coords caméra)
        display.blit(surf, (self.screen.get_size()[0] // 2 - surf.get_width() // 2, 20))

    # ═════════════════════════════════════════════════════════════════════════
    # Transitions
    # ═════════════════════════════════════════════════════════════════════════
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

    # ═════════════════════════════════════════════════════════════════════════
    # Entrées mini-jeu
    # ═════════════════════════════════════════════════════════════════════════
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
            if event.key == pygame.K_LEFT:  g.next_dir = [-1, 0]
            if event.key == pygame.K_RIGHT: g.next_dir = [1,  0]

        elif gid == "snake":
            if event.key == pygame.K_UP:    g.set_dir((0, -1))
            if event.key == pygame.K_DOWN:  g.set_dir((0,  1))
            if event.key == pygame.K_LEFT:  g.set_dir((-1, 0))
            if event.key == pygame.K_RIGHT: g.set_dir((1,  0))

        elif gid == "space":
            if event.key == pygame.K_SPACE: g.shoot()
