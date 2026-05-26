"""
menu.py  —  Menu principal style console rétro
"""

import pygame, math, random
from save_manager import list_saves, load_save, new_save, SKINS, skin_by_id

NOIR    = (4,    4,   8)
BLANC   = (220, 220, 220)
VERT    = (0,   255, 80)
CYAN    = (0,   220, 255)
JAUNE   = (255, 220,  0)
ROUGE   = (255,  50, 50)
GRIS    = (80,   80, 100)
PANEL   = (10,   10,  18)
BORD    = (0,   180,  60)

MUSIC_FILE = "assets/music/menu.ogg"


def _fonts():
    try:
        return {
            "title": pygame.font.SysFont("Courier New", 42, bold=True),
            "big":   pygame.font.SysFont("Courier New", 28, bold=True),
            "mid":   pygame.font.SysFont("Courier New", 20, bold=True),
            "small": pygame.font.SysFont("Courier New", 15),
            "pixel": pygame.font.SysFont("Consolas",    18),
        }
    except Exception:
        return {k: pygame.font.Font(None, s) for k, s in
                [("title",52),("big",34),("mid",26),("small",20),("pixel",22)]}


def _scanlines(surf):
    w = surf.get_width()
    for y in range(0, surf.get_height(), 2):
        pygame.draw.line(surf, (0, 0, 0), (0, y), (w, y))


