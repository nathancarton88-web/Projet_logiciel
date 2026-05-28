# game.py
# Fichier principal boucle de jeu

import pygame
from keylistener import KeyListener
from map import Map
from player import Player
from screen import Screen
from jeux.tetris import Tetris
from jeux.pacman import Pacman
from jeux.snake import SnakeNeon
from jeux.space_invader import SpaceInvaders
from save_manager import write_save, skin_by_id
from entity import Entity, MODE_WALK, MODE_BIKE, MODE_RUN, MODE_SURF
import json, os

# tailles de la fenetre arcade
GW, GH = 700, 500
# position  pour centrer
GX, GY = 290, 110

BLANC = (255, 255, 255)
CYAN = (0, 255, 255)
GRIS = (100, 100, 120)

try:
    # police windows de base
    font_ui = pygame.font.SysFont("Segoe UI", 26, bold=True)
    font_hud = pygame.font.SysFont("Consolas", 20)
except Exception as e:
    print("erreur font:", e)  # debug au cas ou ca crash
    font_ui = pygame.font.Font(None, 30)
    font_hud = pygame.font.Font(None, 22)

# dico des mini jeux
REGISTRE_JEUX = {
    "tetris": {"class": Tetris, "label": "Tetris au soleil", "color": (130, 0, 255)},
    "pacman": {"class": Pacman, "label": "Pac-Man a la playa", "color": (255, 215, 0)},
    "snake": {"class": SnakeNeon, "label": "Snake de plage", "color": (0, 170, 80)},
    "space": {"class": SpaceInvaders, "label": "Plage invaders", "color": (35, 80, 200)},
}

# liste des jeux qui ont besoin du dt (delta time) pour pas tourner a 2000 fps
NEEDS_DT = {"tetris", "snake", "space"}

ZIK = {
    "map": "assets/music/map.ogg",
    "tetris": "assets/music/tetris.ogg",
    "pacman": "assets/music/pacman.ogg",
    "snake": "assets/music/snake.ogg",
    "space": "assets/music/space.ogg",
}


def play_music(cle, vol=0.4):
    # charge la zik sans faire planter le script si le son manque
    chemin = ZIK.get(cle, ZIK.get("map", ""))
    try:
        if chemin and os.path.exists(chemin):
            pygame.mixer.music.load(chemin)
            pygame.mixer.music.set_volume(vol)
            pygame.mixer.music.play(-1)  # tourne en boucle
        else:
            pygame.mixer.music.stop()
    except Exception as e:
        print("bug son: ", e)


