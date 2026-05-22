"""
menu.py
───────
Menu principal affiché au lancement du jeu.

États internes :
    MAIN      → choix Nouveau / Continuer / Quitter
    SELECT    → liste des sauvegardes existantes
    NEW_NAME  → saisie du nom du nouveau joueur
    SKIN      → choix du skin (avant de créer la partie)
"""

import pygame
from save_manager import list_saves, load_save, new_save, SKINS, skin_by_id

# ── Couleurs ──────────────────────────────────────────────────────────────────
NOIR      = (8,  8, 14)
BLANC     = (255, 255, 255)
GRIS      = (130, 130, 150)
CYAN      = (0,  220, 255)
JAUNE     = (255, 220,  0)
ROUGE     = (255,  60,  50)
FOND      = (14,  14,  22)
PANEL     = (22,  22,  34)
BORDURE   = (50,  50,  75)

# ── Polices ───────────────────────────────────────────────────────────────────
def _fonts():
    try:
        return {
            "title":  pygame.font.SysFont("Segoe UI", 58, bold=True),
            "big":    pygame.font.SysFont("Segoe UI", 34, bold=True),
            "mid":    pygame.font.SysFont("Segoe UI", 26, bold=True),
            "small":  pygame.font.SysFont("Consolas", 20),
        }
    except Exception:
        return {
            "title":  pygame.font.Font(None, 68),
            "big":    pygame.font.Font(None, 40),
            "mid":    pygame.font.Font(None, 30),
            "small":  pygame.font.Font(None, 24),
        }


