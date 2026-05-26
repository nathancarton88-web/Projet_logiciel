import pygame

from entity import Entity, MODE_WALK, MODE_BIKE, MODE_RUN, MODE_SURF
from keylistener import KeyListener
from screen import Screen
from change import Change

# ── Couleurs menu ingame ──────────────────────────────────────────────────────
_NOIR   = (4,   4,  12)
_BLANC  = (255, 255, 255)
_CYAN   = (0,   220, 255)
_JAUNE  = (255, 220,   0)
_GRIS   = (120, 120, 140)
_PANEL  = (18,  18,  28)
_BORD   = (50,  50,  80)
_ROUGE  = (255,  60,  50)

_f_title = None
_f_mid   = None
_f_small = None

def _get_fonts():
    global _f_title, _f_mid, _f_small
    if _f_title is None:
        try:
            _f_title = pygame.font.SysFont("Consolas", 28, bold=True)
            _f_mid   = pygame.font.SysFont("Consolas", 20, bold=True)
            _f_small = pygame.font.SysFont("Consolas", 16)
        except Exception:
            _f_title = pygame.font.Font(None, 32)
            _f_mid   = pygame.font.Font(None, 24)
            _f_small = pygame.font.Font(None, 20)
# Libellés des jeux pour l'affichage
_GAME_LABELS = {
    "tetris": "TETRIS FOREVER",
    "pacman": "PAC-MAN NEON",
    "snake":  "SNAKE NEON",
    "space":  "SPACE INVADERS",
}


