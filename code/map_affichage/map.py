# map.py
# Loader de la carte Tiled (TMX) et gestion de la camera pyscroll


import pygame
import pyscroll
import pytmx

from player import Player
from screen import Screen
from change import Change


class Map:
    def __init__(self, screen, map_depart="map_0"):
        self.screen = screen
        self.tmx_data = None
        self.map_layer = None
        self.group = None

        self.player = None
        self.change = None
        self.collisions = None
        self.zones_eau = []

        self.map_actuelle = Change("switch", map_depart, pygame.Rect(0, 0, 0, 0), 0)
        self.charger_map(self.map_actuelle)


    def charger_map(self, infos_map):
        # charge le fichier tmx
        self.tmx_data = pytmx.load_pygame(f"assets/map/{infos_map.name}.tmx")
        map_data = pyscroll.data.TiledMapData(self.tmx_data)
        
        # setup du renderer pyscroll
        self.map_layer = pyscroll.BufferedRenderer(map_data, self.screen.get_size())
        self.group = pyscroll.PyscrollGroup(map_layer=self.map_layer, default_layer=7)

        # zoom selon si c'est la map open world ou l'interieur d'un batiment
        if infos_map.name.split("_")[0] == "map":
            self.map_layer.zoom = 3
        else:
            self.map_layer.zoom = 3.75

        self.change = []
        self.collisions = []
        self.zones_eau = [] # (j'avais oublie de reset l'eau avant, ca faisait lagger)

        # parse tous les objets du TMX
        for obj in self.tmx_data.objects:
            # recup les murs invisibles
            if obj.name == "collision":
                self.collisions.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))
                continue

            # on split le nom pour recup les parametres ("switch map_1 0" par ex)
            parts = obj.name.split(" ")
            obj_type = parts[0]

            if obj_type == "switch":
                self.change.append(Change(
                    "switch",
                    parts[1],
                    pygame.Rect(obj.x, obj.y, obj.width, obj.height),
                    int(parts[-1])
                ))

            # les portes vers les mini-jeux 
            # (Convention = nom de l'objet doit etre "game tetris", "game pacman", etc.)
            elif obj_type == "game" and len(parts) >= 2:
                game_id = parts[1].lower() 
                self.change.append(Change(
                    "game",
                    game_id,
                    pygame.Rect(obj.x, obj.y, obj.width, obj.height),
                    0
                ))
            
            # la mer / les lacs
            elif obj_type == "water":
                self.zones_eau.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))

        # si le joueur est deja load, on le teleporte a sa place
        if self.player:
            self.placer_joueur(infos_map)
            self.player.align_hitbox()
            self.player.step = 16
            self.player.add_switchs(self.change)
            self.player.add_collisions(self.collisions)
            self.player.add_water_zones(self.zones_eau)
            self.group.add(self.player)
            
            # si c'est un batiment (pas "map_X"), on force a velo ?
            #  on laisse comme ca pour l'instant lol
            if infos_map.name.split("_")[0] != "map":
                self.player.switch_bike(True)

        self.map_actuelle = infos_map


    def add_player(self, player):
        self.group.add(player)
        self.player = player
        self.player.align_hitbox()
        self.player.add_switchs(self.change)
        self.player.add_collisions(self.collisions)
        self.player.add_water_zones(self.zones_eau)

    def update(self):
        if self.player:
            # declenche le changement de map s'il a marché sur un block switch
            if self.player.change_map and self.player.step >= 8:
                self.charger_map(self.player.change_map)
                self.player.change_map = None
                
        self.group.update()
        
        # bloque la camera sur la position du perso
        self.group.center(self.player.rect.center)
        self.group.draw(self.screen.get_display())

    def placer_joueur(self, infos_map):
        # recup le point de spawn specifique depuis tiled
        nom_spawn = "spawn " + infos_map.name + " " + str(infos_map.port)
        point = self.tmx_data.get_object_by_name(nom_spawn)
        self.player.position = pygame.math.Vector2(point.x, point.y)