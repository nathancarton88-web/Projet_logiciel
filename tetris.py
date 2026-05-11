import pygame, random



pygame.init()
L_ECRAN, H_ECRAN   = 1000, 600
L_INTERNE, H_INTERNE = 700, 500
X_DEBUT, Y_DEBUT   = 150, 50



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

class Tetris:
    # Définition des 7 formes (Tetriminos) sous forme de matrices (listes de listes)
    SHAPES = [
        [[1, 1, 1, 1]],  # I
        [[1, 1], [1, 1]],  # O
        [[0, 1, 0], [1, 1, 1]],  # T
        [[0, 1, 1], [1, 1, 0]],  # S
        [[1, 1, 0], [0, 1, 1]],  # Z
        [[1, 0, 0], [1, 1, 1]],  # J
        [[0, 0, 1], [1, 1, 1]],  # L
    ]
    # Liste des couleurs associées à chaque forme ci-dessus
    COLORS = [CYAN, (255, 230, 0), (180, 0, 255), (50, 255, 50), (255, 50, 50), (50, 50, 255), (255, 150, 0)]

    # Paramètres de la grille : Largeur=10, Hauteur=18, Taille d'un Bloc (BS)=25 pixels
    LG, HG, BS = 10, 18, 25
    # Position de départ  du plateau sur l'écran
    XO, YO = 225, 25

    def __init__(self):
        self.reset()  # Initialise les variables du jeu au démarrage

    def reset(self):
        # Crée une grille vide (HG lignes x LG colonnes) remplie de None
        self.grid = [[None] * self.LG for _ in range(self.HG)]
        self.cur = self._new()  # Pièce actuelle
        self.nxt = self._new()  # Pièce suivante
        self.score = 0  # Score initial
        self.level = 1  # Niveau de difficulté
        self.lines = 0  # Nombre de lignes totales complétées
        self.ft = 0  # Compteur de temps (Fall Timer)
        self.game_over = False  # État de la partie

    def _new(self):
        # Choisit une forme au hasard et renvoie un dictionnaire avec ses propriétés
        i = random.randint(0, 6)
        return {'x': 3, 'y': 0, 'shape': self.SHAPES[i], 'color': self.COLORS[i]}

    def rotate(self, s):
        # transpose la matrice et inverse les lignes pour une rotation de 90°
        return [list(r) for r in zip(*s[::-1])]

    def collide(self, dx=0, dy=0, shape=None):
        # Vérifie si la pièce entre en collision avec les bords ou les blocs fixés
        s = shape or self.cur['shape']
        for r, row in enumerate(s):
            for c, v in enumerate(row):
                if v:  # Si la case du n'est pas vide
                    nx, ny = self.cur['x'] + c + dx, self.cur['y'] + r + dy  # Future position
                    # Sortie des limites horizontales ou bas de grille
                    if nx < 0 or nx >= self.LG or ny >= self.HG: return True
                    # Collision avec un bloc déjà présent dans la grille (si ny >= 0)
                    if ny >= 0 and self.grid[ny][nx]: return True
        return False

    def ghost_y(self):
        # Calcule la position "fantôme"
        gy = self.cur['y']
        while not self.collide(dy=gy - self.cur['y'] + 1): gy += 1
        return gy

    def update(self, dt):
        # Gère la descente automatique de la pièce en fonction du temps écoulé
        if self.game_over: return
        self.ft += dt
        # Plus le niveau est élevé, plus le délai (500 - level * 40) court
        if self.ft > max(100, 500 - self.level * 40):
            if not self.collide(dy=1):
                self.cur['y'] += 1  # On descend d'une case
            else:
                self._lock()  # Si collision en bas, on fixe la pièce
            self.ft = 0

    def _lock(self):
        # Fixe la pièce actuelle dans la grille permanente
        for r, row in enumerate(self.cur['shape']):
            for c, v in enumerate(row):
                if v:
                    yp = self.cur['y'] + r
                    if yp < 0:  # Si on fixe une pièce au-dessus du bord haut = perdu
                        self.game_over = True;
                        return
                    self.grid[yp][self.cur['x'] + c] = self.cur['color']
        self._clear()  # Vérifie si des lignes sont complètes
        self.cur = self.nxt  # La pièce suivante devient l'actuelle
        self.nxt = self._new()  # On en génère une nouvelle
        if self.collide(): self.game_over = True  # Si la nouvelle pièce est déjà bloquée = perdu

    def _clear(self):
        # Identifie et supprime les lignes pleines
        full = [i for i, row in enumerate(self.grid) if all(row)]
        for i in full:
            del self.grid[i]  # Supprime la ligne
            self.grid.insert(0, [None] * self.LG)  # Ajoute une ligne vide en haut
        if full:
            self.lines += len(full)
            # Calcul du score : bonus selon le nombre de lignes simultanées
            self.score += [0, 100, 300, 500, 800][len(full)] * self.level
            self.level = self.lines // 10 + 1  # Monte de niveau toutes les 10 lignes

    def _blk(self, surf, x, y, color):
        # Dessine un carré (bloc) avec une bordure blanche
        r = (self.XO + x * self.BS, self.YO + y * self.BS, self.BS, self.BS)
        pygame.draw.rect(surf, color, r)
        pygame.draw.rect(surf, BLANC, r, 1)

    def draw(self, surf):
        # Dessine le plateau de jeu
        board = (self.XO, self.YO, self.LG * self.BS, self.HG * self.BS)
        pygame.draw.rect(surf, (15, 15, 25), board)  # Fond du plateau
        pygame.draw.rect(surf, (50, 50, 80), board, 2)  # Bordure du plateau

        # 1. Dessine les blocs déjà fixés dans la grille
        for y, row in enumerate(self.grid):
            for x, c in enumerate(row):
                if c: self._blk(surf, x, y, c)

        # 2. Dessine le "fantome"
        gy = self.ghost_y()
        for r, row in enumerate(self.cur['shape']):
            for c, v in enumerate(row):
                if v:
                    rect = (self.XO + (self.cur['x'] + c) * self.BS, self.YO + (gy + r) * self.BS, self.BS, self.BS)
                    pygame.draw.rect(surf, (38, 38, 48), rect, 1)  # Juste un contour gris sombre

        # 3. Dessine la pièce active
        for r, row in enumerate(self.cur['shape']):
            for c, v in enumerate(row):
                if v: self._blk(surf, self.cur['x'] + c, self.cur['y'] + r, self.cur['color'])

        # INTERFACE
        # Affichage du texte "NEXT" et du cadre pour la pièce suivante
        surf.blit(font_pixel.render("NEXT", True, BLANC), (self.XO + 270, self.YO))
        pygame.draw.rect(surf, (20, 20, 30), (self.XO + 270, self.YO + 30, 100, 100))
        for r, row in enumerate(self.nxt['shape']):
            for c, v in enumerate(row):
                if v:  # Dessine la pièce suivante en miniature
                    pygame.draw.rect(surf, self.nxt['color'],
                                     (self.XO + 285 + c * 20, self.YO + 50 + r * 20, 18, 18))

        # Affichage du Score et du Niveau à gauche
        surf.blit(font_pixel.render(f"SCORE:{self.score}", True, JAUNE), (self.XO - 180, self.YO + 50))
        surf.blit(font_pixel.render(f"LEVEL:{self.level}", True, CYAN), (self.XO - 180, self.YO + 80))

        # Message de fin de partie
        if self.game_over:
            msg = font_main.render("GAME OVER – ESC", True, JOYCON_ROUGE)
            surf.blit(msg, (self.XO - 60, self.HG * self.BS // 2))


