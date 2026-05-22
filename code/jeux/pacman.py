import pygame,math,random


pygame.init()
L_ECRAN, H_ECRAN   = 1000, 600
L_INTERNE, H_INTERNE = 700, 500
X_DEBUT, Y_DEBUT   = 150, 50

# les COULEURS
NOIR_CHASSIS = (20, 20, 22);  ECRAN_OFF   = (5, 5, 10)
JOYCON_BLEU  = (0, 190, 230); JOYCON_ROUGE= (255, 60, 50)
BLANC = (255, 255, 255);      CYAN  = (0, 255, 255)
JAUNE = (255, 230, 0);        VERT  = (50, 255, 80)
GRIS_BOUTON = (50, 50, 55)

# les  POLICES
try:
    font_sys   = pygame.font.SysFont("Segoe UI", 22, bold=True)
    font_main  = pygame.font.SysFont("Segoe UI", 35, bold=True)
    font_pixel = pygame.font.SysFont("Consolas", 20)
    font_large = pygame.font.SysFont("Segoe UI", 55, bold=True)
except Exception:
    font_sys   = pygame.font.Font(None, 24)
    font_main  = pygame.font.Font(None, 40)
    font_pixel = pygame.font.Font(None, 20)
    font_large = pygame.font.Font(None, 65)


class Pacman:
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
        self.t = 22;  self.level = 1;  self.score = 0
        self._mouth = 0;  self._PDUP = 300
        self.game_over = False
        self.reset()

    def reset(self):
        self.walls = []; self.dots = []; self.power_ups = []
        self.game_over = False;  self.power_timer = 0
        self.ghosts = []
        for r, row in enumerate(self.PLAN):
            for c, ch in enumerate(row):
                rx, ry = c*self.t+119, r*self.t+173
                rect = pygame.Rect(rx, ry, self.t, self.t)
                if   ch == '1': self.walls.append(rect)
                elif ch == '2': self.dots.append(pygame.Rect(rect.centerx-2, rect.centery-2, 4, 4))
                elif ch == 'P': self.pos = [rect.x, rect.y]
                elif ch == 'G':
                    self.ghosts.append([rect.x, rect.y, [1,0], "red",  False])
                    self.ghosts.append([rect.x, rect.y, [-1,0],"pink", False])
        self.power_ups = [pygame.Rect(141,195,8,8), pygame.Rect(537,195,8,8),
                          pygame.Rect(141,283,8,8), pygame.Rect(537,283,8,8)]
        self.dir = [0,0];  self.next_dir = [0,0]

    def update(self):
        if self.game_over: return
        if any(self.next_dir):
            nr = pygame.Rect(self.pos[0]+self.next_dir[0], self.pos[1]+self.next_dir[1], self.t-4, self.t-4)
            if not any(nr.colliderect(m) for m in self.walls):
                self.dir = self.next_dir[:];  self.next_dir = [0,0]
        nr = pygame.Rect(self.pos[0]+self.dir[0], self.pos[1]+self.dir[1], self.t-4, self.t-4)
        if not any(nr.colliderect(m) for m in self.walls):
            self.pos[0] += self.dir[0];  self.pos[1] += self.dir[1]
        self._mouth = (self._mouth + 2) % 60
        if self.power_timer > 0: self.power_timer -= 1
        pr = pygame.Rect(self.pos[0], self.pos[1], self.t-4, self.t-4)
        for g in self.ghosts:
            gr = pygame.Rect(g[0]+g[2][0], g[1]+g[2][1], self.t-4, self.t-4)
            if any(gr.colliderect(m) for m in self.walls):
                g[2] = random.choice([[1,0],[-1,0],[0,1],[0,-1]])
            else:
                g[0] += g[2][0];  g[1] += g[2][1]
            hit = pr.colliderect(pygame.Rect(g[0], g[1], self.t-4, self.t-4))
            if hit:
                if self.power_timer > 0: self.score += 200; g[4] = True
                else: self.game_over = True
        self.ghosts = [g for g in self.ghosts if not g[4]]
        for p in self.dots[:]:
            if pr.colliderect(p): self.dots.remove(p); self.score += 10
        for pu in self.power_ups[:]:
            if pr.colliderect(pu):
                self.power_ups.remove(pu); self.score += 50; self.power_timer = self._PDUP
        if not self.dots and not self.power_ups:
            self.level += 1; self.reset()

    def draw(self, surf):
        for m in self.walls:  pygame.draw.rect(surf, (0,0,150), m, border_radius=4)
        for p in self.dots:   pygame.draw.circle(surf, (255,200,150), p.center, 2)
        for pu in self.power_ups: pygame.draw.circle(surf, JAUNE, pu.center, 5)
        # Pacman
        cx, cy = int(self.pos[0]+11), int(self.pos[1]+11)
        d = self.dir if any(self.dir) else [1,0]
        ang = (0 if d[0]>0 else 180 if d[0]<0 else 90 if d[1]>0 else 270)
        mo = 20 + self._mouth // 3
        pygame.draw.circle(surf, JAUNE, (cx, cy), 9)
        pygame.draw.polygon(surf, ECRAN_OFF, [
            (cx, cy),
            (cx + int(9*math.cos(math.radians(ang-mo))), cy + int(9*math.sin(math.radians(ang-mo)))),
            (cx + int(9*math.cos(math.radians(ang+mo))), cy + int(9*math.sin(math.radians(ang+mo)))),
        ])
        # Ghosts
        for g in self.ghosts:
            gcx, gcy = int(g[0]+11), int(g[1]+11)
            if self.power_timer > 0:
                rb = [(255,0,0),(0,255,255),(255,255,0),(0,100,255)]
                gc = rb[(self.power_timer // 8) % len(rb)]
            else:
                gc = JOYCON_ROUGE if g[3]=="red" else (255,184,255)
            pygame.draw.circle(surf, gc, (gcx, gcy-2), 8)
            pygame.draw.rect(surf, gc, (gcx-8, gcy-2, 16, 10))
            for i in range(4): pygame.draw.circle(surf, gc, (gcx-6+i*4, gcy+8), 3)
            if self.power_timer <= 0:
                pygame.draw.circle(surf, BLANC, (gcx-3, gcy-1), 2)
                pygame.draw.circle(surf, BLANC, (gcx+3, gcy-1), 2)
                pygame.draw.circle(surf, (0,0,0), (gcx-3, gcy-1), 1)
                pygame.draw.circle(surf, (0,0,0), (gcx+3, gcy-1), 1)
        surf.blit(font_pixel.render(f"SCORE:{self.score}", True, BLANC), (50, 25))
        surf.blit(font_pixel.render(f"LEVEL:{self.level}", True, CYAN),  (350, 25))
        if self.power_timer > 0:
            surf.blit(font_pixel.render(f"POWER:{self.power_timer//60+1}s", True, JAUNE), (200, 25))
        if self.game_over:
            msg = font_main.render("GAME OVER – ESC", True, JOYCON_ROUGE)
            surf.blit(msg, (150, 240))