class MainMenu:
    """
    Appelle menu.run(screen) → retourne un dict de sauvegarde ou None (quitter).
    """

    MAIN_OPTIONS  = ["Nouvelle partie", "Continuer", "Quitter"]
    MUSIC_FILE    = "assets/music/menu.ogg"

    def __init__(self, screen_surface: pygame.Surface):
        self.surf   = screen_surface
        self.W, self.H = screen_surface.get_size()
        self.fonts  = _fonts()
        self.state  = "MAIN"        # MAIN | SELECT | NEW_NAME | SKIN
        self.result = None          # dict sauvegarde retourné à Game
        self.running= True

        # Navigation menu principal
        self.main_sel   = 0

        # Navigation liste sauvegardes
        self.saves      = []
        self.save_sel   = 0

        # Saisie nom
        self.input_text = ""
        self.input_err  = ""

        # Choix skin
        self.skin_sel   = 0
        self.skin_previews: dict[str, pygame.Surface] = {}
        self._load_skin_previews()

        # Particules fond
        import random
        self.stars = [
            {"x": random.randint(0, self.W), "y": random.randint(0, self.H),
             "r": random.uniform(1, 2.5), "b": random.randint(80, 200)}
            for _ in range(120)
        ]

        # Musique
        self._start_music()

    # ── Musique ───────────────────────────────────────────────────────────────

    def _start_music(self):
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(self.MUSIC_FILE)
            pygame.mixer.music.set_volume(0.45)
            pygame.mixer.music.play(-1)   # -1 = boucle infinie
        except Exception as e:
            print(f"[menu] Musique non chargée : {e}")

    def stop_music(self):
        try:
            pygame.mixer.music.fadeout(800)
        except Exception:
            pass

    # ── Previews des skins ────────────────────────────────────────────────────

    def _load_skin_previews(self):
        for sk in SKINS:
            try:
                sheet = pygame.image.load(sk["walk"]).convert_alpha()
                w = sheet.get_width() // 4
                h = sheet.get_height() // 4
                # Première frame, direction bas
                frame = sheet.subsurface(pygame.Rect(0, 0, w, h))
                # Agrandie ×4 pour être visible
                big   = pygame.transform.scale(frame, (w * 4, h * 4))
                self.skin_previews[sk["id"]] = big
            except Exception:
                self.skin_previews[sk["id"]] = None

    # ── Boucle principale du menu ─────────────────────────────────────────────

    def run(self) -> dict | None:
        clock = pygame.time.Clock()
        while self.running:
            dt = clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return None
                self._handle(event)
            self._draw()
            pygame.display.flip()
            if self.result is not None:
                self.stop_music()
                return self.result
        return None

    # ── Gestion des événements ────────────────────────────────────────────────

    def _handle(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if self.state == "MAIN":
            self._handle_main(event.key)
        elif self.state == "SELECT":
            self._handle_select(event.key)
        elif self.state == "NEW_NAME":
            self._handle_name(event)
        elif self.state == "SKIN":
            self._handle_skin(event.key)

    def _handle_main(self, key):
        if key in (pygame.K_UP, pygame.K_LEFT):
            self.main_sel = (self.main_sel - 1) % len(self.MAIN_OPTIONS)
        elif key in (pygame.K_DOWN, pygame.K_RIGHT):
            self.main_sel = (self.main_sel + 1) % len(self.MAIN_OPTIONS)
        elif key == pygame.K_RETURN:
            choice = self.MAIN_OPTIONS[self.main_sel]
            if choice == "Nouvelle partie":
                self.state = "NEW_NAME"
                self.input_text = ""
                self.input_err  = ""
            elif choice == "Continuer":
                self.saves   = list_saves()
                self.save_sel = 0
                self.state   = "SELECT"
            elif choice == "Quitter":
                self.running = False

    def _handle_select(self, key):
        if not self.saves:
            if key == pygame.K_ESCAPE:
                self.state = "MAIN"
            return
        if key in (pygame.K_UP, pygame.K_LEFT):
            self.save_sel = (self.save_sel - 1) % len(self.saves)
        elif key in (pygame.K_DOWN, pygame.K_RIGHT):
            self.save_sel = (self.save_sel + 1) % len(self.saves)
        elif key == pygame.K_RETURN:
            name = self.saves[self.save_sel]
            data = load_save(name)
            if data:
                self.result = data
        elif key == pygame.K_ESCAPE:
            self.state = "MAIN"

    def _handle_name(self, event):
        key = event.key
        if key == pygame.K_ESCAPE:
            self.state = "MAIN"
        elif key == pygame.K_RETURN:
            name = self.input_text.strip()
            if len(name) < 2:
                self.input_err = "Minimum 2 caractères !"
            elif len(name) > 12:
                self.input_err = "Maximum 12 caractères !"
            else:
                # Passe au choix du skin
                self._pending_name = name
                self.skin_sel = 0
                self.state = "SKIN"
        elif key == pygame.K_BACKSPACE:
            self.input_text = self.input_text[:-1]
            self.input_err  = ""
        else:
            char = event.unicode
            if char and char.isprintable() and len(self.input_text) < 12:
                self.input_text += char
                self.input_err  = ""

    def _handle_skin(self, key):
        if key in (pygame.K_LEFT, pygame.K_UP):
            self.skin_sel = (self.skin_sel - 1) % len(SKINS)
        elif key in (pygame.K_RIGHT, pygame.K_DOWN):
            self.skin_sel = (self.skin_sel + 1) % len(SKINS)
        elif key == pygame.K_RETURN:
            skin_id = SKINS[self.skin_sel]["id"]
            self.result = new_save(self._pending_name, skin_id)
        elif key == pygame.K_ESCAPE:
            self.state = "NEW_NAME"

    # ── Rendu ─────────────────────────────────────────────────────────────────

    def _draw(self):
        self.surf.fill(FOND)
        self._draw_stars()

        if self.state == "MAIN":
            self._draw_main()
        elif self.state == "SELECT":
            self._draw_select()
        elif self.state == "NEW_NAME":
            self._draw_new_name()
        elif self.state == "SKIN":
            self._draw_skin()

    def _draw_stars(self):
        import random
        for s in self.stars:
            s["y"] -= 0.15
            if s["y"] < 0:
                s["y"] = self.H
                s["x"] = random.randint(0, self.W)
            b = int(s["b"])
            pygame.draw.circle(self.surf, (b, b, b), (int(s["x"]), int(s["y"])), int(s["r"]))

    def _draw_main(self):
        # Titre
        title = self.fonts["title"].render("◈  THE JEU  ◈", True, CYAN)
        self.surf.blit(title, (self.W // 2 - title.get_width() // 2, 120))
        sub = self.fonts["small"].render(" mini-game ", True, GRIS)
        self.surf.blit(sub, (self.W // 2 - sub.get_width() // 2, 192))

        # Options
        for i, opt in enumerate(self.MAIN_OPTIONS):
            selected = i == self.main_sel
            color  = JAUNE if selected else BLANC
            prefix = "▶  " if selected else "   "
            size   = "big" if selected else "mid"
            txt    = self.fonts[size].render(prefix + opt, True, color)
            y      = 300 + i * 70
            if selected:
                # fond mis en évidence
                pygame.draw.rect(self.surf, PANEL,
                                 (self.W//2 - 160, y - 6, 320, 48), border_radius=8)
                pygame.draw.rect(self.surf, BORDURE,
                                 (self.W//2 - 160, y - 6, 320, 48), 2, border_radius=8)
            self.surf.blit(txt, (self.W // 2 - txt.get_width() // 2, y))

        hint = self.fonts["small"].render("↑ ↓  Naviguer   Entrée  Valider", True, GRIS)
        self.surf.blit(hint, (self.W // 2 - hint.get_width() // 2, self.H - 40))

    def _draw_select(self):
        self._draw_panel("Choisir une sauvegarde", "Échap = retour")
        if not self.saves:
            msg = self.fonts["mid"].render("Aucune sauvegarde trouvée.", True, ROUGE)
            self.surf.blit(msg, (self.W // 2 - msg.get_width() // 2, self.H // 2))
            return
        for i, name in enumerate(self.saves):
            selected = i == self.save_sel
            data     = load_save(name) or {}
            hs       = data.get("highscores", {})
            best     = max(hs.values()) if hs else 0
            label    = f"{'▶ ' if selected else '  '}{name}   — meilleur score : {best}"
            color    = JAUNE if selected else BLANC
            font     = "mid" if selected else "small"
            txt      = self.fonts[font].render(label, True, color)
            y        = 220 + i * 54
            if selected:
                pygame.draw.rect(self.surf, PANEL,
                                 (self.W//2 - 280, y - 4, 560, 44), border_radius=6)
            self.surf.blit(txt, (self.W // 2 - txt.get_width() // 2, y))

    def _draw_new_name(self):
        self._draw_panel("Nouveau joueur", "Échap = retour")
        prompt = self.fonts["mid"].render("Entre ton nom :", True, BLANC)
        self.surf.blit(prompt, (self.W // 2 - prompt.get_width() // 2, 240))

        # Champ de saisie
        box_w, box_h = 360, 52
        box_x = self.W // 2 - box_w // 2
        box_y = 290
        pygame.draw.rect(self.surf, PANEL,   (box_x, box_y, box_w, box_h), border_radius=8)
        pygame.draw.rect(self.surf, CYAN,    (box_x, box_y, box_w, box_h), 2, border_radius=8)
        cursor = "_" if (pygame.time.get_ticks() // 500) % 2 == 0 else ""
        inp    = self.fonts["big"].render(self.input_text + cursor, True, BLANC)
        self.surf.blit(inp, (box_x + 14, box_y + 8))

        if self.input_err:
            err = self.fonts["small"].render(self.input_err, True, ROUGE)
            self.surf.blit(err, (self.W // 2 - err.get_width() // 2, box_y + box_h + 12))

        hint = self.fonts["small"].render("Entrée = valider", True, GRIS)
        self.surf.blit(hint, (self.W // 2 - hint.get_width() // 2, self.H - 40))

    def _draw_skin(self):
        self._draw_panel("Choisis ton personnage", "Échap = retour  |  ← → changer")
        sk   = SKINS[self.skin_sel]
        prev = self.skin_previews.get(sk["id"])

        if prev:
            px = self.W // 2 - prev.get_width() // 2
            self.surf.blit(prev, (px, 230))

        # Nom du skin
        label = self.fonts["big"].render(sk["label"], True, JAUNE)
        self.surf.blit(label, (self.W // 2 - label.get_width() // 2, 420))

        # Flèches de navigation si plusieurs skins
        if len(SKINS) > 1:
            nav = self.fonts["mid"].render(
                f"◀  {self.skin_sel + 1} / {len(SKINS)}  ▶", True, GRIS)
            self.surf.blit(nav, (self.W // 2 - nav.get_width() // 2, 460))

        conf = self.fonts["mid"].render("Entrée = choisir ce personnage", True, CYAN)
        self.surf.blit(conf, (self.W // 2 - conf.get_width() // 2, self.H - 40))

    def _draw_panel(self, title: str, hint: str):
        # Titre du panneau
        t = self.fonts["big"].render(title, True, CYAN)
        self.surf.blit(t, (self.W // 2 - t.get_width() // 2, 140))
        pygame.draw.line(self.surf, BORDURE,
                         (self.W//2 - 300, 185), (self.W//2 + 300, 185), 1)
        # Hint bas
        h = self.fonts["small"].render(hint, True, GRIS)
        self.surf.blit(h, (self.W // 2 - h.get_width() // 2, self.H - 40))
