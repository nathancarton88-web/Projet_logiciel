import pygame
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
class Notification:
    H      = 48
    FRAMES = 25   # slide-in / slide-out frames

    def __init__(self, text, duration=150):
        self.text  = text
        self.total = self.FRAMES + duration + self.FRAMES
        self.frame = 0
        self.done  = False

    def update(self):
        self.frame += 1
        if self.frame >= self.total:
            self.done = True

    def _y(self):
        def smooth(t): return t * t * (3 - 2 * t)
        if self.frame < self.FRAMES:
            return int(-self.H + smooth(self.frame / self.FRAMES) * self.H)
        if self.frame > self.total - self.FRAMES:
            t = (self.total - self.frame) / self.FRAMES
            return int(-self.H + smooth(t) * self.H)
        return 0

    def draw(self, surf):
        yy = self._y()
        ban = pygame.Surface((L_INTERNE, self.H), pygame.SRCALPHA)
        ban.fill((12, 12, 28, 210))
        surf.blit(ban, (0, yy))
        pygame.draw.line(surf, CYAN, (0, yy + self.H - 1), (L_INTERNE, yy + self.H - 1), 2)
        txt = font_main.render(self.text, True, BLANC)
        surf.blit(txt, (L_INTERNE // 2 - txt.get_width() // 2,
                        yy + self.H // 2 - txt.get_height() // 2))
class NotifSystem:
    def __init__(self):
        self.queue = []

    def push(self, text, duration=150):
        if len(self.queue) < 2:
            self.queue.append(Notification(text, duration))

    def tick(self, surf):
        for n in self.queue:
            n.update()
        self.queue = [n for n in self.queue if not n.done]
        if self.queue:
            self.queue[0].draw(surf)
