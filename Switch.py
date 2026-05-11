import pygame, random, os, json
from snake import SnakeNeon
from notif import NotifSystem
from space_invader import SpaceInvaders
from tetris import Tetris
from pacman import Pacman

_HS_FILE = "scores.json"

def load_hs():
    try:
        if os.path.exists(_HS_FILE):
            with open(_HS_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return {"tetris": 0, "pacman": 0, "snake": 0, "space": 0}

def save_hs(d):
    try:
        with open(_HS_FILE, "w") as f:
            json.dump(d, f)
    except Exception:
        pass


pygame.init()
L_ECRAN, H_ECRAN   = 1000, 600
L_INTERNE, H_INTERNE = 700, 500
X_DEBUT, Y_DEBUT   = 150, 50
screen = pygame.display.set_mode((L_ECRAN, H_ECRAN))
pygame.display.set_caption("Le gaming c'est cool")
clock = pygame.time.Clock()


NOIR_CHASSIS = (20, 20, 22);  ECRAN_OFF   = (5, 5, 10)
JOYCON_BLEU  = (0, 190, 230); JOYCON_ROUGE= (255, 60, 50)
BLANC = (255, 255, 255);      CYAN  = (0, 255, 255)
JAUNE = (255, 230, 0);        VERT  = (50, 255, 80)
GRIS_BOUTON = (50, 50, 55)


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


class Switch:
    GAMES_INFO = [
        {"name": "Tetris Forever",  "color": (130,0,255),   "id": "TETRIS"},
        {"name": "Pac-Man Neon",    "color": (255,215,0),   "id": "PACMAN"},
        {"name": "Snake Neon",      "color": (0,170,80),    "id": "SNAKE"},
        {"name": "Space Invaders",  "color": (35,80,200),   "id": "SPACE"},
        {"name": "Quitter",         "color": (55,55,60),    "id": "QUIT"},
    ]

    def __init__(self):
        self.state     = "MENU"
        self.selection = 0
        self.tetris    = Tetris()
        self.pacman    = Pacman()
        self.snake     = SnakeNeon()
        self.space     = SpaceInvaders()
        self.notifs    = NotifSystem()
        self.highscores= load_hs()

        # Transitions
        self.ts = None   # "FADE_OUT" | "TITLE" | "FADE_IN"
        self.tf = 0
        self.tt = None   # target game id

        # Menu particles (80 stars)
        self.particles = [self._mk_p(True) for _ in range(80)]

        # Menu tile zoom per index
        self.zoom = {i: 152.0 for i in range(len(self.GAMES_INFO))}

        # Pre-built CRT overlays
        self.crt_lines    = self._mk_crt_lines()
        self.crt_vignette = self._mk_vignette()

        # Notification tracking
        self.prev_lvl = {g["id"]: 1     for g in self.GAMES_INFO}
        self.prev_go  = {g["id"]: False for g in self.GAMES_INFO}

    # CRT surfaces
    def _mk_crt_lines(self):
        s = pygame.Surface((L_INTERNE, H_INTERNE), pygame.SRCALPHA)
        for y in range(0, H_INTERNE, 3):
            pygame.draw.line(s, (0, 0, 0, 60), (0, y), (L_INTERNE, y))
        return s

    def _mk_vignette(self):
        s = pygame.Surface((L_INTERNE, H_INTERNE), pygame.SRCALPHA)
        d = 90
        for i in range(d):
            a = int((1 - i/d)**2 * 115)
            # top / bottom
            s.fill((0,0,0,a), (0,         i,             L_INTERNE, 1))
            s.fill((0,0,0,a), (0,         H_INTERNE-i-1, L_INTERNE, 1))
            # left / right
            s.fill((0,0,0,a), (i,         0,             1, H_INTERNE))
            s.fill((0,0,0,a), (L_INTERNE-i-1, 0,         1, H_INTERNE))
        return s

    def _apply_crt(self, surf):
        surf.blit(self.crt_lines,    (0, 0))
        surf.blit(self.crt_vignette, (0, 0))


    def _mk_p(self, spread=False):
        return {
            'x':  random.uniform(0, L_INTERNE),
            'y':  random.uniform(0, H_INTERNE) if spread else float(H_INTERNE),
            'vx': random.uniform(-0.18, 0.18),
            'vy': random.uniform(-0.38, -0.08),
            'r':  random.uniform(1, 2.6),
            'b':  random.randint(110, 255),
        }


    def _go_game(self, gid):
        if gid == "QUIT":
            save_hs(self.highscores);  pygame.quit();  exit()
        self.ts = "FADE_OUT";  self.tf = 0;  self.tt = gid

    def _go_menu(self):
        self.ts = "FADE_IN";  self.tf = 0

    def _apply_trans(self, surf):
        if self.ts == "FADE_OUT":
            self.tf += 1
            ov = pygame.Surface((L_INTERNE, H_INTERNE), pygame.SRCALPHA)
            ov.fill((0, 0, 0, min(255, int(255 * self.tf / 20))))
            surf.blit(ov, (0, 0))
            if self.tf >= 20:
                self.ts = "TITLE";  self.tf = 0

        elif self.ts == "TITLE":
            self.tf += 1
            surf.fill((0, 0, 0))
            name = next(g["name"] for g in self.GAMES_INFO if g["id"] == self.tt)
            t = font_large.render(name, True, BLANC)
            surf.blit(t, (L_INTERNE//2 - t.get_width()//2, H_INTERNE//2 - t.get_height()//2))
            if self.tf >= 40:
                self.ts = None;  self._launch(self.tt)

        elif self.ts == "FADE_IN":
            self.tf += 1
            alpha = max(0, int(255 * (20 - self.tf) / 20))
            if alpha > 0:
                ov = pygame.Surface((L_INTERNE, H_INTERNE), pygame.SRCALPHA)
                ov.fill((0, 0, 0, alpha));  surf.blit(ov, (0, 0))
            if self.tf >= 20:
                self.ts = None;  self.state = "MENU"

    def _launch(self, gid):
        self.state = gid
        game_map = {"TETRIS": self.tetris, "PACMAN": self.pacman,
                    "SNAKE":  self.snake,  "SPACE":  self.space}
        g = game_map.get(gid)
        if g:
            if hasattr(g, 'full_reset'): g.full_reset()
            else:                         g.reset()
        self.prev_lvl[gid] = 1
        self.prev_go [gid] = False


    def _check_notifs(self, gid, game):
        key = gid.lower()
        if game.level > self.prev_lvl[gid]:
            self.prev_lvl[gid] = game.level
            self.notifs.push(f"   NIVEAU {game.level} !    ")
        if game.game_over and not self.prev_go[gid]:
            self.prev_go[gid] = True
            sc = game.score
            if sc > self.highscores.get(key, 0):
                self.highscores[key] = sc
                save_hs(self.highscores)
                self.notifs.push("   NOUVEAU RECORD !   ", 200)
            else:
                self.notifs.push("   GAME OVER   ")


    def draw_hardware(self, surf):
        pygame.draw.rect(surf, JOYCON_BLEU,  (0,  50, 150, 500),
                         border_top_left_radius=60, border_bottom_left_radius=60)
        pygame.draw.rect(surf, JOYCON_ROUGE, (850, 50, 150, 500),
                         border_top_right_radius=60, border_bottom_right_radius=60)
        pygame.draw.circle(surf, GRIS_BOUTON, (75,  200), 25)
        pygame.draw.circle(surf, GRIS_BOUTON, (925, 350), 25)

 #le menuuuuuuuuu
    def draw_menu(self, surf):

        for i, p in enumerate(self.particles):
            p['x'] += p['vx'];  p['y'] += p['vy']
            if p['y'] < 0 or p['x'] < 0 or p['x'] > L_INTERNE:
                self.particles[i] = self._mk_p()
                continue
            b = int(p['b'])
            pygame.draw.circle(surf, (b, b, b), (int(p['x']), int(p['y'])), int(p['r']))

        # zooooooooooommmmm
        for i in range(len(self.GAMES_INFO)):
            target = 165.0 if i == self.selection else 152.0
            self.zoom[i] += (target - self.zoom[i]) * 0.18

        # Entete
        pygame.draw.rect(surf, (26, 26, 32), (0, 0, L_INTERNE, 56))
        surf.blit(font_sys.render("SWITCH", True, BLANC), (18, 15))
        surf.blit(font_pixel.render("Choose un jeu mon reuf", True, (110,110,130)), (L_INTERNE-195, 20))

        # Titre
        SZ    = 155
        GAP   = 16
        rows  = [[0,1,2], [3,4]]
        tile_pos = {}
        for ri, idx_list in enumerate(rows):
            n = len(idx_list)
            tw = n*SZ + (n-1)*GAP
            xs = (L_INTERNE - tw) // 2
            yb = 64 + ri * 198
            for j, idx in enumerate(idx_list):
                tile_pos[idx] = (xs + j*(SZ+GAP), yb)

        for idx, game in enumerate(self.GAMES_INFO):
            s  = int(self.zoom[idx])
            bx, by = tile_pos[idx]
            dx = (SZ - s) // 2;  dy = (SZ - s) // 2
            tx, ty = bx + dx, by + dy
            pygame.draw.rect(surf, game["color"], (tx, ty, s, s), border_radius=10)
            # première lettre
            ltr = font_main.render(game["name"][0], True, BLANC)
            surf.blit(ltr, (tx + s//2 - ltr.get_width()//2, ty + s//2 - ltr.get_height()//2 - 8))
            # meilleur score
            key = game["id"].lower()
            hs  = self.highscores.get(key)
            if hs is not None:
                hs_t = font_pixel.render(f"BEST:{hs}", True, JAUNE)
                surf.blit(hs_t, (tx + s//2 - hs_t.get_width()//2, ty + s + 4))

            if idx == self.selection:
                pygame.draw.rect(surf, CYAN, (tx-3, ty-3, s+6, s+6), 3, border_radius=12)
                nt = font_sys.render(game["name"], True, BLANC)
                surf.blit(nt, (tx + s//2 - nt.get_width()//2, ty + s + 22))

        # bar du bas
        pygame.draw.line(surf, (52,52,60), (0,460),(L_INTERNE,460), 2)
        surf.blit(font_pixel.render("← → Selectionner   ENTREE Lancer   Echap Menu",
                                    True, (135,135,150)), (L_INTERNE//2-210, 472))

    # les touches wsh
    def handle_input(self, event):
        if event.type != pygame.KEYDOWN: return
        if event.key == pygame.K_ESCAPE:
            if self.state != "MENU" and not self.ts:
                self._go_menu()
            return
        if self.ts: return   # block les touches pendant les transitions

        if self.state == "MENU":
            if event.key in (pygame.K_LEFT,  pygame.K_UP):
                self.selection = (self.selection - 1) % len(self.GAMES_INFO)
            if event.key in (pygame.K_RIGHT, pygame.K_DOWN):
                self.selection = (self.selection + 1) % len(self.GAMES_INFO)
            if event.key == pygame.K_RETURN:
                self._go_game(self.GAMES_INFO[self.selection]["id"])

        elif self.state == "TETRIS":
            t = self.tetris
            if event.key == pygame.K_LEFT  and not t.collide(dx=-1): t.cur['x'] -= 1
            if event.key == pygame.K_RIGHT and not t.collide(dx=1):  t.cur['x'] += 1
            if event.key == pygame.K_DOWN  and not t.collide(dy=1):  t.cur['y'] += 1
            if event.key == pygame.K_UP:
                rot = t.rotate(t.cur['shape'])
                if not t.collide(shape=rot): t.cur['shape'] = rot
            if event.key == pygame.K_SPACE:
                t.cur['y'] = t.ghost_y();  t._lock()

        elif self.state == "PACMAN":
            if event.key == pygame.K_UP:    self.pacman.next_dir = [0,-1]
            if event.key == pygame.K_DOWN:  self.pacman.next_dir = [0, 1]
            if event.key == pygame.K_LEFT:  self.pacman.next_dir = [-1,0]
            if event.key == pygame.K_RIGHT: self.pacman.next_dir = [1, 0]

        elif self.state == "SNAKE":
            if event.key == pygame.K_UP:    self.snake.set_dir((0,-1))
            if event.key == pygame.K_DOWN:  self.snake.set_dir((0, 1))
            if event.key == pygame.K_LEFT:  self.snake.set_dir((-1,0))
            if event.key == pygame.K_RIGHT: self.snake.set_dir((1, 0))

        elif self.state == "SPACE":
            if event.key == pygame.K_SPACE: self.space.shoot()

    # la boucle infiniiiiiiiiiie
    def run(self):
        while True:
            dt = clock.tick(60)
            screen.fill(NOIR_CHASSIS)
            self.draw_hardware(screen)

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    save_hs(self.highscores);  pygame.quit();  return
                self.handle_input(ev)

            inner = pygame.Surface((L_INTERNE, H_INTERNE))
            inner.fill(ECRAN_OFF)

            if self.state == "MENU":
                self.draw_menu(inner)
            elif self.state == "TETRIS":
                self.tetris.update(dt);  self.tetris.draw(inner)
                self._check_notifs("TETRIS", self.tetris)
            elif self.state == "PACMAN":
                self.pacman.update();    self.pacman.draw(inner)
                self._check_notifs("PACMAN", self.pacman)
            elif self.state == "SNAKE":
                self.snake.update(dt);   self.snake.draw(inner)
                self._check_notifs("SNAKE", self.snake)
            elif self.state == "SPACE":
                self.space.update(dt);   self.space.draw(inner)
                self._check_notifs("SPACE", self.space)

            # Transition
            if self.ts:
                self._apply_trans(inner)

            # des effets waouw
            self._apply_crt(inner)

            # Notif bannière
            self.notifs.tick(inner)

            screen.blit(inner, (X_DEBUT, Y_DEBUT))
            pygame.display.flip()

