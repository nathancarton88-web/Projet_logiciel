import pygame
from keylistener import KeyListener
from screen import Screen
from tool import Tool

MODE_WALK = "walk"
MODE_BIKE = "bike"
MODE_RUN  = "run"
MODE_SURF = "surf"


class Entity(pygame.sprite.Sprite):
    SKIN_WALK = "assets/sprite/hero_01_white_f_walk.png"
    SKIN_BIKE = "assets/sprite/hero_01_white_f_cycle_wheel.png"
    SKIN_RUN  = "assets/sprite/hero_01_white_f_run.png"
    SKIN_SURF = "assets/sprite/hero_01_white_f_surf.png"

    def __init__(self, keylistener, screen, x, y):
        super().__init__()
        self.screen      = screen
        self.keylistener = keylistener

        # Chargement spritesheets
        self.spritesheet      = pygame.image.load(Entity.SKIN_WALK)
        self.spritesheet_bike = pygame.image.load(Entity.SKIN_BIKE)
        self.spritesheet_run  = self._try_load(Entity.SKIN_RUN)
        self.spritesheet_surf = self._try_load(Entity.SKIN_SURF)

        # Image initiale identique à l'original
        self.image    = Tool.split_image(self.spritesheet, 0, 0, 24, 32)
        self.position = pygame.math.Vector2(x, y)
        self.rect     = self.image.get_rect()

        self.all_images = self.get_all_images(self.spritesheet)

        self._images_run  = self._build_images(self.spritesheet_run,  4, 4) \
                            if self.spritesheet_run  else self.all_images
        self._images_surf = self._build_images(self.spritesheet_surf, 4, 4) \
                            if self.spritesheet_surf else self.all_images

        # Animation — identique à l'original
        self.index_image       = 0
        self.image_part        = 0
        self.reset_animation   = False
        self.hitbox            = pygame.Rect(0, 0, 16, 16)
        self.step              = 0
        self.animation_walk    = False
        self.direction         = "down"
        self.animtion_step_time= 0.0
        self.action_animation  = 16
        self.speed             = 1
        self.mode              = MODE_WALK

    @staticmethod
    def _try_load(path):
        try:
            return pygame.image.load(path)
        except Exception as e:
            print(f"[Entity] Spritesheet manquante : {path} ({e})")
            return None

    def _build_images(self, sheet, cols, rows):
        """
        Découpe un spritesheet selon sa vraie taille.
        cols = frames par direction, rows = nb de directions (3 ou 4)
        Ordre : down, left, right, up
        """
        dirs   = ["down", "left", "right", "up"]
        fw     = sheet.get_width()  // cols
        fh     = sheet.get_height() // rows
        result = {d: [] for d in dirs}
        for row in range(rows):
            d = dirs[row]
            for col in range(cols):
                result[d].append(Tool.split_image(sheet, col * fw, row * fh, fw, fh))
        # Si 3 directions seulement, "up" reprend "down"
        if rows < 4:
            result["up"] = result["down"][:]
        return result

    # ── Update identique à l'original ────────────────────────────────────────

    def update(self):
        self.animation_sprite()
        self.move()
        self.rect.center = self.position
        self.hitbox.midbottom = self.rect.midbottom
        self.image = self.all_images[self.direction][self.index_image]

    def move_left(self):  self.animation_walk = True; self.direction = "left"
    def move_right(self): self.animation_walk = True; self.direction = "right"
    def move_up(self):    self.animation_walk = True; self.direction = "up"
    def move_down(self):  self.animation_walk = True; self.direction = "down"

    def animation_sprite(self):
        # Nb de frames dispo pour la direction courante
        nb = len(self.all_images.get(self.direction, []))
        nb = nb if nb > 0 else 4
        if int(self.step // 8) + self.image_part >= nb:
            self.image_part      = 0
            self.reset_animation = True
        self.index_image = min(int(self.step // 8) + self.image_part, nb - 1)

    def move(self):
        if self.animation_walk:
            self.animtion_step_time += self.screen.get_delta_time()
            if self.step < 16 and self.animtion_step_time >= self.action_animation:
                self.step += self.speed
                if   self.direction == "left":  self.position.x -= self.speed
                elif self.direction == "right": self.position.x += self.speed
                elif self.direction == "up":    self.position.y -= self.speed
                elif self.direction == "down":  self.position.y += self.speed
                self.animtion_step_time = 0
            elif self.step >= 16:
                self.step           = 0
                self.animation_walk = False
                if self.reset_animation:
                    self.reset_animation = False
                else:
                    self.image_part = 2 if self.image_part == 0 else 0

    def align_hitbox(self):
        self.position.x += 16
        self.rect.center  = self.position
        self.hitbox.midbottom = self.rect.midbottom
        while self.hitbox.x % 16 != 0:
            self.rect.x -= 1
            self.hitbox.midbottom = self.rect.midbottom
        while self.hitbox.y % 16 != 0:
            self.rect.y -= 1
            self.hitbox.midbottom = self.rect.midbottom
        self.position = pygame.math.Vector2(self.rect.center)

    # get_all_images IDENTIQUE à l'original — utilisé pour walk et bike
    def get_all_images(self, spritesheet):
        all_images = {"down": [], "left": [], "right": [], "up": []}
        width  = spritesheet.get_width()  // 4
        height = spritesheet.get_height() // 4
        for i in range(4):
            for j, key in enumerate(all_images.keys()):
                all_images[key].append(
                    Tool.split_image(spritesheet, i * width, j * height, width, height)
                )
        return all_images

    # ── Modes ─────────────────────────────────────────────────────────────────

    def switch_walk(self):
        self.mode       = MODE_WALK
        self.speed      = 1
        self.all_images = self.get_all_images(self.spritesheet)

    def switch_bike(self, deactive=False):
        if deactive or self.mode == MODE_BIKE:
            self.switch_walk()
        else:
            self.mode       = MODE_BIKE
            self.speed      = 2
            self.all_images = self.get_all_images(self.spritesheet_bike)

    def switch_run(self, deactive=False):
        if deactive or self.mode == MODE_RUN:
            self.switch_walk()
        else:
            self.mode       = MODE_RUN
            self.speed      = 2
            self.all_images = self._images_run

    def switch_surf(self, deactive=False):
        if deactive or self.mode == MODE_SURF:
            self.switch_walk()
        else:
            self.mode       = MODE_SURF
            self.speed      = 1
            self.all_images = self._images_surf
