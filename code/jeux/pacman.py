import pygame, math, random
from jeux.ete_theme import (draw_game_bg, draw_wood_panel, draw_wave_line,
                            draw_game_over, BLANC, BRUN, BRUN2, MER, MER_FONC,
                            SABLE, SABLE2, SOLEIL, ORANGE, ROUGE_VIF, VERT_PALM,
                            ROSE, JAUNE_VIF, BOIS, BOIS_FONC)

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


class Pacman:
    # map faite a la main en string (1 = mur, 2 = point, P = pacman, G = mechant)
    PLAN = [
        "111111111111111111111",
        "122221222212222122221",
        "121121211212112121121",
        "1222222222P2222222221",
        "121121211121112121121",
        "12222122G222G22122221",
        "111111111111111111111",
    ]

    def __init__(self):
        self.t = 22  # taille d'un bloc de map
        self.level = 1;
        self.score = 0
        self._mouth = 0  # variable pour animer l'ouverture de la bouche
        self._PDUP = 300  # duree du buf qd tu bouffe l etoile (en frames)
        self.game_over = False
        self.reset()

    def reset(self):
        # init des list de hitbox (que des rects pygame)
        self.walls = [];
        self.dots = [];
        self.power_ups = []
        self.game_over = False;
        self.power_timer = 0
        self.ghosts = []

        # on parse le PLAN string array pour generer le level dynamique
        for r, row in enumerate(self.PLAN):
            for c, ch in enumerate(row):
                # on decale un peu (offset manuel) pour centrer
                rx, ry = c * self.t + 119, r * self.t + 173
                rect = pygame.Rect(rx, ry, self.t, self.t)

                if ch == '1':
                    self.walls.append(rect)
                elif ch == '2':
                    self.dots.append(pygame.Rect(rect.centerx - 2, rect.centery - 2, 4, 4))
                elif ch == 'P':
                    self.pos = [rect.x, rect.y]
                elif ch == 'G':
                    # array data fantome = [pos x, pos y, [dir x, dir y], color, is_dead]
                    self.ghosts.append([rect.x, rect.y, [1, 0], "red", False])
                    self.ghosts.append([rect.x, rect.y, [-1, 0], "pink", False])

        # positions des 4 grosses etoiles
        self.power_ups = [pygame.Rect(141, 195, 8, 8), pygame.Rect(537, 195, 8, 8),
                          pygame.Rect(141, 283, 8, 8), pygame.Rect(537, 283, 8, 8)]
        self.dir = [0, 0];
        self.next_dir = [0, 0]

    def update(self):
        if self.game_over: return

        # buffer de direction pour pas galerer a tourner pile poil dans l'angle du mur
        if any(self.next_dir):
            nr = pygame.Rect(self.pos[0] + self.next_dir[0], self.pos[1] + self.next_dir[1], self.t - 4, self.t - 4)
            # any() evalue le generateur bool d'un coup
            if not any(nr.colliderect(m) for m in self.walls):
                self.dir = self.next_dir[:];
                self.next_dir = [0, 0]

        # check collison mur pour le mvmt general
        nr = pygame.Rect(self.pos[0] + self.dir[0], self.pos[1] + self.dir[1], self.t - 4, self.t - 4)
        if not any(nr.colliderect(m) for m in self.walls):
            self.pos[0] += self.dir[0];
            self.pos[1] += self.dir[1]

        self._mouth = (self._mouth + 2) % 60  # boucle de frame pour la bouche

        if self.power_timer > 0: self.power_timer -= 1

        pr = pygame.Rect(self.pos[0], self.pos[1], self.t - 4, self.t - 4)

        # fantomes (completement full random au bord des murs)
        for g in self.ghosts:
            gr = pygame.Rect(g[0] + g[2][0], g[1] + g[2][1], self.t - 4, self.t - 4)

            if any(gr.colliderect(m) for m in self.walls):
                # choppe une nvl dir si ca tape un mur
                g[2] = random.choice([[1, 0], [-1, 0], [0, 1], [0, -1]])
            else:
                g[0] += g[2][0];
                g[1] += g[2][1]

            # collision hitbox pacman vs fantome
            hit = pr.colliderect(pygame.Rect(g[0], g[1], self.t - 4, self.t - 4))
            if hit:
                if self.power_timer > 0:
                    self.score += 200;
                    g[4] = True  # miam
                else:
                    self.game_over = True  # oups

        # maj de liste : on degage ceux dont is_dead (g[4]) = True
        self.ghosts = [g for g in self.ghosts if not g[4]]

        # bouffe les pac gums
        for p in self.dots[:]:
            if pr.colliderect(p): self.dots.remove(p); self.score += 10

        # les buffs
        for pu in self.power_ups[:]:
            if pr.colliderect(pu):
                self.power_ups.remove(pu);
                self.score += 50;
                self.power_timer = self._PDUP

        # si on a tout clean (listes vides) = lvl up direct
        if not self.dots and not self.power_ups:
            self.level += 1;
            self.reset()

    def draw(self, surf):
        t_anim = pygame.time.get_ticks() / 1000.0
        draw_game_bg(surf)

        # ptite vague en bg
        draw_wave_line(surf, H_INTERNE - 40, t_anim, color=(0, 160, 200), alpha=80)

        # rendu des murs en mode planches cabane
        for m in self.walls:
            pygame.draw.rect(surf, BOIS, m, border_radius=3)
            pygame.draw.rect(surf, BOIS_FONC, m, 1, border_radius=3)
            # 1 px line pour faire une fausse veine de bois au milieu
            pygame.draw.line(surf, SABLE2,
                             (m.x + 3, m.y + m.h // 2), (m.x + m.w - 3, m.y + m.h // 2), 1)

        # pts = coquillages sur la map
        for p in self.dots:
            pygame.draw.ellipse(surf, SABLE, (p.x - 1, p.y - 1, 6, 5))
            pygame.draw.ellipse(surf, BLANC, (p.x, p.y, 3, 2))

        # powerup = etoile qui clignote ac sinusoides
        for pu in self.power_ups:
            pulse = int(5 + 2 * math.sin(t_anim * 3))
            cx, cy = pu.centerx, pu.centery
            pts = []
            for k in range(10):
                angle = math.radians(k * 36 - 90)
                r = pulse if k % 2 == 0 else pulse // 2
                pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
            pygame.draw.polygon(surf, ORANGE, pts)
            pygame.draw.polygon(surf, SOLEIL, pts, 1)

        # sprite pacman (fait avec les primitives pygame)
        cx, cy = int(self.pos[0] + 11), int(self.pos[1] + 11)

        # recup l'angle pour savoir vers ou il regarde
        d = self.dir if any(self.dir) else [1, 0]
        ang = (0 if d[0] > 0 else 180 if d[0] < 0 else 90 if d[1] > 0 else 270)
        mo = 20 + self._mouth // 3  # l'anim de l'ouverture

        pygame.draw.circle(surf, SOLEIL, (cx, cy), 10)

        # c'est juste un polygone bleu par dessus pour cacher le jaune et "faire la bouche" (big brain)
        pygame.draw.polygon(surf, MER_FONC, [
            (cx, cy),
            (cx + int(10 * math.cos(math.radians(ang - mo))),
             cy + int(10 * math.sin(math.radians(ang - mo)))),
            (cx + int(10 * math.cos(math.radians(ang + mo))),
             cy + int(10 * math.sin(math.radians(ang + mo)))),
        ])

        # petit oeil
        eye_angle = math.radians(ang - 55)
        ex = cx + int(5 * math.cos(eye_angle))
        ey = cy + int(5 * math.sin(eye_angle))
        pygame.draw.circle(surf, BRUN, (ex, ey), 2)

        # FX pour faire le style soleil
        for i in range(8):
            ra = math.radians(i * 45 + t_anim * 60)
            x1 = cx + int(11 * math.cos(ra));
            y1 = cy + int(11 * math.sin(ra))
            x2 = cx + int(15 * math.cos(ra));
            y2 = cy + int(15 * math.sin(ra))
            pygame.draw.line(surf, ORANGE, (x1, y1), (x2, y2), 2)

        # fantomes
        ghost_cols = {
            "red": ROUGE_VIF,
            "pink": ROSE,
        }
        for g in self.ghosts:
            gcx, gcy = int(g[0] + 11), int(g[1] + 11)

            if self.power_timer > 0:
                # switch de couleurs a l'arrache via list d'index pcq is_scared
                rb = [MER, ORANGE, SOLEIL, MER]
                gc = rb[(self.power_timer // 8) % len(rb)]
            else:
                gc = ghost_cols.get(g[3], ROSE)

            # le corp de base
            pygame.draw.circle(surf, gc, (gcx, gcy - 2), 9)
            pygame.draw.rect(surf, gc, (gcx - 9, gcy - 2, 18, 12))

            # les 4 ptites vaguelettes en bas
            for i in range(4):
                pygame.draw.circle(surf, gc, (gcx - 7 + i * 5, gcy + 10), 4)

            if self.power_timer <= 0:
                # normal eyes
                for ox in (-3, 3):
                    pygame.draw.circle(surf, BLANC, (gcx + ox, gcy - 1), 3)
                    pygame.draw.circle(surf, BRUN, (gcx + ox, gcy - 1), 1)
            else:
                # yeux de flipé en croix
                for ox in (-3, 3):
                    pygame.draw.line(surf, BLANC,
                                     (gcx + ox - 2, gcy - 3), (gcx + ox + 2, gcy + 1), 1)
                    pygame.draw.line(surf, BLANC,
                                     (gcx + ox + 2, gcy - 3), (gcx + ox - 2, gcy + 1), 1)

        # Ui 
        draw_wood_panel(surf, (6, 6, 160, 26), radius=5)
        surf.blit(font_small.render(f"SCORE: {self.score}", True, BRUN), (12, 10))

        draw_wood_panel(surf, (L_INTERNE // 2 - 60, 6, 120, 26), radius=5)
        surf.blit(font_small.render(f"NIVEAU: {self.level}", True, BRUN),
                  (L_INTERNE // 2 - font_small.size(f"NIVEAU: {self.level}")[0] // 2, 10))

        if self.power_timer > 0:
            draw_wood_panel(surf, (L_INTERNE - 150, 6, 144, 26), radius=5)
            pt = font_small.render(f"POWER: {self.power_timer // 60 + 1}s", True, ORANGE)
            surf.blit(pt, (L_INTERNE - 144, 10))

        ht = font_small.render("Fleches = direction", True, SABLE)
        surf.blit(ht, (L_INTERNE // 2 - ht.get_width() // 2, H_INTERNE - 18))

        if self.game_over:
            draw_game_over(surf, font_main)