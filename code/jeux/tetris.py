import pygame, random, math
from jeux.ete_theme import (draw_game_bg, draw_wood_panel, draw_wave_line,
                            draw_game_over, BLANC, BRUN, BRUN2, MER, SABLE,
                            SOLEIL, ORANGE, ROUGE_VIF, VERT_PALM, ROSE, JAUNE_VIF)

pygame.init()
L_INTERNE, H_INTERNE = 700, 500


try:
    font_pixel = pygame.font.SysFont("Courier New", 17, bold=True)
    font_main = pygame.font.SysFont("Courier New", 32, bold=True)
    font_small = pygame.font.SysFont("Courier New", 13)
except Exception:
    font_pixel = pygame.font.Font(None, 20)
    font_main = pygame.font.Font(None, 36)
    font_small = pygame.font.Font(None, 16)


class Tetris:
    # matrice des pieces
    SHAPES = [
        [[1, 1, 1, 1]],
        [[1, 1], [1, 1]],
        [[0, 1, 0], [1, 1, 1]],
        [[0, 1, 1], [1, 1, 0]],
        [[1, 1, 0], [0, 1, 1]],
        [[1, 0, 0], [1, 1, 1]],
        [[0, 0, 1], [1, 1, 1]],
    ]
    # couleurs
    COLORS = [
        MER,
        SOLEIL,
        ROSE,
        VERT_PALM,
        ROUGE_VIF,
        (100, 180, 255),
        ORANGE,
    ]

    # variables globals (largeur grille, hauteur, taille block)
    LG, HG, BS = 10, 18, 25
    XO, YO = 225, 25  # offset x et y

    def __init__(self):
        self.reset()

    def reset(self):
        # init du tabeau principal vide
        self.grid = [[None] * self.LG for _ in range(self.HG)]
        self.cur = self._new()  # piece actule
        self.nxt = self._new()  # piece apres
        self.score = 0
        self.level = 1
        self.lines = 0
        self.ft = 0
        self.game_over = False

    def _new(self):
        # genere nvl piece au pif
        i = random.randint(0, 6)
        return {'x': 3, 'y': 0, 'shape': self.SHAPES[i], 'color': self.COLORS[i]}

    def rotate(self, s):
        # opti: tourne la matrice avec zip
        return [list(r) for r in zip(*s[::-1])]

    def collide(self, dx=0, dy=0, shape=None):
        # fonction pour fix la hitbox
        s = shape or self.cur['shape']
        for r, row in enumerate(s):
            for c, v in enumerate(row):
                if v:  # si ya un bloc
                    nx, ny = self.cur['x'] + c + dx, self.cur['y'] + r + dy
                    # check murs gauche droite et bas
                    if nx < 0 or nx >= self.LG or ny >= self.HG: return True
                    # check block deja posé
                    if ny >= 0 and self.grid[ny][nx]: return True
        return False

    def ghost_y(self):
        # simule la chute pour afficher lombre
        gy = self.cur['y']
        while not self.collide(dy=gy - self.cur['y'] + 1): gy += 1
        return gy

    def update(self, dt):
        if self.game_over: return
        self.ft += dt

        # update de la vitesse (accelere selon le level)
        if self.ft > max(100, 500 - self.level * 40):
            # si libre en dessous on descend de 1
            if not self.collide(dy=1):
                self.cur['y'] += 1
            else:
                # sinon on merge avec le decor
                self._lock()
            self.ft = 0

    def _lock(self):
        # fige la map
        for r, row in enumerate(self.cur['shape']):
            for c, v in enumerate(row):
                if v:
                    yp = self.cur['y'] + r
                    # si ca bloque hors ecran = dead
                    if yp < 0:
                        self.game_over = True
                        return
                    self.grid[yp][self.cur['x'] + c] = self.cur['color']

        self._clear()  # pete les lignes
        self.cur = self.nxt
        self.nxt = self._new()
        # respawn dans un mur
        if self.collide(): self.game_over = True

    def _clear(self):
        # check ligne pleine
        full = [i for i, row in enumerate(self.grid) if all(row)]
        for i in full:
            # supprime la ligne
            del self.grid[i]
            # decale tout vers le bas en addant une liste None en haut
            self.grid.insert(0, [None] * self.LG)

        if full:
            self.lines += len(full)
            # calcul des pts
            self.score += [0, 100, 300, 500, 800][len(full)] * self.level
            self.level = self.lines // 10 + 1

    def _blk(self, surf, x, y, color):
        # helper pour afficher 1 seul carre de tetris
        r = (self.XO + x * self.BS, self.YO + y * self.BS, self.BS, self.BS)
        pygame.draw.rect(surf, color, r, border_radius=3)
        # petit filtre blanc en haut a gauche pour l'effet 3d vitre
        highlight = tuple(min(255, c + 60) for c in color)
        pygame.draw.rect(surf, highlight, (r[0] + 2, r[1] + 2, 6, 6))
        pygame.draw.rect(surf, (0, 0, 0), r, 1, border_radius=3)

    def draw(self, surf):
        # fct d'affichage frame
        t = pygame.time.get_ticks() / 1000.0
        draw_game_bg(surf)

        # decor vagues
        draw_wave_line(surf, self.YO + self.HG * self.BS + 4, t)

        # map principal
        board = (self.XO, self.YO, self.LG * self.BS, self.HG * self.BS)
        bg = pygame.Surface((self.LG * self.BS, self.HG * self.BS), pygame.SRCALPHA)
        bg.fill((0, 40, 80, 140))  # filtre sombre
        surf.blit(bg, (self.XO, self.YO))
        pygame.draw.rect(surf, SABLE, board, 2)

        # affichage des trais de la grille
        for x in range(self.LG + 1):
            pygame.draw.line(surf, (0, 60, 100), (self.XO + x * self.BS, self.YO),
                             (self.XO + x * self.BS, self.YO + self.HG * self.BS))
        for y in range(self.HG + 1):
            pygame.draw.line(surf, (0, 60, 100), (self.XO, self.YO + y * self.BS),
                             (self.XO + self.LG * self.BS, self.YO + y * self.BS))

        # affichage pieces figees
        for y, row in enumerate(self.grid):
            for x, c in enumerate(row):
                if c: self._blk(surf, x, y, c)

        # affichage du pseudo fantome en bas
        gy = self.ghost_y()
        for r, row in enumerate(self.cur['shape']):
            for c, v in enumerate(row):
                if v:
                    rect = (self.XO + (self.cur['x'] + c) * self.BS,
                            self.YO + (gy + r) * self.BS, self.BS, self.BS)
                    ghost = pygame.Surface((self.BS, self.BS), pygame.SRCALPHA)
                    ghost.fill((*self.cur['color'], 50))  # 50 = alpha
                    surf.blit(ghost, rect[:2])
                    pygame.draw.rect(surf, (*self.cur['color'], 100), rect, 1)

        # piece qui tombe
        for r, row in enumerate(self.cur['shape']):
            for c, v in enumerate(row):
                if v: self._blk(surf, self.cur['x'] + c, self.cur['y'] + r, self.cur['color'])


        nx_x = self.XO + self.LG * self.BS + 14
        draw_wood_panel(surf, (nx_x, self.YO, 110, 110), radius=6)
        lbl = font_small.render("SUIVANT", True, BRUN)
        surf.blit(lbl, (nx_x + 55 - lbl.get_width() // 2, self.YO + 6))

        # dessine le mini block next
        for r, row in enumerate(self.nxt['shape']):
            for c, v in enumerate(row):
                if v:
                    pygame.draw.rect(surf, self.nxt['color'],
                                     (nx_x + 20 + c * 22, self.YO + 30 + r * 22, 20, 20), border_radius=3)
                    h = tuple(min(255, x + 50) for x in self.nxt['color'])
                    pygame.draw.rect(surf, h, (nx_x + 20 + c * 22 + 2, self.YO + 30 + r * 22 + 2, 5, 5))

        # score/stats
        draw_wood_panel(surf, (nx_x, self.YO + 120, 110, 70), radius=6)
        sc = font_small.render(f"SCORE", True, BRUN2)
        surf.blit(sc, (nx_x + 10, self.YO + 126))
        sv = font_pixel.render(str(self.score), True, BRUN)
        surf.blit(sv, (nx_x + 10, self.YO + 142))
        lv = font_small.render(f"LEVEL {self.level}", True, BRUN2)
        surf.blit(lv, (nx_x + 10, self.YO + 162))

        # Tuto inputs
        draw_wood_panel(surf, (nx_x, self.YO + 200, 110, 80), radius=6)
        for i, line in enumerate(["↑ Rotation", "<- -> Depl.", "↓ Rapide", "ESPACE Drop"]):
            ct = font_small.render(line, True, BRUN2)
            surf.blit(ct, (nx_x + 6, self.YO + 208 + i * 17))

        if self.game_over:
            draw_game_over(surf, font_main)