import pygame,random
pygame.init()
# les COULEURS
NOIR_CHASSIS = (20, 20, 22);  ECRAN_OFF   = (5, 5, 10)
JOYCON_BLEU  = (0, 190, 230); JOYCON_ROUGE= (255, 60, 50)
BLANC = (255, 255, 255);      CYAN  = (0, 255, 255)
JAUNE = (255, 230, 0);        VERT  = (50, 255, 80)
GRIS_BOUTON = (50, 50, 55)
L_ECRAN, H_ECRAN   = 1000, 600
L_INTERNE, H_INTERNE = 700, 500
X_DEBUT, Y_DEBUT   = 150, 50

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




class SpaceInvaders:
    EW, EH   = 36, 24     # enemy tile
    ESX, ESY = 58, 42     # enemy step x/y
    EC, ER   = 5, 3       # enemy cols/rows
    SBK      = 6          # shield block px
    SCO, SRO = 7, 4       # shield cols/rows
    PW, PH   = 44, 22     # player

    def __init__(self):
        self.level = 1;  self.score = 0;  self.game_over = False
        self.reset()

    def reset(self):
        """Full reset (level & score kept, use for wave restart).
        Called directly resets wave; full new game needs prior level/score reset."""
        self.px   = L_INTERNE // 2 - self.PW // 2
        self.py   = H_INTERNE - 65
        self.pbullets = [];  self.ebullets = []
        self.cooldown = 0
        self.enemies  = self._mk_enemies()
        self.shields  = self._mk_shields()
        self.boss     = None;  self.boss_dir = 1;  self.boss_st = 0
        self.edir     = 1
        self.emove_t  = 0;  self.emove_i = max(18, 55 - self.level*4)
        self.eshoot_t = 0;  self.eshoot_i= max(22, 80 - self.level*6)
        self.game_over= False

    def full_reset(self):
        self.level = 1;  self.score = 0
        self.reset()

    def _mk_enemies(self):
        sx = (L_INTERNE - self.EC*self.ESX) // 2
        en = []
        for r in range(self.ER):
            for c in range(self.EC):
                en.append({'x': sx+c*self.ESX, 'y': 65+r*self.ESY, 'alive': True, 'type': r})
        return en

    def _mk_shields(self):
        n = 3;  sw = self.SCO * self.SBK
        sp = (L_INTERNE - n*sw) // (n+1)
        sy = self.py - 85
        shields = []
        for i in range(n):
            x = sp + i*(sw+sp)
            shields.append({'x': x, 'y': sy, 'blocks': [[True]*self.SCO for _ in range(self.SRO)]})
        return shields

    def _mk_boss(self):
        hp = 10 + self.level * 5
        return {'x': L_INTERNE//2-65, 'y': 28, 'w': 130, 'h': 44, 'hp': hp, 'mhp': hp, 'alive': True}

    def shoot(self):
        if self.cooldown <= 0:
            self.pbullets.append({'x': self.px+self.PW//2, 'y': self.py})
            self.cooldown = 18

    def update(self, dt):
        if self.game_over: return
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]  and self.px > 0:             self.px -= 4
        if keys[pygame.K_RIGHT] and self.px < L_INTERNE-self.PW: self.px += 4
        if self.cooldown > 0: self.cooldown -= 1
        # Move bullets
        for b in self.pbullets[:]:
            b['y'] -= 7
            if b['y'] < 0: self.pbullets.remove(b)
        for b in self.ebullets[:]:
            b['y'] += 4 + self.level // 2
            if b['y'] > H_INTERNE: self.ebullets.remove(b)
        # Move enemies
        self.emove_t += 1
        if self.emove_t >= self.emove_i:
            self.emove_t = 0
            alive = [e for e in self.enemies if e['alive']]
            if alive:
                lx = min(e['x'] for e in alive)
                rx = max(e['x']+self.EW for e in alive)
                if rx + self.edir*14 > L_INTERNE-5 or lx + self.edir*14 < 5:
                    self.edir *= -1
                    for e in self.enemies: e['y'] += 14
                for e in self.enemies: e['x'] += self.edir * 14
        # Enemy shooting
        self.eshoot_t += 1
        if self.eshoot_t >= self.eshoot_i:
            self.eshoot_t = 0
            alive = [e for e in self.enemies if e['alive']]
            if alive:
                s = random.choice(alive)
                self.ebullets.append({'x': s['x']+self.EW//2, 'y': s['y']+self.EH})
        # Boss
        if self.boss and self.boss['alive']:
            self.boss['x'] += self.boss_dir * 2
            if self.boss['x'] < 5 or self.boss['x']+self.boss['w'] > L_INTERNE-5:
                self.boss_dir *= -1
            self.boss_st += 1
            if self.boss_st >= 38:
                self.boss_st = 0
                for ox in (-22, 0, 22):
                    self.ebullets.append({'x': self.boss['x']+self.boss['w']//2+ox,
                                          'y': self.boss['y']+self.boss['h']})
        # Player bullet collisions
        for b in self.pbullets[:]:
            if b not in self.pbullets: continue
            hit = False
            # vs enemies
            for e in self.enemies:
                if e['alive']:
                    if b['x']>=e['x'] and b['x']<=e['x']+self.EW and b['y']>=e['y'] and b['y']<=e['y']+self.EH:
                        e['alive'] = False;  self.score += (3-e['type'])*10*self.level;  hit = True;  break
            # vs boss
            if not hit and self.boss and self.boss['alive']:
                bss = self.boss
                if b['x']>=bss['x'] and b['x']<=bss['x']+bss['w'] and b['y']>=bss['y'] and b['y']<=bss['y']+bss['h']:
                    bss['hp'] -= 1;  hit = True
                    if bss['hp'] <= 0: bss['alive'] = False;  self.score += 500*self.level
            # vs shields
            if not hit:
                br = pygame.Rect(b['x']-2, b['y']-8, 4, 8)
                for sh in self.shields:
                    if hit: break
                    for r in range(self.SRO):
                        if hit: break
                        for c in range(self.SCO):
                            if sh['blocks'][r][c]:
                                blk = pygame.Rect(sh['x']+c*self.SBK, sh['y']+r*self.SBK, self.SBK, self.SBK)
                                if br.colliderect(blk): sh['blocks'][r][c]=False; hit=True; break
            if hit and b in self.pbullets: self.pbullets.remove(b)
        # Enemy bullets vs shields
        for b in self.ebullets[:]:
            if b not in self.ebullets: continue
            br = pygame.Rect(b['x']-2, b['y']-4, 4, 8)
            hit = False
            for sh in self.shields:
                if hit: break
                for r in range(self.SRO):
                    if hit: break
                    for c in range(self.SCO):
                        if sh['blocks'][r][c]:
                            blk = pygame.Rect(sh['x']+c*self.SBK, sh['y']+r*self.SBK, self.SBK, self.SBK)
                            if br.colliderect(blk): sh['blocks'][r][c]=False; hit=True; break
            if hit and b in self.ebullets: self.ebullets.remove(b)
        # Enemy bullet vs player
        pr = pygame.Rect(self.px, self.py, self.PW, self.PH)
        for b in self.ebullets:
            if pygame.Rect(b['x']-2, b['y']-4, 4, 8).colliderect(pr):
                self.game_over = True;  return
        # Enemies reach bottom
        for e in self.enemies:
            if e['alive'] and e['y']+self.EH >= self.py:
                self.game_over = True;  return
        # Wave check
        alive = [e for e in self.enemies if e['alive']]
        if not alive and not self.boss:
            self.boss = self._mk_boss()
        elif self.boss and not self.boss['alive']:
            self.level += 1;  self.reset()

    def _draw_enemy(self, surf, e):
        col = [(180,50,220), (50,200,220), (50,220,80)][e['type']]
        x, y, w, h = e['x'], e['y'], self.EW, self.EH
        if e['type'] == 0:
            pygame.draw.rect(surf, col, (x+8, y, w-16, h//2+2))
            pygame.draw.rect(surf, col, (x, y+h//2, w, h//2))
            pygame.draw.rect(surf, ECRAN_OFF, (x+4, y+h//4, 6, 6))
            pygame.draw.rect(surf, ECRAN_OFF, (x+w-10, y+h//4, 6, 6))
        elif e['type'] == 1:
            pygame.draw.rect(surf, col, (x+4, y+4, w-8, h-8))
            pygame.draw.rect(surf, col, (x, y+6, 8, 8))
            pygame.draw.rect(surf, col, (x+w-8, y+6, 8, 8))
            pygame.draw.circle(surf, ECRAN_OFF, (x+11, y+h//2), 3)
            pygame.draw.circle(surf, ECRAN_OFF, (x+w-11, y+h//2), 3)
        else:
            pygame.draw.ellipse(surf, col, (x+2, y, w-4, h))
            for i in range(4): pygame.draw.line(surf, col, (x+5+i*8, y+h), (x+3+i*8, y+h+6), 2)

    def draw(self, surf):
        surf.fill((4, 4, 18))
        # Shields
        for sh in self.shields:
            for r in range(self.SRO):
                for c in range(self.SCO):
                    if sh['blocks'][r][c]:
                        pygame.draw.rect(surf, (45, 200, 45),
                                         (sh['x']+c*self.SBK, sh['y']+r*self.SBK, self.SBK-1, self.SBK-1))
        # Enemies
        for e in self.enemies:
            if e['alive']: self._draw_enemy(surf, e)
        # Boss
        if self.boss and self.boss['alive']:
            bss = self.boss
            x,y,w,h = bss['x'],bss['y'],bss['w'],bss['h']
            pygame.draw.rect(surf, (200,30,30), (x,y,w,h), border_radius=6)
            pygame.draw.rect(surf, (255,80,80), (x+6,y+6,w-12,h//2), border_radius=3)
            for ox in (-30, 30):
                pygame.draw.circle(surf, JAUNE, (x+w//2+ox, y+h//2), 7)
                pygame.draw.circle(surf, (0,0,0), (x+w//2+ox, y+h//2), 4)
            hp_w = int(w * bss['hp'] / bss['mhp'])
            pygame.draw.rect(surf, (80,0,0), (x, y-13, w, 8))
            pygame.draw.rect(surf, (255,50,50), (x, y-13, hp_w, 8))
            pygame.draw.rect(surf, BLANC, (x, y-13, w, 8), 1)
            surf.blit(font_pixel.render("BOSS", True,(255,100,100)), (x+w//2-18, y-27))
        # Player
        px, py = self.px, self.py
        pygame.draw.polygon(surf, CYAN, [(px+self.PW//2,py),(px,py+self.PH),(px+self.PW,py+self.PH)])
        pygame.draw.rect(surf, JOYCON_BLEU, (px+self.PW//2-5, py+self.PH-9, 10, 9))
        # Bullets
        for b in self.pbullets: pygame.draw.rect(surf, CYAN,        (b['x']-2, b['y']-8, 4, 8))
        for b in self.ebullets: pygame.draw.rect(surf, (255,50,50), (b['x']-2, b['y']-4, 4, 8))
        # UI
        surf.blit(font_pixel.render(f"SCORE:{self.score}", True, BLANC), (10, 10))
        surf.blit(font_pixel.render(f"VAGUE:{self.level}", True, CYAN),  (L_INTERNE-140, 10))
        surf.blit(font_pixel.render("← → deplacer   ESPACE tirer", True,(55,55,75)), (10, H_INTERNE-20))
        if self.game_over:
            msg = font_main.render("GAME OVER – ESC", True, JOYCON_ROUGE)
            surf.blit(msg, (L_INTERNE//2 - msg.get_width()//2, H_INTERNE//2 - 20))