class Player(Entity):
    def __init__(self, keylistener: KeyListener, screen: Screen, x: int, y: int):
        super().__init__(keylistener, screen, x, y)
        self.pokedollars: int = 0

        # Chemins surf / run (pour le skin sélectionné, injectés par game.py)
        # Les spritesheets sont déjà chargés dans Entity via SKIN_RUN / SKIN_SURF

        self.change:       list[Change] | None = None
        self.collisions:   list[pygame.Rect] | None = None
        self.water_zones:  list[pygame.Rect] = []   # zones déclenchant le surf
        self.change_map:   Change | None = None
        self.nearby_game:  str | None = None

        # ── Menu ingame ───────────────────────────────────────────────────────
        self.show_menu:    bool  = False
        self.menu_sel:     int   = 0
        self._menu_opts    = ["Scores", "Quitter vers menu", "Fermer"]
        self._highscores:  dict  = {}   # injecté par game.py

        # ── Surf ──────────────────────────────────────────────────────────────
        self._on_water:    bool  = False

    # ══════════════════════════════════════════════════════════════════════════
    # Update
    # ══════════════════════════════════════════════════════════════════════════

    def update(self) -> None:
        if not self.show_menu:
            self.check_input()
            self.check_move()
        super().update()

    # ══════════════════════════════════════════════════════════════════════════
    # Input
    # ══════════════════════════════════════════════════════════════════════════

    def check_input(self) -> None:
        # Vélo : B
        if self.keylistener.key_pressed(pygame.K_b):
            if self.mode == MODE_BIKE:
                self.switch_walk()
            elif self.mode == MODE_WALK or self.mode == MODE_RUN:
                self.switch_bike()
                self.switch_run(deactive=True)  # désactive run si actif
            self.keylistener.remove_key(pygame.K_b)

        # Course : R  (seulement hors eau, hors vélo)
        if self.keylistener.key_pressed(pygame.K_r):
            if self.mode == MODE_RUN:
                self.switch_walk()
            elif self.mode == MODE_WALK:
                self.switch_run()
            self.keylistener.remove_key(pygame.K_r)

        # Surf : S  (seulement si sur une zone eau)
        if self.keylistener.key_pressed(pygame.K_s):
            if self.mode == MODE_SURF:
                self.switch_walk()
            elif self._on_water and self.mode == MODE_WALK:
                self.switch_surf()
            self.keylistener.remove_key(pygame.K_s)

    # ══════════════════════════════════════════════════════════════════════════
    # Mouvement & déclencheurs
    # ══════════════════════════════════════════════════════════════════════════

    def check_move(self) -> None:
        self.nearby_game = None
        self._on_water   = self._check_water(self.hitbox)

        # Si on quitte l'eau sans être en surf → retour marche
        if not self._on_water and self.mode == MODE_SURF:
            self.switch_walk()

        if self.animation_walk:
            return

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
            self._check_proximity(self.hitbox.inflate(8, 8))

    # ── Détection eau ─────────────────────────────────────────────────────────

    def _check_water(self, hb: pygame.Rect) -> bool:
        for z in self.water_zones:
            if hb.colliderect(z):
                return True
        return False

    # ── Déclencheurs ──────────────────────────────────────────────────────────

    def _check_triggers(self, temp_hitbox: pygame.Rect) -> None:
        if not self.change:
            return
        for trigger in self.change:
            if trigger.check_collision(temp_hitbox):
                if trigger.type == "switch":
                    self.change_map = trigger
                elif trigger.type == "game":
                    self.nearby_game = trigger.name

    def _check_proximity(self, probe: pygame.Rect) -> None:
        if not self.change:
            return
        for trigger in self.change:
            if trigger.type == "game" and trigger.check_collision(probe):
                self.nearby_game = trigger.name
                return

    # ── Collisions ────────────────────────────────────────────────────────────

    def add_switchs(self, change: list[Change]) -> None:
        self.change = change

    def add_collisions(self, collisions: list[pygame.Rect]) -> None:
        self.collisions = collisions

    def add_water_zones(self, zones: list[pygame.Rect]) -> None:
        self.water_zones = zones

    def check_collisions(self, temp_hitbox: pygame.Rect) -> bool:
        # En mode surf, on ignore les collisions des zones eau
        for collision in self.collisions:
            if temp_hitbox.colliderect(collision):
                # Si c'est une zone eau et qu'on surfe, pas de collision
                if self.mode == MODE_SURF and self._check_water(temp_hitbox):
                    continue
                return True
        return False

    # ══════════════════════════════════════════════════════════════════════════
    # Menu ingame  (START / Echap ingame)
    # ══════════════════════════════════════════════════════════════════════════

    def open_menu(self) -> None:
        self.show_menu = True
        self.menu_sel  = 0

    def close_menu(self) -> None:
        self.show_menu = False

    def menu_up(self) -> None:
        self.menu_sel = (self.menu_sel - 1) % len(self._menu_opts)

    def menu_down(self) -> None:
        self.menu_sel = (self.menu_sel + 1) % len(self._menu_opts)

    def menu_confirm(self) -> str:
        """Retourne l'action choisie : 'scores' | 'quit_menu' | 'close'"""
        choice = self._menu_opts[self.menu_sel]
        if choice == "Scores":
            return "scores"
        elif choice == "Quitter vers menu":
            return "quit_menu"
        else:
            self.close_menu()
            return "close"

    def draw_ingame_menu(self, display: pygame.Surface, highscores: dict) -> None:
        """Dessine le menu pause par-dessus l'écran."""
        _get_fonts()
        W, H = display.get_size()

        # Fond semi-transparent
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        display.blit(overlay, (0, 0))

        # Panneau central
        pw, ph = 460, 380
        px, py = W // 2 - pw // 2, H // 2 - ph // 2
        pygame.draw.rect(display, _PANEL,  (px, py, pw, ph), border_radius=10)
        pygame.draw.rect(display, _CYAN,   (px, py, pw, ph), 2, border_radius=10)

        # Titre style console rétro
        title = _f_title.render("══  MENU  ══", True, _CYAN)
        display.blit(title, (px + pw // 2 - title.get_width() // 2, py + 18))
        pygame.draw.line(display, _BORD, (px + 20, py + 56), (px + pw - 20, py + 56), 1)

        # ── Scores ────────────────────────────────────────────────────────────
        sy = py + 70
        hs_label = _f_mid.render("[ MEILLEURS SCORES ]", True, _JAUNE)
        display.blit(hs_label, (px + pw // 2 - hs_label.get_width() // 2, sy))
        sy += 30

        for gid, label in _GAME_LABELS.items():
            score = highscores.get(gid, 0)
            bar_w = min(int(score / 10), pw - 80)   # barre proportionnelle (max 10 000)
            # Fond barre
            pygame.draw.rect(display, (30, 30, 50), (px + 30, sy + 18, pw - 60, 10), border_radius=4)
            # Barre remplie
            color = [_CYAN, _JAUNE, (100, 255, 100), (255, 100, 100)][list(_GAME_LABELS).index(gid)]
            if bar_w > 0:
                pygame.draw.rect(display, color, (px + 30, sy + 18, bar_w, 10), border_radius=4)
            # Texte
            line = _f_small.render(f"{label:<20} {score:>6} pts", True, _BLANC)
            display.blit(line, (px + 30, sy))
            sy += 34

        pygame.draw.line(display, _BORD, (px + 20, sy + 4), (px + pw - 20, sy + 4), 1)
        sy += 14

        # ── Options ───────────────────────────────────────────────────────────
        for i, opt in enumerate(self._menu_opts):
            selected = i == self.menu_sel
            col  = _JAUNE if selected else _GRIS
            prefix = "-> " if selected else "  "
            txt  = _f_mid.render(prefix + opt, True, col)
            if selected:
                pygame.draw.rect(display, (30, 30, 55),
                                 (px + 20, sy - 2, pw - 40, 26), border_radius=4)
            display.blit(txt, (px + pw // 2 - txt.get_width() // 2, sy))
            sy += 30

        # Hint
        hint = _f_small.render("↑ ↓  Naviguer   Entrée  Valider   Echap  Fermer",
                                True, _GRIS)
        display.blit(hint, (px + pw // 2 - hint.get_width() // 2, py + ph - 24))

        # Indicateur de mode actuel
        mode_txt = {
            MODE_WALK: "[ MARCHE ]",
            MODE_BIKE: "[ VELO   ]",
            MODE_RUN:  "[ COURSE ]",
            MODE_SURF: "[ SURF   ]",
        }.get(self.mode, "")
        ms = _f_small.render(mode_txt, True, _CYAN)
        display.blit(ms, (px + pw - ms.get_width() - 14, py + 18))
