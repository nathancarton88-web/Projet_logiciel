"""
menu.py  —  Menu principal  ~  L'ÎLE AUX MINI-JEUX  ~  style été rétro
"""

import pygame, math, random
from save_manager import list_saves, load_save, new_save, SKINS, skin_by_id

# ── Palette été rétro ─────────────────────────────────────────────────────────
CIEL_HAUT  = ( 30, 140, 255)   # bleu ciel profond
CIEL_BAS   = (135, 210, 255)   # bleu ciel clair
MER_HAUT   = (  0, 180, 200)   # turquoise
MER_BAS    = (  0, 120, 160)   # bleu mer
SABLE      = (255, 210, 100)   # sable chaud
SABLE2     = (240, 175,  60)   # sable ombre
SOLEIL     = (255, 240,  80)   # jaune soleil
SOLEIL2    = (255, 180,  30)   # orange soleil
BLANC      = (255, 255, 240)   # blanc crème
ROUGE_VIF  = (255,  70,  50)   # rouge vif
ORANGE     = (255, 140,   0)   # orange
VERT_PALM  = ( 60, 200,  80)   # vert palmier
VERT_FONC  = ( 20, 120,  40)   # vert foncé
TEXTE_OMB  = (120,  60,   0)   # brun ombré
PANEL_ETE  = (255, 250, 220)   # panneau bois clair
PANEL_BORD = (200, 140,  50)   # bord bois
GRIS_ETE   = (160, 130,  90)   # gris chaud

MUSIC_FILE = "assets/music/menu.ogg"


def _fonts():
    try:
        return {
            "title": pygame.font.SysFont("Courier New", 48, bold=True),
            "big":   pygame.font.SysFont("Courier New", 26, bold=True),
            "mid":   pygame.font.SysFont("Courier New", 19, bold=True),
            "small": pygame.font.SysFont("Courier New", 14),
            "pixel": pygame.font.SysFont("Consolas",    17),
        }
    except Exception:
        return {k: pygame.font.Font(None, s) for k, s in
                [("title",56),("big",32),("mid",24),("small",18),("pixel",20)]}


