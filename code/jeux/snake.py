import pygame, random, math
from jeux.ete_theme import (draw_game_bg, draw_wood_panel, draw_wave_line,
                            draw_game_over, BLANC, BRUN, BRUN2, MER, MER_FONC,
                            SABLE, SABLE2, SOLEIL, ORANGE, ROUGE_VIF, VERT_PALM,
                            JAUNE_VIF, ROSE, BOIS, BOIS_FONC)

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


class SnakeNeon:
    # params de base map
    COLS, ROWS, TILE = 20, 15, 25
    # offset opti pour centrer la grille direct au milieu de l'ecran
    XO = (L_INTERNE - 20 * 25) // 2
    YO = (H_INTERNE - 15 * 25) // 2

    def __init__(self):
        self.level = 1;
        self.score = 0;
        self.game_over = False
        self.reset()

    def reset(self):
        # coord de spawn au milieu
        cx, cy = self.COLS // 2, self.ROWS // 2
        # le snake c juste une liste de tuple (x,y)
        self.snake = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]
        self.direction = (1, 0);
        self.next_dir = (1, 0)  # vecteur deplacement

        self.score = 0;
        self.level = 1;
        self.eaten = 0
        self.move_timer = 0;
        self.speed = 160  # vitesse de base (en ms jpense)
        self.game_over = False;
        self.flash_timer = 0

        self.boost_timer = 0  # ptit buff de speed
        self.apple_pulse = 0.0;
        self.bonus_blink = 0.0  # float pour timer anim
        self.bonus = None;
        self.bonus_timer = 0

        self.walls = self._build_walls()  # set() des coord des murs
        self.apple = self._free()  # spawn la 1ere pomme au pif

    def _build_walls(self):

        walls = set()
        rings = (self.level - 1) // 5  # division entiere, tout les 5 lvl = un cerle de mur en plus
        for ring in range(1, rings + 1):
            # remplis en haut et bas de la grille
            for x in range(ring, self.COLS - ring):
                walls.add((x, ring));
                walls.add((x, self.ROWS - 1 - ring))
            # remplis cote gauche droite
            for y in range(ring + 1, self.ROWS - ring - 1):
                walls.add((ring, y));
                walls.add((self.COLS - 1 - ring, y))
        return walls

    def _free(self):
        # trouve un block libre
        # on merge les list
        used = set(self.snake) | self.walls
        if self.bonus: used.add(self.bonus)

        # list comprehension pour iterer tt les cases
        cands = [(x, y) for x in range(self.COLS) for y in range(self.ROWS) if (x, y) not in used]
        return random.choice(cands) if cands else (0, 0)

    def set_dir(self, d):
        # empeche de reverse la direction d'un coup mort stupide
        if d[0] != -self.direction[0] or d[1] != -self.direction[1]:
            self.next_dir = d

    def _spawn_bonus(self):
        # fonction rng pour faire pop l'etoile bonus (28% chance qd tu mange)
        if self.bonus is None and random.random() < 0.28:
            self.bonus = self._free()
            self.bonus_timer = 240  # frames de delais max

    def update(self, dt):
        # si t mort on update
        if self.game_over:
            if self.flash_timer > 0: self.flash_timer -= 1
            return

        # maj des frames pour les ptites anim
        self.apple_pulse += 0.12;
        self.bonus_blink += 0.20

        # timeout bonus
        if self.bonus_timer > 0:
            self.bonus_timer -= 1
            if self.bonus_timer == 0: self.bonus = None

        if self.boost_timer > 0: self.boost_timer -= 1

        self.move_timer += dt
        # division euclid //2 pour buf vitesse
        eff = self.speed // 2 if self.boost_timer > 0 else self.speed
        if self.move_timer < eff: return

        self.move_timer = 0
        self.direction = self.next_dir
        hx, hy = self.snake[0]  # on choppe la tete
        nx, ny = hx + self.direction[0], hy + self.direction[1]  # nvl pos

        # verif hitbox bordures ecran + mur + serpent
        if (nx < 0 or nx >= self.COLS or ny < 0 or ny >= self.ROWS
                or (nx, ny) in self.walls or (nx, ny) in set(self.snake)):
            self.game_over = True
            self.flash_timer = 30  # init anim de mort
            return

        # add nvl case a l'avant
        self.snake.insert(0, (nx, ny))

        # check collision pomme
        if (nx, ny) == self.apple:
            self.score += 10 * self.level;
            self.eaten += 1
            # cap le lvl max toute les 5 pommes
            if self.eaten % 5 == 0:
                self.level += 1
                self.speed = max(60, self.speed - 10)  # reduit le temps donc ca va plus vite
                self.walls = self._build_walls()  # update map
            self.apple = self._free()
            self._spawn_bonus()
        # check collision bonus rng
        elif self.bonus and (nx, ny) == self.bonus:
            self.score += 50 * self.level
            self.bonus = None;
            self.bonus_timer = 0;
            self.boost_timer = 180
        else:
            # si on a pas manger on supprime le dernier tuple sinon il grandit a linfini
            self.snake.pop()

    def _seg_color(self, i, total):
        # methode lerp pour color degrade turquoise/vert en fct de la list
        t = i / max(total - 1, 1)  # max pour le ZeroDivisionError
        return (int(t * 60), int((1 - t) * 200 + t * 180), int((1 - t) * 200 + t * 80))

    @staticmethod
    def _star(cx, cy, ro, n=5):
        # fct c des math radian pour tracer des polygone etoile
        ri = ro // 2;
        pts = []
        for k in range(n * 2):
            a = math.radians(k * 180 / n - 90)
            r = ro if k % 2 == 0 else ri
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        return pts

    def draw(self, surf):
        # blit de la frame
        t = pygame.time.get_ticks() / 1000.0
        draw_game_bg(surf)

        # fond du snake avec opacité
        area = (self.XO, self.YO, self.COLS * self.TILE, self.ROWS * self.TILE)
        bg = pygame.Surface((self.COLS * self.TILE, self.ROWS * self.TILE), pygame.SRCALPHA)
        bg.fill((0, 50, 90, 150))
        surf.blit(bg, (self.XO, self.YO))
        pygame.draw.rect(surf, SABLE, area, 2)  # border outline

        # render grille
        for x in range(self.COLS + 1):
            pygame.draw.line(surf, (0, 70, 110),
                             (self.XO + x * self.TILE, self.YO),
                             (self.XO + x * self.TILE, self.YO + self.ROWS * self.TILE))
        for y in range(self.ROWS + 1):
            pygame.draw.line(surf, (0, 70, 110),
                             (self.XO, self.YO + y * self.TILE),
                             (self.XO + self.COLS * self.TILE, self.YO + y * self.TILE))

        # blocks de murs
        for wx, wy in self.walls:
            rx, ry = self.XO + wx * self.TILE, self.YO + wy * self.TILE
            pygame.draw.rect(surf, SABLE2, (rx, ry, self.TILE, self.TILE), border_radius=3)
            pygame.draw.rect(surf, BOIS_FONC, (rx + 1, ry + 1, self.TILE - 2, self.TILE - 2), 1, border_radius=3)

        # fx rouge rgba qd on perd
        if self.flash_timer > 0:
            fs = pygame.Surface((self.COLS * self.TILE, self.ROWS * self.TILE), pygame.SRCALPHA)
            fs.fill((255, 80, 30, int(180 * self.flash_timer / 30)))
            surf.blit(fs, (self.XO, self.YO))

        # render de la ref snake en boucle
        total = len(self.snake)
        for i, (sx, sy) in enumerate(self.snake):
            col = self._seg_color(i, total)
            rx, ry = self.XO + sx * self.TILE + 2, self.YO + sy * self.TILE + 2
            pygame.draw.rect(surf, col, (rx, ry, self.TILE - 3, self.TILE - 3), border_radius=5)
            # if i=0 c la tete on rajoute une ptite stroke et des yeux
            if i == 0:
                pygame.draw.rect(surf, BLANC, (rx, ry, self.TILE - 3, self.TILE - 3), 1, border_radius=5)
                ex = rx + self.TILE - 8 if self.direction[0] >= 0 else rx + 2
                pygame.draw.circle(surf, BLANC, (ex, ry + 5), 3)
                pygame.draw.circle(surf, BRUN, (ex, ry + 5), 1)

        # apple design
        ax = self.XO + self.apple[0] * self.TILE + self.TILE // 2
        ay = self.YO + self.apple[1] * self.TILE + self.TILE // 2
        pr = int(9 + abs(math.sin(self.apple_pulse)) * 3)  # effet de scale sur la pomme
        pygame.draw.circle(surf, (180, 100, 30), (ax, ay), pr)
        pygame.draw.circle(surf, (220, 150, 60), (ax - 2, ay - 2), pr - 3)
        pygame.draw.circle(surf, BRUN, (ax, ay), pr, 1)

        # pop etoile
        if self.bonus:
            bx = self.XO + self.bonus[0] * self.TILE + self.TILE // 2
            by = self.YO + self.bonus[1] * self.TILE + self.TILE // 2
            # clignotement switch ternary wtf
            sc = ORANGE if int(self.bonus_blink) % 2 == 0 else SOLEIL
            pygame.draw.polygon(surf, sc, self._star(bx, by, 11))
            pygame.draw.polygon(surf, BLANC, self._star(bx, by, 11), 1)

        # panels de stats
        draw_wood_panel(surf, (6, 6, 160, 26), radius=5)
        surf.blit(font_small.render(f"SCORE: {self.score}", True, BRUN), (12, 10))
        draw_wood_panel(surf, (6, 36, 160, 26), radius=5)
        surf.blit(font_small.render(f"LEVEL: {self.level}", True, BRUN), (12, 40))

        # message de buff speed si on a manger le bonus
        if self.boost_timer > 0:
            draw_wood_panel(surf, (L_INTERNE // 2 - 70, 6, 140, 26), radius=5)
            bt = font_small.render(f"BOOST ! {self.boost_timer // 60 + 1}s", True, ORANGE)
            surf.blit(bt, (L_INTERNE // 2 - bt.get_width() // 2, 10))

        ht = font_small.render("Fleches = direction", True, SABLE)
        surf.blit(ht, (L_INTERNE // 2 - ht.get_width() // 2, H_INTERNE - 18))

        if self.game_over:
            draw_game_over(surf, font_main)