class Game:
    def __init__(self, data_sauvegarde: dict):
        pygame.init()
        pygame.mixer.init()

        self.save_data = data_sauvegarde
        self.screen = Screen()

        # recup du skin depuis le json
        skin = skin_by_id(self.save_data.get("skin", ""))

        # bidouille pour ecraser les variables de la classe Entity direct
        from entity import Entity
        Entity.SKIN_WALK = skin["walk"]
        Entity.SKIN_BIKE = skin["bike"]
        Entity.SKIN_RUN = skin["run"]
        Entity.SKIN_SURF = skin["surf"]

        # setup du player et map
        px, py = self.save_data.get("position", [512, 288])  # valeurs par defaut si 1ere game
        nom_map = self.save_data.get("map", "map_0")

        self.keylistener = KeyListener()
        self.player = Player(self.keylistener, self.screen, px, py)
        self.map = Map(self.screen, map_depart=nom_map)
        self.map.add_player(self.player)

        # machine a etat qui marche lol
        self.etat = "MAP"
        self.alpha_fondu = 0
        self.vitesse_fondu = 12

        self.jeu_actuel = None
        self.id_jeu_actuel = None

        # fx bouton E
        self.prompt_alpha = 0
        self.prompt_dir = 1

        play_music("map")

        self.timer_save = 0
        self.quit_to_menu = False

    def run(self):
        # BOUCLE PRINCIPALE
        while True:
            dt = self.screen.clock.tick(60)  # cap a 60 fps

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.save_pos()
                    pygame.quit()
                    return
                self.check_inputs(ev)

            self.update_logic(dt)
            self.draw_frame()
            self.screen.update()

            if self.quit_to_menu:
                return

            # autosave toutes les 30 sec environ
            self.timer_save += dt
            if self.timer_save >= 30000:
                self.timer_save = 0
                self.save_pos()
                # print("autosave ok")

    def save_pos(self):
        # cast en int() pour eviter les float bizarres dans le json
        pos = [int(self.player.position.x), int(self.player.position.y)]

        m = self.map.map_actuelle.name if self.map.map_actuelle else "map_0"
        self.save_data["position"] = pos
        self.save_data["map"] = m
        self.save_data["highscores"] = self.save_data.get("highscores", {})
        write_save(self.save_data)

    def set_highscore(self, id_jeu, score):
        hs = self.save_data.setdefault("highscores", {})
        if score > hs.get(id_jeu, 0):
            hs[id_jeu] = score
            write_save(self.save_data)

    def check_inputs(self, ev):
        # tout ce qui est touches clavier
        if ev.type == pygame.KEYDOWN:
            k = ev.key

            if self.etat == "MAP" and k == pygame.K_m:
                if self.player.menu_ouvert:
                    self.player.close_menu()
                else:
                    self.player.highscores = self.save_data.get("highscores", {})
                    self.player.open_menu()
                return

            # nav menu
            if self.etat == "MAP" and self.player.menu_ouvert:
                if k == pygame.K_ESCAPE:
                    self.player.close_menu()
                elif k == pygame.K_UP:
                    self.player.menu_up()
                elif k == pygame.K_DOWN:
                    self.player.menu_down()
                elif k == pygame.K_RETURN:
                    act = self.player.menu_confirm()
                    if act == "quit_menu":
                        self.save_pos()
                        self.quit_to_menu = True
                return

            if self.etat == "GAME" and k == pygame.K_ESCAPE:
                self.start_fade_out()
                return

            if self.etat == "MAP" and k == pygame.K_e:
                if self.player.jeu_proche:
                    self.start_fade_in(self.player.jeu_proche)
                return

            if self.etat == "GAME":
                self.input_minijeux(ev)
                return

            # deplacement sur map
            if self.etat == "MAP":
                if k == pygame.K_b:
                    if self.player.mode == MODE_BIKE:
                        self.player.switch_walk()
                    else:
                        self.player.switch_bike()
                elif k == pygame.K_r:
                    if self.player.mode == MODE_RUN:
                        self.player.switch_walk()
                    else:
                        self.player.switch_run()
                elif k == pygame.K_s:
                    if self.player.mode == MODE_SURF:
                        self.player.switch_walk()
                    elif self.player.est_sur_eau:
                        self.player.switch_surf()
                else:
                    self.keylistener.add_key(k)

        elif ev.type == pygame.KEYUP:
            if self.etat == "MAP":
                self.keylistener.remove_key(ev.key)

    def update_logic(self, dt):
        if self.etat == "MAP":
            self.map.update()

            # anim du bouton E
            if self.player.jeu_proche:
                self.prompt_alpha = min(255, self.prompt_alpha + self.prompt_dir * 4)
                if self.prompt_alpha >= 255 or self.prompt_alpha <= 0:
                    self.prompt_dir *= -1
            else:
                self.prompt_alpha = 0

        elif self.etat == "FADE_IN":
            self.alpha_fondu = min(255, self.alpha_fondu + self.vitesse_fondu)
            if self.alpha_fondu >= 255:
                self.launch_game(self.jeu_en_attente)
                self.etat = "GAME"

        elif self.etat == "GAME":
            g = self.jeu_actuel
            if g:
                if self.id_jeu_actuel in NEEDS_DT:
                    g.update(dt)
                else:
                    g.update()

                if g.game_over:
                    self.set_highscore(self.id_jeu_actuel, g.score)

        elif self.etat == "FADE_OUT":
            self.alpha_fondu = min(255, self.alpha_fondu + self.vitesse_fondu)
            if self.alpha_fondu >= 255:
                self.jeu_actuel = None
                self.id_jeu_actuel = None
                self.etat = "FADE_BACK"
                self.alpha_fondu = 255
                play_music("map")

        elif self.etat == "FADE_BACK":
            self.alpha_fondu = max(0, self.alpha_fondu - self.vitesse_fondu)
            if self.alpha_fondu <= 0:
                self.etat = "MAP"
                self.save_pos()

    def draw_frame(self):
        disp = self.screen.get_display()

        if self.etat in ("MAP", "FADE_IN", "FADE_BACK"):
            if self.etat != "MAP":
                self.map.update()

            if self.etat == "MAP" and self.player.jeu_proche:
                self.draw_bouton_e(disp)

            if self.etat == "MAP" and self.player.menu_ouvert:
                self.player.draw_ingame_menu(disp, self.save_data.get("highscores", {}))

            if self.etat in ("FADE_IN", "FADE_BACK"):
                calque = pygame.Surface(disp.get_size(), pygame.SRCALPHA)
                calque.fill((0, 0, 0, self.alpha_fondu))
                disp.blit(calque, (0, 0))

        elif self.etat in ("GAME", "FADE_OUT"):
            ecran_jeu = pygame.Surface((GW, GH))
            ecran_jeu.fill((5, 5, 10))
            if self.jeu_actuel:
                self.jeu_actuel.draw(ecran_jeu)

            disp.fill((15, 15, 20))
            # contour de la borne
            pygame.draw.rect(disp, (40, 40, 50),
                             (GX - 4, GY - 4, GW + 8, GH + 8), border_radius=6)
            disp.blit(ecran_jeu, (GX, GY))

            # UI
            if self.id_jeu_actuel in REGISTRE_JEUX:
                info = REGISTRE_JEUX[self.id_jeu_actuel]

                titre = font_ui.render(info["label"], True, info["color"])
                disp.blit(titre, (GX, GY - 36))

                hs = self.save_data.get("highscores", {}).get(self.id_jeu_actuel, 0)
                txt_hs = font_hud.render(f"BEST : {hs}", True, (200, 200, 100))
                disp.blit(txt_hs, (GX + GW - txt_hs.get_width(), GY - 30))

                txt_esc = font_hud.render("[ Echap ] Retour a la carte", True, GRIS)
                disp.blit(txt_esc, (GX, GY + GH + 8))

                pseudo = self.save_data.get('player_name', 'Joueur')
                txt_joueur = font_hud.render(f"Joueur : {pseudo}", True, GRIS)
                disp.blit(txt_joueur, (GX, GY + GH + 28))

            if self.etat == "FADE_OUT":
                calque = pygame.Surface((GW, GH), pygame.SRCALPHA)
                calque.fill((0, 0, 0, self.alpha_fondu))
                disp.blit(calque, (GX, GY))

    def draw_bouton_e(self, disp):
        txt = font_hud.render("[ E ]  pour Jouer", True, BLANC)
        # on rajoute un peu de marge autour du texte (+16 et +10)
        s = pygame.Surface((txt.get_width() + 16, txt.get_height() + 10), pygame.SRCALPHA)
        alpha_safe = max(0, min(255, int(self.prompt_alpha)))

        s.fill((20, 20, 30, alpha_safe))
        s.blit(txt, (8, 5))
        disp.blit(s, (self.screen.get_size()[0] // 2 - s.get_width() // 2, 20))

    def start_fade_in(self, id_jeu):
        self.jeu_en_attente = id_jeu
        self.alpha_fondu = 0
        self.etat = "FADE_IN"
        self.keylistener.clear()  # vide buffer pour pas bouger tout seul apres

    def start_fade_out(self):
        self.alpha_fondu = 0
        self.etat = "FADE_OUT"

    def launch_game(self, id_jeu):
        info = REGISTRE_JEUX.get(id_jeu)
        if not info:
            self.etat = "MAP"  # si y'a un typo dans la TMX on annule
            return

        self.jeu_actuel = info["class"]()
        self.id_jeu_actuel = id_jeu
        play_music(id_jeu)

    def input_minijeux(self, ev):
        # des inputs mais ca fait le taff
        g = self.jeu_actuel
        gid = self.id_jeu_actuel
        if not g or not gid: return

        if gid == "tetris":
            if ev.key == pygame.K_LEFT and not g.collide(dx=-1): g.cur['x'] -= 1
            if ev.key == pygame.K_RIGHT and not g.collide(dx=1):  g.cur['x'] += 1
            if ev.key == pygame.K_DOWN and not g.collide(dy=1):  g.cur['y'] += 1
            if ev.key == pygame.K_UP:
                r = g.rotate(g.cur['shape'])
                if not g.collide(shape=r): g.cur['shape'] = r
            if ev.key == pygame.K_SPACE:
                g.cur['y'] = g.ghost_y()
                g._lock()

        elif gid == "pacman":
            if ev.key == pygame.K_UP:    g.next_dir = [0, -1]
            if ev.key == pygame.K_DOWN:  g.next_dir = [0, 1]
            if ev.key == pygame.K_LEFT:  g.next_dir = [-1, 0]
            if ev.key == pygame.K_RIGHT: g.next_dir = [1, 0]

        elif gid == "snake":
            if ev.key == pygame.K_UP:    g.set_dir((0, -1))
            if ev.key == pygame.K_DOWN:  g.set_dir((0, 1))
            if ev.key == pygame.K_LEFT:  g.set_dir((-1, 0))
            if ev.key == pygame.K_RIGHT: g.set_dir((1, 0))

        elif gid == "space":
            if ev.key == pygame.K_SPACE: g.shoot()