def _blit_centered(surf, txt_surf, y):
    surf.blit(txt_surf, (surf.get_width() // 2 - txt_surf.get_width() // 2, y))


def _box(surf, rect, color=BORD, fill=PANEL, radius=6):
    pygame.draw.rect(surf, fill,  rect, border_radius=radius)
    pygame.draw.rect(surf, color, rect, 2, border_radius=radius)


class MainMenu:
    MAIN_OPTIONS = ["NOUVELLE PARTIE", "CONTINUER", "QUITTER"]

    def __init__(self, screen_surface):
        self.surf    = screen_surface
        self.W, self.H = screen_surface.get_size()
        self.fonts   = _fonts()
        self.state   = "MAIN"
        self.result  = None
        self.running = True
        self.main_sel  = 0
        self.saves     = []
        self.save_sel  = 0
        self.input_text= ""
        self.input_err = ""
        self.skin_sel  = 0
        self._pending_name = ""
        self.skin_previews = {}
        self._load_skin_previews()
        self._stars = [self._mk_star(True) for _ in range(60)]
        self._blink = 0
        self._start_music()

    def _start_music(self):
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(MUSIC_FILE)
            pygame.mixer.music.set_volume(0.4)
            pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"[menu] Musique non chargée : {e}")

    def stop_music(self):
        try:
            pygame.mixer.music.fadeout(600)
        except Exception:
            pass

    def _load_skin_previews(self):
        for sk in SKINS:
            try:
                sheet = pygame.image.load(sk["walk"]).convert_alpha()
                w, h  = sheet.get_width() // 4, sheet.get_height() // 4
                frame = sheet.subsurface(pygame.Rect(0, 0, w, h))
                self.skin_previews[sk["id"]] = pygame.transform.scale(frame, (w*5, h*5))
            except Exception:
                self.skin_previews[sk["id"]] = None

    def _mk_star(self, spread=False):
        return {
            "x": random.uniform(0, self.W),
            "y": random.uniform(0, self.H) if spread else float(self.H),
            "vx": random.uniform(-0.3, 0.3),
            "vy": random.uniform(-0.6, -0.1),
            "r":  random.uniform(0.5, 2),
            "b":  random.randint(40, 160),
        }

    def _draw_stars(self):
        for i, s in enumerate(self._stars):
            s["x"] += s["vx"]; s["y"] += s["vy"]
            if s["y"] < 0 or s["x"] < 0 or s["x"] > self.W:
                self._stars[i] = self._mk_star()
                continue
            b = int(s["b"])
            pygame.draw.circle(self.surf, (0, b, int(b*0.6)),
                               (int(s["x"]), int(s["y"])), int(s["r"]))

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            dt = clock.tick(60)
            self._blink = (self._blink + dt) % 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                self._handle(event)
            self._draw()
            pygame.display.flip()
            if self.result is not None:
                self.stop_music()
                return self.result
        return None

    def _handle(self, event):
        if event.type != pygame.KEYDOWN:
            return
        {"MAIN": self._handle_main, "SELECT": self._handle_select,
         "NEW_NAME": self._handle_name, "SKIN": self._handle_skin,
         }.get(self.state, lambda e: None)(event)

    def _handle_main(self, event):
        k = event.key
        if k in (pygame.K_UP, pygame.K_LEFT):
            self.main_sel = (self.main_sel - 1) % len(self.MAIN_OPTIONS)
        elif k in (pygame.K_DOWN, pygame.K_RIGHT):
            self.main_sel = (self.main_sel + 1) % len(self.MAIN_OPTIONS)
        elif k == pygame.K_RETURN:
            opt = self.MAIN_OPTIONS[self.main_sel]
            if opt == "NOUVELLE PARTIE":
                self.state = "NEW_NAME"; self.input_text = ""; self.input_err = ""
            elif opt == "CONTINUER":
                self.saves = list_saves(); self.save_sel = 0; self.state = "SELECT"
            else:
                self.running = False

    def _handle_select(self, event):
        k = event.key
        if not self.saves:
            if k == pygame.K_ESCAPE: self.state = "MAIN"
            return
        if k in (pygame.K_UP, pygame.K_LEFT):
            self.save_sel = (self.save_sel - 1) % len(self.saves)
        elif k in (pygame.K_DOWN, pygame.K_RIGHT):
            self.save_sel = (self.save_sel + 1) % len(self.saves)
        elif k == pygame.K_RETURN:
            data = load_save(self.saves[self.save_sel])
            if data: self.result = data
        elif k == pygame.K_ESCAPE:
            self.state = "MAIN"

    def _handle_name(self, event):
        k = event.key
        if k == pygame.K_ESCAPE:
            self.state = "MAIN"
        elif k == pygame.K_RETURN:
            name = self.input_text.strip()
            if len(name) < 2:    self.input_err = "MIN. 2 CARACTERES !"
            elif len(name) > 12: self.input_err = "MAX. 12 CARACTERES !"
            else:
                self._pending_name = name; self.skin_sel = 0; self.state = "SKIN"
        elif k == pygame.K_BACKSPACE:
            self.input_text = self.input_text[:-1]; self.input_err = ""
        else:
            c = event.unicode
            if c and c.isprintable() and len(self.input_text) < 12:
                self.input_text += c; self.input_err = ""

    def _handle_skin(self, event):
        k = event.key
        if k in (pygame.K_LEFT, pygame.K_UP):
            self.skin_sel = (self.skin_sel - 1) % len(SKINS)
        elif k in (pygame.K_RIGHT, pygame.K_DOWN):
            self.skin_sel = (self.skin_sel + 1) % len(SKINS)
        elif k == pygame.K_RETURN:
            self.result = new_save(self._pending_name, SKINS[self.skin_sel]["id"])
        elif k == pygame.K_ESCAPE:
            self.state = "NEW_NAME"

    def _draw(self):
        self.surf.fill(NOIR)
        self._draw_stars()
        {"MAIN": self._draw_main, "SELECT": self._draw_select,
         "NEW_NAME": self._draw_new_name, "SKIN": self._draw_skin,
         }.get(self.state, lambda: None)()
        _scanlines(self.surf)

    def _draw_main(self):
        t  = pygame.time.get_ticks() / 1000
        W, H = self.W, self.H
        logo_lines = [
            "  __  __  ___  _  _     _ ___ _   _  ",
            " |  \\/  |/ _ \\| \\| |   | | __| | | | ",
            " | |\\/| | (_) | .` |   | | _|| |_| | ",
            " |_|  |_|\\___/|_|\\_|  _/ |___|\\___|  ",
            "                     |__/             ",
        ]
        pulse = int(abs(math.sin(t * 1.5)) * 55)
        logo_color = (0, 180 + pulse, 60 + pulse // 2)
        for i, line in enumerate(logo_lines):
            s = self.fonts["pixel"].render(line, True, logo_color)
            _blit_centered(self.surf, s, 55 + i * 20)
        sub = self.fonts["small"].render(
            ">>> L'ILE AUX MINI-JEUX <<<", True, GRIS)
        _blit_centered(self.surf, sub, 170)
        pygame.draw.line(self.surf, BORD, (W//2-220, 196), (W//2+220, 196), 1)
        for i, opt in enumerate(self.MAIN_OPTIONS):
            sel   = i == self.main_sel
            y     = 218 + i * 56
            blink = self._blink < 500
            prefix = ("> " if blink else "  ") if sel else "  "
            color  = VERT if sel else GRIS
            txt    = self.fonts["big"].render(prefix + opt, True, color)
            if sel:
                _box(self.surf, pygame.Rect(W//2-210, y-5, 420, 44))
            _blit_centered(self.surf, txt, y)
        pygame.draw.line(self.surf, BORD, (W//2-220, H-58), (W//2+220, H-58), 1)
        hint = self.fonts["small"].render(
            "[ FLECHES ] NAVIGUER    [ ENTREE ] VALIDER", True, GRIS)
        _blit_centered(self.surf, hint, H - 42)
        ver = self.fonts["small"].render("v1.0", True, (35, 35, 55))
        self.surf.blit(ver, (10, H - 20))

    def _draw_select(self):
        self._draw_header(">> CHARGER UNE PARTIE <<")
        if not self.saves:
            msg = self.fonts["mid"].render("AUCUNE SAUVEGARDE TROUVEE.", True, ROUGE)
            _blit_centered(self.surf, msg, self.H // 2)
        else:
            for i, name in enumerate(self.saves):
                sel  = i == self.save_sel
                data = load_save(name) or {}
                hs   = data.get("highscores", {}); best = max(hs.values()) if hs else 0
                label = f"{'>' if sel else ' '} {name:<12}  BEST:{best:>6}"
                txt   = self.fonts["mid"].render(label, True, VERT if sel else GRIS)
                y     = 185 + i * 46
                if sel: _box(self.surf, pygame.Rect(self.W//2-270, y-4, 540, 36))
                _blit_centered(self.surf, txt, y)
        self._draw_footer("[ FLECHES ] CHOISIR   [ ENTREE ] JOUER   [ ECHAP ] RETOUR")

    def _draw_new_name(self):
        self._draw_header(">> NOUVELLE PARTIE <<")
        prompt = self.fonts["mid"].render("ENTRE TON NOM :", True, BLANC)
        _blit_centered(self.surf, prompt, 215)
        bw, bh = 380, 46
        bx = self.W // 2 - bw // 2
        by = 255
        _box(self.surf, pygame.Rect(bx, by, bw, bh), color=VERT)
        cursor = "_" if self._blink < 500 else " "
        inp    = self.fonts["big"].render(self.input_text + cursor, True, VERT)
        self.surf.blit(inp, (bx + 12, by + 8))
        if self.input_err:
            err = self.fonts["small"].render("! " + self.input_err, True, ROUGE)
            _blit_centered(self.surf, err, by + bh + 12)
        self._draw_footer("[ ENTREE ] VALIDER   [ ECHAP ] RETOUR")

    def _draw_skin(self):
        self._draw_header(">> CHOIX DU PERSONNAGE <<")
        sk   = SKINS[self.skin_sel]
        prev = self.skin_previews.get(sk["id"])
        fx, fy, fw, fh = self.W//2-70, 185, 140, 160
        _box(self.surf, pygame.Rect(fx, fy, fw, fh), color=VERT)
        if prev:
            self.surf.blit(prev, (fx + fw//2 - prev.get_width()//2,
                                  fy + fh//2 - prev.get_height()//2))
        else:
            ph = self.fonts["mid"].render("???", True, GRIS)
            _blit_centered(self.surf, ph, fy + fh//2)
        lbl = self.fonts["big"].render(sk["label"].upper(), True, JAUNE)
        _blit_centered(self.surf, lbl, fy + fh + 12)
        if len(SKINS) > 1:
            nav = self.fonts["mid"].render(
                f"<  {self.skin_sel+1} / {len(SKINS)}  >", True, GRIS)
            _blit_centered(self.surf, nav, fy + fh + 42)
        self._draw_footer("[ FLECHES ] CHANGER   [ ENTREE ] CHOISIR   [ ECHAP ] RETOUR")

    def _draw_header(self, title):
        t = self.fonts["big"].render(title, True, CYAN)
        _blit_centered(self.surf, t, 115)
        pygame.draw.line(self.surf, BORD, (self.W//2-260,152), (self.W//2+260,152), 1)

    def _draw_footer(self, hint):
        pygame.draw.line(self.surf, BORD,
                         (self.W//2-260, self.H-52), (self.W//2+260, self.H-52), 1)
        h = self.fonts["small"].render(hint, True, GRIS)
        _blit_centered(self.surf, h, self.H - 36)
