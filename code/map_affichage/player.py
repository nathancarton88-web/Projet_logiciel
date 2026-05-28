# player.py
# Gere le perso principal (mouvements, collisions, surf, et le menu pause)


import pygame
from entity import Entity, MODE_WALK, MODE_BIKE, MODE_RUN, MODE_SURF
from keylistener import KeyListener
from screen import Screen
from change import Change


SABLE      = (255, 210, 100)
SABLE_F    = (200, 150,  70)
MER        = (  0, 180, 200)
SOLEIL     = (255, 220,  50)
ORANGE     = (255, 140,   0)
MARRON     = ( 60,  30,   0)
MARRON_C   = (100,  60,  20)
BLANC      = (255, 248, 220)
ROUGE_VIF  = (255,  70,  50)
VERT_PALM  = ( 60, 200,  80)

# Variables globales pour les fonts
font_titre = None
font_mid   = None
font_small = None

def load_fonts_player():
    global font_titre, font_mid, font_small
    if font_titre is None:
        try:
            font_titre = pygame.font.SysFont("Courier New", 26, bold=True)
            font_mid   = pygame.font.SysFont("Courier New", 18, bold=True)
            font_small = pygame.font.SysFont("Courier New", 14)
        except Exception as e:
            print("erreur font player:", e)
            font_titre = pygame.font.Font(None, 30)
            font_mid   = pygame.font.Font(None, 22)
            font_small = pygame.font.Font(None, 18)

# Noms des jeux pour l'UI
LABELS_JEUX = {
    "tetris": "TETRIS au soleil",
    "pacman": "PAC-MAN a la playa",
    "snake":  "SNAKE de plage",
    "space":  "PLAGE invaders",
}