def _blit_centered(surf, txt_surf, y):
    surf.blit(txt_surf, (surf.get_width() // 2 - txt_surf.get_width() // 2, y))


def _scanlines(surf):
    """Légères scanlines pour garder l'aspect rétro sans assombrir."""
    sl = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    for y in range(0, surf.get_height(), 3):
        pygame.draw.line(sl, (0, 0, 0, 18), (0, y), (surf.get_width(), y))
    surf.blit(sl, (0, 0))


def _box(surf, rect, color=PANEL_BORD, fill=PANEL_ETE, radius=6):
    pygame.draw.rect(surf, fill,  rect, border_radius=radius)
    pygame.draw.rect(surf, color, rect, 2, border_radius=radius)


# ── Éléments décoratifs ───────────────────────────────────────────────────────

def _draw_sun(surf, cx, cy, r, t):
    """Soleil animé avec rayons tournants."""
    # Halo
    for i in range(3):
        alpha = 60 - i * 18
        sr = r + 14 + i * 10
        halo = pygame.Surface((sr*2, sr*2), pygame.SRCALPHA)
        pygame.draw.circle(halo, (*SOLEIL, alpha), (sr, sr), sr)
        surf.blit(halo, (cx - sr, cy - sr))
    # Corps soleil
    pygame.draw.circle(surf, SOLEIL2, (cx, cy), r + 2)
    pygame.draw.circle(surf, SOLEIL,  (cx, cy), r)
    # Rayons
    nb = 12
    for i in range(nb):
        angle = math.radians(i * 360 / nb + t * 15)
        x1 = cx + int((r + 5)  * math.cos(angle))
        y1 = cy + int((r + 5)  * math.sin(angle))
        x2 = cx + int((r + 14) * math.cos(angle))
        y2 = cy + int((r + 14) * math.sin(angle))
        pygame.draw.line(surf, SOLEIL, (x1, y1), (x2, y2), 3)


def _draw_palm(surf, bx, by, flip=False):
    """Palmier pixel rétro."""
    # Tronc
    for i in range(7):
        w = 10 - i
        col = (160 + i*8, 100 + i*5, 40)
        pygame.draw.rect(surf, col, (bx - w//2 + (2 if flip else -2)*i//3, by - i*18, w, 20))
    tx, ty = bx + (-5 if flip else 5), by - 7*18 + 10
    # Feuilles
    leaves = [(-60, -30), (-40, -55), (-15, -65), (15, -60), (40, -50), (55, -25)]
    if flip:
        leaves = [(-x, y) for x, y in leaves]
    for dx, dy in leaves:
        ex, ey = tx + dx, ty + dy
        pygame.draw.line(surf, VERT_FONC, (tx, ty), (ex, ey), 5)
        pygame.draw.line(surf, VERT_PALM, (tx, ty), (ex, ey), 3)
        # Petites feuilles secondaires
        mid_x, mid_y = tx + dx//2, ty + dy//2
        pygame.draw.line(surf, VERT_PALM,
                         (mid_x, mid_y),
                         (mid_x + dy//5, mid_y - dx//5), 2)


def _draw_wave(surf, y_base, t, color, alpha=180, amp=8, freq=0.018, phase=0):
    """Vague animée."""
    W = surf.get_width()
    pts = []
    for x in range(W + 1):
        y = y_base + int(amp * math.sin(x * freq + t * 2 + phase))
        pts.append((x, y))
    pts.append((W, surf.get_height()))
    pts.append((0, surf.get_height()))
    wave_surf = pygame.Surface((W, surf.get_height()), pygame.SRCALPHA)
    pygame.draw.polygon(wave_surf, (*color, alpha), pts)
    surf.blit(wave_surf, (0, 0))


def _draw_cloud(surf, cx, cy, scale=1.0):
    """Nuage rétro pixel."""
    blobs = [(0, 0, 28), (-26, 8, 20), (26, 8, 20), (-14, 14, 16), (14, 14, 16)]
    for dx, dy, r in blobs:
        pygame.draw.circle(surf, BLANC, (int(cx + dx*scale), int(cy + dy*scale)), int(r*scale))


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
        self._blink = 0
        self._t = 0.0
        # Nuages : (x, y, vitesse, scale)
        self._clouds = [
            {"x": random.uniform(0, self.W), "y": random.uniform(50, 160),
             "vx": random.uniform(0.2, 0.6), "s": random.uniform(0.7, 1.3)}
            for _ in range(6)
        ]
        # Mouettes : (x, y, phase)
        self._gulls = [
            {"x": random.uniform(0, self.W), "y": random.uniform(80, 180),
             "vx": random.uniform(0.5, 1.2), "ph": random.uniform(0, math.pi*2)}
            for _ in range(5)
        ]
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

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            dt = clock.tick(60)
            self._blink = (self._blink + dt) % 1000
            self._t += dt / 1000.0
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

    # ── Input handlers (inchangés) ─────────────────────────────────────────────

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

    # ── Rendu ─────────────────────────────────────────────────────────────────

    def _draw(self):
        self._draw_background()
        {"MAIN":     self._draw_main,
         "SELECT":   self._draw_select,
         "NEW_NAME": self._draw_new_name,
         "SKIN":     self._draw_skin,
         }.get(self.state, lambda: None)()
        _scanlines(self.surf)

    def _draw_background(self):
        W, H = self.W, self.H
        t = self._t

        # ── Dégradé ciel ──────────────────────────────────────────────────────
        sky_h = int(H * 0.58)
        for y in range(sky_h):
            r_lerp = y / sky_h
            r = int(CIEL_HAUT[0] + (CIEL_BAS[0] - CIEL_HAUT[0]) * r_lerp)
            g = int(CIEL_HAUT[1] + (CIEL_BAS[1] - CIEL_HAUT[1]) * r_lerp)
            b = int(CIEL_HAUT[2] + (CIEL_BAS[2] - CIEL_HAUT[2]) * r_lerp)
            pygame.draw.line(self.surf, (r, g, b), (0, y), (W, y))

        # ── Soleil ────────────────────────────────────────────────────────────
        _draw_sun(self.surf, W - 140, 80, 44, t)

        # ── Nuages ────────────────────────────────────────────────────────────
        for c in self._clouds:
            c["x"] += c["vx"]
            if c["x"] > W + 100:
                c["x"] = -100
            _draw_cloud(self.surf, int(c["x"]), int(c["y"]), c["s"])

        # ── Mouettes ──────────────────────────────────────────────────────────
        for g in self._gulls:
            g["x"] += g["vx"]
            if g["x"] > W + 40:
                g["x"] = -40
            wing = int(5 * math.sin(t * 4 + g["ph"]))
            gx, gy = int(g["x"]), int(g["y"])
            pygame.draw.line(self.surf, (60, 60, 90),
                             (gx - 10, gy + wing), (gx, gy), 2)
            pygame.draw.line(self.surf, (60, 60, 90),
                             (gx, gy), (gx + 10, gy + wing), 2)

        # ── Mer (dégradé + vagues) ────────────────────────────────────────────
        mer_y = sky_h
        for y in range(mer_y, H - 60):
            r_lerp = (y - mer_y) / (H - 60 - mer_y)
            r = int(MER_HAUT[0] + (MER_BAS[0] - MER_HAUT[0]) * r_lerp)
            g = int(MER_HAUT[1] + (MER_BAS[1] - MER_HAUT[1]) * r_lerp)
            b = int(MER_HAUT[2] + (MER_BAS[2] - MER_HAUT[2]) * r_lerp)
            pygame.draw.line(self.surf, (r, g, b), (0, y), (W, y))

        # Reflets soleil sur la mer
        for i in range(5):
            rx = W - 140 + random.randint(-30, 30)
            ry = sky_h + 20 + i * 12
            rw = max(4, 60 - i * 10)
            refl = pygame.Surface((rw, 4), pygame.SRCALPHA)
            refl.fill((*SOLEIL, 80))
            self.surf.blit(refl, (rx - rw//2, ry))

        _draw_wave(self.surf, sky_h + 5,  t, MER_HAUT, alpha=120, amp=6,  freq=0.020, phase=0)
        _draw_wave(self.surf, sky_h + 18, t, (0, 200, 220), alpha=80, amp=5, freq=0.016, phase=1.2)

        # ── Sable ─────────────────────────────────────────────────────────────
        sand_y = H - 60
        for y in range(sand_y, H):
            r_lerp = (y - sand_y) / (H - sand_y)
            r = int(SABLE[0] + (SABLE2[0] - SABLE[0]) * r_lerp)
            g_c = int(SABLE[1] + (SABLE2[1] - SABLE[1]) * r_lerp)
            b = int(SABLE[2] + (SABLE2[2] - SABLE[2]) * r_lerp)
            pygame.draw.line(self.surf, (r, g_c, b), (0, y), (W, y))

        # Petits cailloux / détails sable
        for i in range(18):
            sx = 50 + i * 65 + int(3 * math.sin(i * 1.7))
            sy = sand_y + 15 + (i % 3) * 12
            pygame.draw.ellipse(self.surf, SABLE2, (sx, sy, 8, 4))

        # ── Palmiers ─────────────────────────────────────────────────────────
        _draw_palm(self.surf, 90,  H - 10, flip=False)
        _draw_palm(self.surf, W - 80, H - 10, flip=True)

    def _draw_main(self):
        t = self._t
        W, H = self.W, self.H

        # ── Titre principal "L'ÎLE AUX MINI-JEUX" ────────────────────────────
        # Panneau en bois rétro
        pw, ph = 640, 110
        px, py = W//2 - pw//2, 28
        # Ombre panneau
        shadow = pygame.Surface((pw, ph), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 60))
        self.surf.blit(shadow, (px + 6, py + 6))
        # Fond bois
        pygame.draw.rect(self.surf, (200, 150, 70), (px, py, pw, ph), border_radius=8)
        pygame.draw.rect(self.surf, (160, 110, 40), (px, py, pw, ph), 3, border_radius=8)
        # Lignes bois
        for i in range(6):
            lx = px + 8 + i * (pw - 16) // 6
            pygame.draw.line(self.surf, (180, 130, 55),
                             (lx, py + 6), (lx, py + ph - 6), 1)
        # Clous aux coins
        for cx2, cy2 in [(px+12, py+12), (px+pw-12, py+12),
                         (px+12, py+ph-12), (px+pw-12, py+ph-12)]:
            pygame.draw.circle(self.surf, (120, 90, 40), (cx2, cy2), 5)
            pygame.draw.circle(self.surf, (200, 170, 100), (cx2, cy2), 3)

        # Texte titre avec ombre
        titre1 = self.fonts["title"].render("L'ILE AUX", True, TEXTE_OMB)
        titre2 = self.fonts["title"].render("MINI-JEUX", True, TEXTE_OMB)
        # Ombres
        self.surf.blit(self.fonts["title"].render("L'ILE AUX", True, (80, 40, 0)),
                       (W//2 - titre1.get_width()//2 + 2, py + 8 + 2))
        self.surf.blit(titre1, (W//2 - titre1.get_width()//2, py + 8))

        # Pulsation couleur sur "MINI-JEUX"
        pulse = abs(math.sin(t * 2.0))
        mc = (int(220 + pulse*35), int(80 + pulse*40), int(20 + pulse*20))
        titre2_col = self.fonts["title"].render("MINI-JEUX", True, mc)
        self.surf.blit(self.fonts["title"].render("MINI-JEUX", True, (80, 40, 0)),
                       (W//2 - titre2.get_width()//2 + 2, py + 57 + 2))
        self.surf.blit(titre2_col, (W//2 - titre2.get_width()//2, py + 57))

        # ── Options (panneaux style affichette de plage) ──────────────────────
        opt_y_start = 168
        for i, opt in enumerate(self.MAIN_OPTIONS):
            sel   = i == self.main_sel
            y     = opt_y_start + i * 62

            # Couleurs selon option
            fill_colors = [(255, 240, 180), (220, 255, 200), (255, 210, 200)]
            bord_colors = [(200, 140,  50), (50,  160,  60), (200,  80,  60)]
            fill = fill_colors[i]
            bord = bord_colors[i]

            ow, oh = 460, 48
            ox = W//2 - ow//2

            # Ombre
            sh = pygame.Surface((ow, oh), pygame.SRCALPHA)
            sh.fill((0, 0, 0, 50 if sel else 25))
            self.surf.blit(sh, (ox + 5, y + 5))

            # Fond
            pygame.draw.rect(self.surf, fill, (ox, y, ow, oh), border_radius=7)
            bw = 3 if sel else 2
            pygame.draw.rect(self.surf, bord, (ox, y, ow, oh), bw, border_radius=7)

            # Clignotement curseur
            blink = self._blink < 500
            prefix = (">> " if blink else "   ") if sel else "   "
            txt_col = (40, 20, 0) if sel else (90, 60, 20)
            txt = self.fonts["big"].render(prefix + opt, True, txt_col)
            self.surf.blit(txt, (ox + ow//2 - txt.get_width()//2, y + oh//2 - txt.get_height()//2))

        # ── Séparateur vague décoratif ────────────────────────────────────────
        sep_y = opt_y_start + len(self.MAIN_OPTIONS) * 62 + 10
        for x in range(0, W, 8):
            dy = int(3 * math.sin(x * 0.05 + t * 2))
            pygame.draw.circle(self.surf, MER_HAUT, (x, sep_y + dy), 1)

        # ── Hint bas ──────────────────────────────────────────────────────────
        hint = self.fonts["small"].render(
            "[ FLECHES ] NAVIGUER     [ ENTREE ] VALIDER", True, (100, 70, 20))
        _blit_centered(self.surf, hint, H - 38)

        ver = self.fonts["small"].render("v1.0", True, (160, 120, 60))
        self.surf.blit(ver, (10, H - 22))

    def _draw_select(self):
        self._draw_panel_header(">> CHARGER UNE PARTIE <<")
        if not self.saves:
            msg = self.fonts["mid"].render("AUCUNE SAUVEGARDE TROUVEE.", True, ROUGE_VIF)
            _blit_centered(self.surf, msg, self.H // 2)
        else:
            for i, name in enumerate(self.saves):
                sel  = i == self.save_sel
                data = load_save(name) or {}
                hs   = data.get("highscores", {}); best = max(hs.values()) if hs else 0
                label = f"{'>' if sel else ' '} {name:<12}  BEST:{best:>6}"
                fill = (255, 245, 200) if sel else (230, 220, 180)
                bord = PANEL_BORD if sel else (180, 140, 80)
                y = 185 + i * 48
                ow, oh = 520, 38
                ox = self.W//2 - ow//2
                pygame.draw.rect(self.surf, fill, (ox, y, ow, oh), border_radius=6)
                pygame.draw.rect(self.surf, bord, (ox, y, ow, oh), 2, border_radius=6)
                txt = self.fonts["mid"].render(label, True, (40, 20, 0) if sel else (100, 70, 30))
                _blit_centered(self.surf, txt, y + 9)
        self._draw_panel_footer("[ FLECHES ] CHOISIR   [ ENTREE ] JOUER   [ ECHAP ] RETOUR")

    def _draw_new_name(self):
        self._draw_panel_header(">> NOUVELLE PARTIE <<")
        prompt = self.fonts["mid"].render("ENTRE TON NOM :", True, (60, 30, 0))
        _blit_centered(self.surf, prompt, 215)
        bw, bh = 380, 48
        bx = self.W // 2 - bw // 2
        by = 255
        pygame.draw.rect(self.surf, (255, 250, 210), (bx, by, bw, bh), border_radius=7)
        pygame.draw.rect(self.surf, PANEL_BORD,      (bx, by, bw, bh), 2, border_radius=7)
        cursor = "_" if self._blink < 500 else " "
        inp = self.fonts["big"].render(self.input_text + cursor, True, (60, 30, 0))
        self.surf.blit(inp, (bx + 14, by + 10))
        if self.input_err:
            err = self.fonts["small"].render("! " + self.input_err, True, ROUGE_VIF)
            _blit_centered(self.surf, err, by + bh + 12)
        self._draw_panel_footer("[ ENTREE ] VALIDER   [ ECHAP ] RETOUR")

    def _draw_skin(self):
        self._draw_panel_header(">> CHOIX DU PERSONNAGE <<")
        sk   = SKINS[self.skin_sel]
        prev = self.skin_previews.get(sk["id"])
        fx, fy, fw, fh = self.W//2-70, 185, 140, 160
        pygame.draw.rect(self.surf, (255, 248, 210), (fx, fy, fw, fh), border_radius=8)
        pygame.draw.rect(self.surf, PANEL_BORD,      (fx, fy, fw, fh), 2, border_radius=8)
        if prev:
            self.surf.blit(prev, (fx + fw//2 - prev.get_width()//2,
                                  fy + fh//2 - prev.get_height()//2))
        else:
            ph = self.fonts["mid"].render("???", True, GRIS_ETE)
            _blit_centered(self.surf, ph, fy + fh//2)
        lbl = self.fonts["big"].render(sk["label"].upper(), True, (60, 30, 0))
        _blit_centered(self.surf, lbl, fy + fh + 14)
        if len(SKINS) > 1:
            nav = self.fonts["mid"].render(
                f"<  {self.skin_sel+1} / {len(SKINS)}  >", True, GRIS_ETE)
            _blit_centered(self.surf, nav, fy + fh + 44)
        self._draw_panel_footer("[ FLECHES ] CHANGER   [ ENTREE ] CHOISIR   [ ECHAP ] RETOUR")

    # ── En-tête / pied de page communs ────────────────────────────────────────

    def _draw_panel_header(self, title):
        W = self.W
        # Panneau bois
        pw, ph2 = 520, 44
        px, py = W//2 - pw//2, 78
        pygame.draw.rect(self.surf, (200, 150, 70), (px, py, pw, ph2), border_radius=6)
        pygame.draw.rect(self.surf, (160, 110, 40), (px, py, pw, ph2), 2, border_radius=6)
        t = self.fonts["mid"].render(title, True, (60, 30, 0))
        _blit_centered(self.surf, t, py + ph2//2 - t.get_height()//2)
        # Ligne déco
        for x in range(W//2 - 240, W//2 + 240, 6):
            dy = int(2 * math.sin(x * 0.07 + self._t * 2))
            pygame.draw.circle(self.surf, MER_HAUT, (x, py + ph2 + 10 + dy), 1)

    def _draw_panel_footer(self, hint):
        for x in range(self.W//2 - 240, self.W//2 + 240, 6):
            dy = int(2 * math.sin(x * 0.07 + self._t * 2 + 1))
            pygame.draw.circle(self.surf, MER_HAUT, (x, self.H - 48 + dy), 1)
        h = self.fonts["small"].render(hint, True, (100, 70, 20))
        _blit_centered(self.surf, h, self.H - 34)
