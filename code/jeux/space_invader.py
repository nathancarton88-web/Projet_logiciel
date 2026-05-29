# space_invader.py



import pygame, random, math

# import du theme 
from jeux.ete_theme import (draw_game_bg, draw_wood_panel, draw_wave_line,
                            draw_game_over, BLANC, BRUN, BRUN2, MER, SABLE,
                            SABLE2, SOLEIL, ORANGE, ROUGE_VIF, VERT_PALM, ROSE,
                            JAUNE_VIF, BOIS, BOIS_FONC)

pygame.init()

# taille de l'ecran d'arcade 
L_INTERNE, H_INTERNE = 700, 500

try:
    font_pixel = pygame.font.SysFont("Courier New", 17, bold=True)
    font_main = pygame.font.SysFont("Courier New", 32, bold=True)
    font_small = pygame.font.SysFont("Courier New", 13)
except Exception as e:
    print("font crash space:", e)
    font_pixel = pygame.font.Font(None, 20)
    font_main = pygame.font.Font(None, 36)
    font_small = pygame.font.Font(None, 16)


class SpaceInvaders:

    W_MOB, H_MOB = 36, 24  
    ESPACE_X, ESPACE_Y = 58, 42  
    COL, LIG = 5, 3  
    S_BLOC = 6  # taille des ptits carre de sable
    COL_BOUCLIER, LIG_BOUCLIER = 7, 4  
    W_JOUEUR, H_JOUEUR = 44, 22 

    def __init__(self):
        self.full_reset()

    def full_reset(self):
        self.level = 1
        self.score = 0
        self.reset()

    def reset(self):
        # respawn du joueur
        self.px = L_INTERNE // 2 - self.W_JOUEUR // 2
        self.py = H_INTERNE - 65
        self.timer_tir = 0  

        self.tirs_vaisseau = []  
        self.tirs_mobs = []  
        self.mobs = self.genere_ennemis()
        self.bunkers = self.genere_bunkers()

        self.boss = None
        self.dir_boss = 1
        self.timer_boss = 0

        self.dir_groupe = 1 # 1 = droite, -1 = gauche

        #  mobs qui accelere avec le niveau (math.max pour pas que ca freeze)
        self.timer_mouv = 0
        self.interval_mouv = max(18, 55 - self.level * 4)
        self.timer_eshoot = 0
        self.interval_eshoot = max(22, 80 - self.level * 6)

        self.game_over = False

    def genere_ennemis(self):
        # calcul savant pour centrer la grille
        sx = (L_INTERNE - self.COL * self.ESPACE_X) // 2
        return [
            {'rect': pygame.Rect(sx + c * self.ESPACE_X, 65 + r * self.ESPACE_Y, self.W_MOB, self.H_MOB), 'type': r}
            for r in range(self.LIG) for c in range(self.COL)
        ]

    def genere_bunkers(self):
        n = 3 # nombre de bunkers
        w_total = self.COL_BOUCLIER * self.S_BLOC  
        espace = (L_INTERNE - n * w_total) // (n + 1)  
        sy = self.py - 85 


        return [
            pygame.Rect(espace + i * (w_total + espace) + c * self.S_BLOC, sy + r * self.S_BLOC, self.S_BLOC, self.S_BLOC)
            for i in range(n) for r in range(self.LIG_BOUCLIER) for c in range(self.COL_BOUCLIER)
        ]

    def spawn_boss(self):
        hp = 10 + self.level * 5  # ptit buff de sac a pv 
        return {
            'rect': pygame.Rect(L_INTERNE // 2 - 65, 28, 130, 44),
            'hp': hp, 'mhp': hp  
        }

    def shoot(self):
        if self.timer_tir <= 0:
            self.tirs_vaisseau.append(pygame.Rect(self.px + self.W_JOUEUR // 2 - 2, self.py - 10, 4, 10))
            self.timer_tir = 18 



    def update(self, dt=0):
        if self.game_over: return

        touches = pygame.key.get_pressed()
        if touches[pygame.K_LEFT] and self.px > 0:
            self.px -= 4
        if touches[pygame.K_RIGHT] and self.px < L_INTERNE - self.W_JOUEUR:
            self.px += 4

        if self.timer_tir > 0: self.timer_tir -= 1

        for b in self.tirs_vaisseau[:]:
            b.y -= 7
            if b.bottom < 0: self.tirs_vaisseau.remove(b)  # despawn

        for b in self.tirs_mobs[:]:
            b.y += 4 + self.level // 2  
            if b.top > H_INTERNE: self.tirs_mobs.remove(b)

        # deplacement de l'armee
        self.timer_mouv += 1
        if self.timer_mouv >= self.interval_mouv and self.mobs:
            self.timer_mouv = 0

            # on check les extremites
            lx = min(e['rect'].x for e in self.mobs)
            rx = max(e['rect'].right for e in self.mobs)

            # rebond contre les murs de l'ecran
            if rx + self.dir_groupe * 14 > L_INTERNE - 5 or lx + self.dir_groupe * 14 < 5:
                self.dir_groupe *= -1
                for e in self.mobs: e['rect'].y += 14 # on descend d'un cran

            for e in self.mobs: e['rect'].x += self.dir_groupe * 14

        # rng du tireur
        self.timer_eshoot += 1
        if self.timer_eshoot >= self.interval_eshoot and self.mobs:
            self.timer_eshoot = 0
            tireur = random.choice(self.mobs)  
            self.tirs_mobs.append(pygame.Rect(tireur['rect'].centerx - 2, tireur['rect'].bottom, 4, 8))


        if self.boss:
            self.boss['rect'].x += self.dir_boss * 2
            if self.boss['rect'].left < 5 or self.boss['rect'].right > L_INTERNE - 5:
                self.dir_boss *= -1

            self.timer_boss += 1
            if self.timer_boss >= 38: # cadence de tir
                self.timer_boss = 0
                bx, by = self.boss['rect'].centerx, self.boss['rect'].bottom

                # triple shot eventail
                for ox in (-22, 0, 22):
                    self.tirs_mobs.append(pygame.Rect(bx + ox - 2, by, 4, 8))




        # ce qu'on touche 
        for b in self.tirs_vaisseau[:]:
            
            idx = b.collidelist(self.bunkers)
            if idx != -1:
                self.bunkers.pop(idx)  # paf
                self.tirs_vaisseau.remove(b)  
                continue

            idx = b.collidelist([e['rect'] for e in self.mobs])
            if idx != -1:
                mob_tue = self.mobs.pop(idx)  
                self.score += (3 - mob_tue['type']) * 10 * self.level  
                self.tirs_vaisseau.remove(b)
                continue

            if self.boss and b.colliderect(self.boss['rect']):
                self.boss['hp'] -= 1
                if self.boss['hp'] <= 0:
                    self.boss = None 
                    self.score += 500 * self.level
                self.tirs_vaisseau.remove(b)

        # ce qui nous touche 
        rect_joueur = pygame.Rect(self.px, self.py, self.W_JOUEUR, self.H_JOUEUR)
        for b in self.tirs_mobs[:]:

            idx = b.collidelist(self.bunkers)
            if idx != -1:
                self.bunkers.pop(idx)
                self.tirs_mobs.remove(b)
                continue

            if b.colliderect(rect_joueur):
                self.game_over = True
                return

        # Game over si les mobs touchent le sol
        if self.mobs and max(e['rect'].bottom for e in self.mobs) >= self.py:
            self.game_over = True
            return

        # spawn du boss ou level up
        if not self.mobs and not self.boss:
            self.boss = self.spawn_boss()
        elif self.boss is None and not self.mobs:
            self.level += 1
            self.reset()


    
    def dessine_mob(self, surf, e):
        # skin des mobs selon la ligne (meduse, crabe, poisson) en théorie mdr
        col = [ROSE, MER, VERT_PALM][e['type']]
        x, y, w, h = e['rect'].x, e['rect'].y, self.W_MOB, self.H_MOB

        if e['type'] == 0:
            pygame.draw.ellipse(surf, col, (x + 4, y, w - 8, h - 6))
            for i in range(5):
                pygame.draw.line(surf, col, (x + 6 + i * 5, y + h - 6), (x + 4 + i * 5, y + h + 4), 2)
            pygame.draw.circle(surf, BLANC, (x + 11, y + 8), 3)
            pygame.draw.circle(surf, BLANC, (x + w - 11, y + 8), 3)
        elif e['type'] == 1:
            pygame.draw.rect(surf, col, (x + 4, y + 4, w - 8, h - 8), border_radius=4)
            pygame.draw.rect(surf, col, (x, y + 6, 8, 8), border_radius=2)
            pygame.draw.rect(surf, col, (x + w - 8, y + 6, 8, 8), border_radius=2)
            pygame.draw.circle(surf, BLANC, (x + 11, y + h // 2), 3)
            pygame.draw.circle(surf, BLANC, (x + w - 11, y + h // 2), 3)
            pygame.draw.circle(surf, BRUN, (x + 11, y + h // 2), 1)
            pygame.draw.circle(surf, BRUN, (x + w - 11, y + h // 2), 1)
        else:
            pygame.draw.ellipse(surf, col, (x + 2, y, w - 4, h))
            for i in range(4):
                pygame.draw.line(surf, col, (x + 5 + i * 8, y + h), (x + 3 + i * 8, y + h + 6), 2)
            pygame.draw.circle(surf, BLANC, (x + w - 8, y + h // 2 - 2), 4)
            pygame.draw.circle(surf, BRUN, (x + w - 8, y + h // 2 - 2), 2)

    def draw(self, surf):
        t = pygame.time.get_ticks() / 1000.0
        draw_game_bg(surf)
        draw_wave_line(surf, H_INTERNE - 50, t, color=(0, 160, 180), alpha=100)

        # dessin des boucliers opti
        for bloc in self.bunkers:
            pygame.draw.rect(surf, SABLE, bloc, border_radius=2)
            pygame.draw.rect(surf, SABLE2, bloc, 1, border_radius=2)

        for e in self.mobs:
            self.dessine_mob(surf, e)

        # rendu du requin carre (lol)
        if self.boss:
            r_boss = self.boss['rect']
            x, y, w, h = r_boss.x, r_boss.y, r_boss.w, r_boss.h

            pygame.draw.rect(surf, (80, 80, 100), r_boss, border_radius=8)
            pygame.draw.rect(surf, (120, 120, 150), (x + 6, y + 6, w - 12, h // 2), border_radius=4)
            pygame.draw.polygon(surf, (60, 60, 80), [(x + w // 2, y - 20), (x + w // 2 - 12, y), (x + w // 2 + 12, y)])

            for ox in (-24, 24):
                pygame.draw.circle(surf, JAUNE_VIF, (x + w // 2 + ox, y + h // 2), 7)
                pygame.draw.circle(surf, BRUN, (x + w // 2 + ox, y + h // 2), 4)

            # jauge de vie 
            hp_w = int(w * self.boss['hp'] / self.boss['mhp'])
            pygame.draw.rect(surf, ROUGE_VIF, (x, y - 14, w, 8)) 
            pygame.draw.rect(surf, VERT_PALM, (x, y - 14, hp_w, 8)) 
            pygame.draw.rect(surf, BLANC, (x, y - 14, w, 8), 1)  

            draw_wood_panel(surf, (x + w // 2 - 22, y - 30, 44, 16), radius=4)
            surf.blit(font_small.render("BOSS", True, ROUGE_VIF), (x + w // 2 - 18, y - 28))


        # notre bateau super en polygone
        px, py2 = self.px, self.py
        pygame.draw.polygon(surf, BOIS, [
            (px, py2 + self.H_JOUEUR), (px + self.W_JOUEUR, py2 + self.H_JOUEUR),
            (px + self.W_JOUEUR - 4, py2 + self.H_JOUEUR - 10), (px + 4, py2 + self.H_JOUEUR - 10)
        ])
        pygame.draw.polygon(surf, SABLE, [
            (px + self.W_JOUEUR // 2, py2), (px + self.W_JOUEUR // 2 - 8, py2 + self.H_JOUEUR - 12),
            (px + self.W_JOUEUR // 2 + 8, py2 + self.H_JOUEUR - 12)
        ])
        pygame.draw.rect(surf, BOIS_FONC, (px + self.W_JOUEUR // 2 - 2, py2 + self.H_JOUEUR - 12, 4, 12))

        # FX tirs
        for b in self.tirs_vaisseau:
            pygame.draw.rect(surf, SOLEIL, b, border_radius=2)
            pygame.draw.circle(surf, ORANGE, (b.centerx, b.y), 3)

        for b in self.tirs_mobs:
            pygame.draw.ellipse(surf, MER, (b.x - 1, b.y - 2, 6, 10))
            pygame.draw.ellipse(surf, BLANC, (b.x + 1, b.y, 2, 4))

        # UI
        draw_wood_panel(surf, (6, 6, 160, 26), radius=5)
        surf.blit(font_small.render(f"SCORE: {self.score}", True, BRUN), (12, 10))

        draw_wood_panel(surf, (L_INTERNE - 150, 6, 144, 26), radius=5)
        surf.blit(font_small.render(f"VAGUE: {self.level}", True, BRUN), (L_INTERNE - 144, 10))

        ht = font_small.render("<- -> deplacer   ESPACE tirer", True, SABLE)
        surf.blit(ht, (L_INTERNE // 2 - ht.get_width() // 2, H_INTERNE - 18))

        if self.game_over:
            draw_game_over(surf, font_main)