class Player(Entity):
    def __init__(self, keylistener, screen, x, y):
        super().__init__(keylistener, screen, x, y)
        self.pokedollars = 0 # ptet a virer si on s'en sert pas

        self.change = None
        self.collisions = None
        self.zones_eau = []   # liste des rects d'eau pour declencher le surf
        self.change_map = None
        self.jeu_proche = None

        # Setup menu pause
        self.menu_ouvert = False
        self.menu_index = 0
        self.options_menu = ["Scores", "Quitter vers menu", "Fermer"]
        self._highscores = {}   # recupéré depuis game.py

        self.est_sur_eau = False

    def update(self):
        # on bouge pas si le menu est affiché
        if not self.menu_ouvert:
            self.gestion_touches()
            self.gestion_mouvements()
        super().update()


    def gestion_touches(self):
        # Velo = B
        if self.keylistener.key_pressed(pygame.K_b):
            if self.mode == MODE_BIKE:
                self.switch_walk()
            elif self.mode == MODE_WALK or self.mode == MODE_RUN:
                self.switch_bike()
                self.switch_run(deactive=True)  #  plus de course si on courrait
            self.keylistener.remove_key(pygame.K_b)

        # Courir = R (marche pas dans l'eau ni a velo)
        if self.keylistener.key_pressed(pygame.K_r):
            if self.mode == MODE_RUN:
                self.switch_walk()
            elif self.mode == MODE_WALK:
                self.switch_run()
            self.keylistener.remove_key(pygame.K_r)

        # Surf = S (check zone eau d'abord)
        if self.keylistener.key_pressed(pygame.K_s):
            if self.mode == MODE_SURF:
                self.switch_walk()
            elif self.est_sur_eau and self.mode == MODE_WALK:
                self.switch_surf()
            self.keylistener.remove_key(pygame.K_s)


    def gestion_mouvements(self):
        self.jeu_proche = None
        self.est_sur_eau = self.check_flotte(self.hitbox)

        # bugfix: si on sort de l'eau en surfant ca remet a pied automatiquement
        if not self.est_sur_eau and self.mode == MODE_SURF:
            self.switch_walk()

        if self.animation_walk:
            return

        # copie la hitbox pour tester la collision avant de bouger le vrai perso
        temp_hitbox = self.hitbox.copy()

        # Vitesse
        if self.keylistener.key_pressed(pygame.K_LEFT):
            temp_hitbox.x -= 16
            if not self.verif_collisions(temp_hitbox):
                self.check_triggers(temp_hitbox)
                self.move_left()
            else:
                self.direction = "left"

        elif self.keylistener.key_pressed(pygame.K_RIGHT):
            temp_hitbox.x += 16
            if not self.verif_collisions(temp_hitbox):
                self.check_triggers(temp_hitbox)
                self.move_right()
            else:
                self.direction = "right"

        elif self.keylistener.key_pressed(pygame.K_UP):
            temp_hitbox.y -= 16
            if not self.verif_collisions(temp_hitbox):
                self.check_triggers(temp_hitbox)
                self.move_up()
            else:
                self.direction = "up"

        elif self.keylistener.key_pressed(pygame.K_DOWN):
            temp_hitbox.y += 16
            if not self.verif_collisions(temp_hitbox):
                self.check_triggers(temp_hitbox)
                self.move_down()
            else:
                self.direction = "down"

        else:
            # check si on est a coté d'un batiment arcade meme sans bouger
            self.check_proximite(self.hitbox.inflate(8, 8))


    def check_flotte(self, hb):
        for z in self.zones_eau:
            if hb.colliderect(z):
                return True
        return False


    def check_triggers(self, hitbox_test):
        if not self.change: return
        
        for zone in self.change:
            if zone.check_collision(hitbox_test):
                # trigger de changement de map (les portes)
                if zone.type == "switch":
                    self.change_map = zone
                # trigger pour jouer a une borne
                elif zone.type == "game":
                    self.jeu_proche = zone.name

    def check_proximite(self, zone_test):
        if not self.change: return
        for t in self.change:
            if t.type == "game" and t.check_collision(zone_test):
                self.jeu_proche = t.name
                return


    def add_switchs(self, lst_change):
        self.change = lst_change

    def add_collisions(self, lst_collisions):
        self.collisions = lst_collisions

    def add_water_zones(self, zones):
        self.zones_eau = zones

    def verif_collisions(self, hitbox_test):
        # Si on surfe, on ignore completement les blocs d'eau pour pouvoir avancer dedans
        for col in self.collisions:
            if hitbox_test.colliderect(col):
                if self.mode == MODE_SURF and self.check_flotte(hitbox_test):
                    continue
                return True
        return False



   # Menu (Touche M ou START)


    def open_menu(self):
        self.menu_ouvert = True
        self.menu_index = 0

    def close_menu(self):
        self.menu_ouvert = False

    def menu_up(self):
        self.menu_index = (self.menu_index - 1) % len(self.options_menu)

    def menu_down(self):
        self.menu_index = (self.menu_index + 1) % len(self.options_menu)

    def menu_confirm(self):
        choix = self.options_menu[self.menu_index]
        if choix == "Scores": return "scores"
        elif choix == "Quitter vers menu": return "quit_menu"
        else:
            self.close_menu()
            return "close"

    def draw_ingame_menu(self, surface, highscores):
        import math
        load_fonts_player()
        W, H = surface.get_size()
        t = pygame.time.get_ticks() / 1000.0

        # Filtre sombre arriere plan
        calque = pygame.Surface((W, H), pygame.SRCALPHA)
        calque.fill((20, 10, 0, 150))
        surface.blit(calque, (0, 0))

        # Panneau central en bois
        pw, ph = 480, 400
        px, py = W // 2 - pw // 2, H // 2 - ph // 2

        # Ombre 
        ombre = pygame.Surface((pw + 10, ph + 10), pygame.SRCALPHA)
        ombre.fill((0, 0, 0, 80))
        surface.blit(ombre, (px + 7, py + 7))

        pygame.draw.rect(surface, (210, 160, 75), (px, py, pw, ph), border_radius=10)
        
        # deco lignes bois
        for i in range(8):
            lx = px + 10 + i * (pw - 20) // 8
            pygame.draw.line(surface, (190, 140, 60), (lx, py + 8), (lx, py + ph - 8), 1)
            
        pygame.draw.rect(surface, (150, 100, 35), (px, py, pw, ph), 3, border_radius=10)
        
        # les ptits clous
        for cx, cy in [(px+14, py+14), (px+pw-14, py+14), (px+14, py+ph-14), (px+pw-14, py+ph-14)]:
            pygame.draw.circle(surface, (120, 80, 30), (cx, cy), 6)
            pygame.draw.circle(surface, (220, 180, 100), (cx-1, cy-1), 3)

        # Header menu
        pygame.draw.rect(surface, (180, 110, 40), (px + 20, py + 14, pw - 40, 34), border_radius=5)
        titre = font_titre.render("~  MENU  ~", True, BLANC)
        surface.blit(titre, (px + pw // 2 - titre.get_width() // 2, py + 18))

        for x in range(px + 20, px + pw - 20, 5):
            dy = int(2 * math.sin(x * 0.08 + t * 2))
            pygame.draw.circle(surface, MER, (x, py + 54 + dy), 1)

        # Affichage du transport actuel en haut a droite
        icones_mode = {
            MODE_WALK: ("MARCHE", (60, 180, 80)),
            MODE_BIKE: ("VELO",   (0, 180, 200)),
            MODE_RUN:  ("COURSE", (255, 140, 0)),
            MODE_SURF: ("SURF",   (0, 160, 220)),
        }
        if self.mode in icones_mode:
            lbl, col = icones_mode[self.mode]
            pygame.draw.rect(surface, col, (px + pw - 84, py + 16, 66, 22), border_radius=4)
            txt_mode = font_small.render(lbl, True, BLANC)
            # galere de ouf avec les coords pour centrer, pas toucher
            surface.blit(txt_mode, (px + pw - 84 + 33 - txt_mode.get_width()//2, py + 20))

        # SCORES
        y_score = py + 64
        pygame.draw.rect(surface, (0, 160, 180), (px + pw//2 - 80, y_score, 160, 22), border_radius=4)
        txt_hs = font_small.render("MEILLEURS SCORES", True, BLANC)
        surface.blit(txt_hs, (px + pw//2 - txt_hs.get_width()//2, y_score + 3))
        y_score += 30

        couleurs_barres = [(0, 200, 220), (255, 200, 0), (80, 220, 100), (255, 100, 60)]
        i = 0
        for id_jeu, libelle in LABELS_JEUX.items():
            pts = highscores.get(id_jeu, 0)
            largeur_max = pw - 80
            # on divise par 10 pour la width sinon ca deborde de la fenetre avec les gros scores 
            w_barre = min(int(pts / 10), largeur_max) 
            
            pygame.draw.rect(surface, (170, 120, 50), (px + 24, y_score, pw - 48, 28), border_radius=4)
            
            txt_lbl = font_small.render(libelle, True, MARRON)
            surface.blit(txt_lbl, (px + 30, y_score + 3))
            
            bx = px + 30
            by = y_score + 17
            pygame.draw.rect(surface, (150, 100, 40), (bx, by, pw - 60, 7), border_radius=3)
            if w_barre > 0:
                pygame.draw.rect(surface, couleurs_barres[i], (bx, by, w_barre, 7), border_radius=3)
                
            txt_pts = font_small.render(f"{pts} pts", True, MARRON)
            surface.blit(txt_pts, (px + pw - txt_pts.get_width() - 30, y_score + 3))
            
            y_score += 34
            i += 1

        for x in range(px + 20, px + pw - 20, 5):
            dy = int(2 * math.sin(x * 0.08 + t * 2 + 1.5))
            pygame.draw.circle(surface, SABLE_F, (x, y_score + 6 + dy), 1)
        y_score += 18

        # BOUTONS MENU
        couleurs_btn = [(255, 240, 180), (220, 248, 210), (255, 220, 210)]
        bordures_btn = [(200, 140, 50),  (50, 160, 60),   (200, 80, 60)]
        
        for index, opt in enumerate(self.options_menu):
            est_select = (index == self.menu_index)
            w, h = pw - 48, 30
            x_btn = px + 24
            
            if est_select:
                sh2 = pygame.Surface((w, h), pygame.SRCALPHA)
                sh2.fill((0, 0, 0, 40))
                surface.blit(sh2, (x_btn + 3, y_score + 3))
                
            pygame.draw.rect(surface, couleurs_btn[index], (x_btn, y_score, w, h), border_radius=5)
            epaisseur = 3 if est_select else 2
            pygame.draw.rect(surface, bordures_btn[index], (x_btn, y_score, w, h), epaisseur, border_radius=5)
            
            prefix = ">> " if est_select else "   "
            txt_opt = font_mid.render(prefix + opt, True, MARRON)
            surface.blit(txt_opt, (x_btn + w//2 - txt_opt.get_width()//2, y_score + h//2 - txt_opt.get_height()//2))
            
            y_score += 36

        info = font_small.render("↑↓ Naviguer   Entree Valider   Echap Fermer", True, MARRON_C)
        surface.blit(info, (px + pw//2 - info.get_width()//2, py + ph - 22))