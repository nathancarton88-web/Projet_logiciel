import pygame
import pyscroll
import pytmx

from player import Player
from screen import Screen
from change import Change


class Map:
    def __init__(self, screen: Screen):
        self.screen: Screen = screen
        self.tmx_data: pytmx.TiledMap | None = None
        self.map_layer: pyscroll.BufferedRenderer | None = None
        self.group: pyscroll.PyscrollGroup | None = None

        self.player: Player | None = None
        self.change: list[Change] | None = None
        self.collisions: list[pygame.Rect] | None = None

        self.current_map: Change = Change("switch", "map_0", pygame.Rect(0, 0, 0, 0), 0)
        self.switch_map(self.current_map)

    # ═════════════════════════════════════════════════════════════════════════

    def switch_map(self, change: Change) -> None:
        self.tmx_data = pytmx.load_pygame(
            f"C:/Users/natha/PycharmProjects/PokePoke/assets/map/{change.name}.tmx"
        )
        map_data = pyscroll.data.TiledMapData(self.tmx_data)
        self.map_layer = pyscroll.BufferedRenderer(map_data, self.screen.get_size())
        self.group = pyscroll.PyscrollGroup(map_layer=self.map_layer, default_layer=7)

        if change.name.split("_")[0] == "map":
            self.map_layer.zoom = 3
        else:
            self.map_layer.zoom = 3.75

        self.change = []
        self.collisions = []

        for obj in self.tmx_data.objects:
            if obj.name == "collision":
                self.collisions.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))
                continue

            parts = obj.name.split(" ")
            obj_type = parts[0]

            # ── Changement de carte (comportement existant) ────────────────────
            if obj_type == "switch":
                self.change.append(Change(
                    "switch",
                    parts[1],
                    pygame.Rect(obj.x, obj.y, obj.width, obj.height),
                    int(parts[-1])
                ))

            # ── Porte vers un mini-jeu ─────────────────────────────────────────
            # Convention TMX : nom de l'objet = "game tetris" / "game snake" / etc.
            elif obj_type == "game" and len(parts) >= 2:
                game_id = parts[1].lower()   # "tetris", "pacman", "snake", "space"
                self.change.append(Change(
                    "game",
                    game_id,
                    pygame.Rect(obj.x, obj.y, obj.width, obj.height),
                    0
                ))

        if self.player:
            self.pose_player(change)
            self.player.align_hitbox()
            self.player.step = 16
            self.player.add_switchs(self.change)
            self.player.add_collisions(self.collisions)
            self.group.add(self.player)
            if change.name.split("_")[0] != "map":
                self.player.switch_bike(True)

        self.current_map = change

    # ═════════════════════════════════════════════════════════════════════════

    def add_player(self, player: Player) -> None:
        self.group.add(player)
        self.player = player
        self.player.align_hitbox()
        self.player.add_switchs(self.change)
        self.player.add_collisions(self.collisions)

    def update(self) -> None:
        if self.player:
            # Changement de carte classique (switch uniquement, pas game)
            if self.player.change_map and self.player.step >= 8:
                self.switch_map(self.player.change_map)
                self.player.change_map = None
        self.group.update()
        self.group.center(self.player.rect.center)
        self.group.draw(self.screen.get_display())

    def pose_player(self, change: Change) -> None:
        position = self.tmx_data.get_object_by_name(
            "spawn " + self.current_map.name + " " + str(change.port)
        )
        self.player.position = pygame.math.Vector2(position.x, position.y)
