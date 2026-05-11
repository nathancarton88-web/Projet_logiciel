import pygame, random, math
pygame.init()


L_ECRAN, H_ECRAN = 1000, 600  # Dimensions totales de la fenêtre Windows
L_INTERNE, H_INTERNE = 700, 500  # Dimensions de la zone de jeu "active" à l'intérieur de la console
X_DEBUT, Y_DEBUT = 150, 50  # Décalage pour centrer la zone de jeu
screen = pygame.display.set_mode((L_ECRAN, H_ECRAN))  # Création de la surface d'affichage
pygame.display.set_caption("Le gaming c'est cool")  # Titre de la fenêtre
clock = pygame.time.Clock()  # Horloge pour contrôler les FPS (tours par seconde)


NOIR_CHASSIS = (20, 20, 22)  # Couleur de la carrosserie de la console
ECRAN_OFF = (5, 5, 10)  # Couleur de fond de l'écran éteint
JOYCON_BLEU = (0, 190, 230)  # Bleu style Joy-Con gauche
JOYCON_ROUGE = (255, 60, 50)  # Rouge style Joy-Con droit
BLANC = (255, 255, 255)  # Blanc pur
CYAN = (0, 255, 255)  # Cyan pour le niveau
JAUNE = (255, 230, 0)  # Jaune pour le score et les bonus
VERT = (50, 255, 80)  # Vert fluo
GRIS_BOUTON = (50, 50, 55)  # Gris foncé pour les détails

# CHARGEMENT DES POLICES D'ÉCRAN
try:

    font_sys = pygame.font.SysFont("Segoe UI", 22, bold=True)
    font_main = pygame.font.SysFont("Segoe UI", 35, bold=True)
    font_pixel = pygame.font.SysFont("Consolas", 20)
    font_large = pygame.font.SysFont("Segoe UI", 55, bold=True)
except Exception:
    # si les polices précédentes ne sont pas installées
    font_sys = pygame.font.Font(None, 24)
    font_main = pygame.font.Font(None, 40)
    font_pixel = pygame.font.Font(None, 20)
    font_large = pygame.font.Font(None, 65)


class SnakeNeon:
    # Paramètres de la grille de jeu
    COLS, ROWS, TILE = 20, 15, 25  # 20 colonnes, 15 lignes, chaque case fait 25 pixels
    XO = (L_INTERNE - 20 * 25) // 2  # Calcul de l'origine X pour centrer la grille
    YO = (H_INTERNE - 15 * 25) // 2  # Calcul de l'origine Y pour centrer la grille

    def __init__(self):
        self.level = 1;
        self.score = 0;
        self.game_over = False  # Initialisation du score et de l'état
        self.reset()  # Appel de la fonction de remise à zéro pour démarrer

    def reset(self):
        cx, cy = self.COLS // 2, self.ROWS // 2  # Coordonnées du centre de la grille
        self.snake = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]  # Liste des segments du serpent (tête en premier)
        self.direction = (1, 0);
        self.next_dir = (1, 0)  # Direction actuelle et direction demandée (pour éviter l'auto-collision)
        self.score = 0;
        self.level = 1;
        self.eaten = 0  # Reset des stats de jeu
        self.move_timer = 0;
        self.speed = 160  # Timer de mouvement et vitesse initiale (en ms)
        self.game_over = False;
        self.flash_timer = 0  # États visuels du Game Over
        self.boost_timer = 0  # Temps restant pour l'effet de vitesse
        self.apple_pulse = 0.0;
        self.bonus_blink = 0.0  # Variables d'animation pour les objets
        self.bonus = None;
        self.bonus_timer = 0  # Gestion de l'apparition du bonus étoile
        self.walls = self._build_walls()  # Génération des murs du niveau 1
        self.apple = self._free()  # Placement de la première pomme

    def _build_walls(self):
        # Génère des murs en forme de carrés concentriques selon le niveau
        walls = set()
        rings = (self.level - 1) // 5  # Tous les 5 niveaux, une nouvelle couche de murs apparaît
        for ring in range(1, rings + 1):
            for x in range(ring, self.COLS - ring):
                walls.add((x, ring));
                walls.add((x, self.ROWS - 1 - ring))  # Murs horizontaux
            for y in range(ring + 1, self.ROWS - ring - 1):
                walls.add((ring, y));
                walls.add((self.COLS - 1 - ring, y))  # Murs verticaux
        return walls

    def _free(self):
        # Trouve une case vide (sans serpent, sans mur, sans bonus) pour placer une pomme
        used = set(self.snake) | self.walls
        if self.bonus: used.add(self.bonus)
        cands = [(x, y) for x in range(self.COLS) for y in range(self.ROWS) if (x, y) not in used]
        return random.choice(cands) if cands else (0, 0)  # Retourne une coordonnée aléatoire parmi les libres

    def set_dir(self, d):
        # Change la direction si elle n'est pas opposée à la direction actuelle (empêche de faire demi-tour sur soi-même)
        if d[0] != -self.direction[0] or d[1] != -self.direction[1]:
            self.next_dir = d

    def _spawn_bonus(self):
        # 28% de chance de faire apparaître une étoile après avoir mangé une pomme
        if self.bonus is None and random.random() < 0.28:
            self.bonus = self._free();
            self.bonus_timer = 240  # L'étoile reste 240 frames

    def update(self, dt):
        # Logique principale mise à jour à chaque frame
        if self.game_over:
            if self.flash_timer > 0: self.flash_timer -= 1  # Décompte de l'effet visuel rouge de mort
            return

        # Mise à jour des timers d'animation (sinus pour le battement de la pomme)
        self.apple_pulse += 0.12;
        self.bonus_blink += 0.20

        if self.bonus_timer > 0:
            self.bonus_timer -= 1  # L'étoile disparaît avec le temps
            if self.bonus_timer == 0: self.bonus = None

        if self.boost_timer > 0: self.boost_timer -= 1  # Décompte de la vitesse bonus

        self.move_timer += dt  # Accumulation du temps écoulé
        # Détermine la vitesse : si boost actif, on bouge 2x plus vite
        eff = self.speed // 2 if self.boost_timer > 0 else self.speed

        if self.move_timer < eff: return  # Si le temps écoulé est inférieur à la vitesse, on ne bouge pas encore

        self.move_timer = 0  # On réinitialise le timer après un mouvement
        self.direction = self.next_dir  # On valide la direction demandée

        hx, hy = self.snake[0]  # Position actuelle de la tête
        nx, ny = hx + self.direction[0], hy + self.direction[1]  # Future position de la tête

        #  GESTION DES COLLISIONS
        if (nx < 0 or nx >= self.COLS or ny < 0 or ny >= self.ROWS
                or (nx, ny) in self.walls or (nx, ny) in set(self.snake)):
            self.game_over = True;
            self.flash_timer = 30;
            return  # Fin de partie si mur ou corps touché

        self.snake.insert(0, (nx, ny))  # Ajout de la nouvelle tête

        # COLLISION AVEC LA POMME
        if (nx, ny) == self.apple:
            self.score += 10 * self.level;
            self.eaten += 1
            if self.eaten % 5 == 0:  # Tous les 5 repas : niveau supérieur + vitesse augmente
                self.level += 1;
                self.speed = max(60, self.speed - 10)
                self.walls = self._build_walls()  # Mise à jour de la configuration des murs
            self.apple = self._free();
            self._spawn_bonus()  # Nouvelle pomme et chance de bonus

        # COLLISION AVEC LE BONUS
        elif self.bonus and (nx, ny) == self.bonus:
            self.score += 50 * self.level
            self.bonus = None;
            self.bonus_timer = 0;
            self.boost_timer = 180  # Active le mode BOOST
        else:
            self.snake.pop()  # Si on n'a rien mangé, on retire le dernier segment (mouvement normal)

    def _seg_color(self, i, total):
        # Calcule une couleur dégradée pour le corps du serpent (du bleu au violet)
        t = i / max(total - 1, 1)  # Ratio de la position dans le corps (0 à 1)
        return (int(t * 80), int((1 - t) * 255 + t * 30), int((1 - t) * 255 + t * 90))

    @staticmethod
    def _star(cx, cy, ro, n=5):
        # Calcule les points géométriques pour dessiner une étoile à 5 branches
        ri = ro // 2;
        pts = []
        for k in range(n * 2):
            a = math.radians(k * 180 / n - 90)  # Angle pour chaque pointe
            r = ro if k % 2 == 0 else ri  # Alterne entre rayon extérieur et intérieur
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        return pts

    def draw(self, surf):
        # DESSIN DU FOND ET DE LA GRILLE
        area = (self.XO, self.YO, self.COLS * self.TILE, self.ROWS * self.TILE)
        pygame.draw.rect(surf, (7, 9, 16), area)  # Fond de la zone de jeu
        for x in range(self.COLS + 1):  # Lignes verticales de la grille
            pygame.draw.line(surf, (13, 17, 27), (self.XO + x * self.TILE, self.YO),
                             (self.XO + x * self.TILE, self.YO + self.ROWS * self.TILE))
        for y in range(self.ROWS + 1):  # Lignes horizontales de la grille
            pygame.draw.line(surf, (13, 17, 27), (self.XO, self.YO + y * self.TILE),
                             (self.XO + self.COLS * self.TILE, self.YO + y * self.TILE))

        #  DESSIN DES MURS
        for wx, wy in self.walls:
            rx, ry = self.XO + wx * self.TILE, self.YO + wy * self.TILE
            pygame.draw.rect(surf, (50, 0, 80), (rx, ry, self.TILE, self.TILE))  # Base violet foncé
            pygame.draw.rect(surf, (130, 0, 200), (rx + 1, ry + 1, self.TILE - 2, self.TILE - 2), 1)  # Contour néon

        # EFFET DE FLASH
        if self.flash_timer > 0:
            fsurf = pygame.Surface((self.COLS * self.TILE, self.ROWS * self.TILE), pygame.SRCALPHA)
            fsurf.fill((255, 0, 0, int(190 * self.flash_timer / 30)))  # Carré rouge transparent
            surf.blit(fsurf, (self.XO, self.YO))

        #  DESSIN DU SERPENT
        total = len(self.snake)
        for i, (sx, sy) in enumerate(self.snake):
            col = self._seg_color(i, total)  # Couleur dégradée
            rx, ry = self.XO + sx * self.TILE + 2, self.YO + sy * self.TILE + 2
            pygame.draw.rect(surf, col, (rx, ry, self.TILE - 3, self.TILE - 3), border_radius=4)
            if i == 0:  # Si c'est la tête, on ajoute un petit contour blanc
                pygame.draw.rect(surf, BLANC, (rx, ry, self.TILE - 3, self.TILE - 3), 1, border_radius=4)

        #  DESSIN DE LA POMM
        ax = self.XO + self.apple[0] * self.TILE + self.TILE // 2
        ay = self.YO + self.apple[1] * self.TILE + self.TILE // 2
        pr = int(8 + abs(math.sin(self.apple_pulse)) * 3)  # Rayon qui varie selon le temps
        pygame.draw.circle(surf, (255, 40, 40), (ax, ay), pr)  # Cercle rouge
        pygame.draw.circle(surf, (255, 140, 140), (ax, ay), pr - 2)  # Reflet brillant

        # DESSIN DU BONUS
        if self.bonus:
            bx = self.XO + self.bonus[0] * self.TILE + self.TILE // 2
            by = self.YO + self.bonus[1] * self.TILE + self.TILE // 2
            sc = JAUNE if int(self.bonus_blink) % 2 == 0 else (255, 140, 0)  # Alterne jaune/orange
            pygame.draw.polygon(surf, sc, self._star(bx, by, 11))  # Remplissage
            pygame.draw.polygon(surf, BLANC, self._star(bx, by, 11), 1)  # Contour

        #INTERFACE
        surf.blit(font_pixel.render(f"SCORE:{self.score}", True, JAUNE), (10, 10))
        surf.blit(font_pixel.render(f"LEVEL:{self.level}", True, CYAN), (10, 35))
        if self.boost_timer > 0:  # Affiche le temps de boost si actif
            surf.blit(font_pixel.render(f"BOOST ! {self.boost_timer // 60 + 1}s", True, (255, 200, 0)),
                      (L_INTERNE // 2 - 55, 10))
        surf.blit(font_pixel.render("Fleches = direction | Pas de collision", True, (55, 55, 70)), (10, H_INTERNE - 20))

        if self.game_over:  # Message final
            msg = font_main.render("GAME OVER – ESC", True, JOYCON_ROUGE)
            surf.blit(msg, (L_INTERNE // 2 - msg.get_width() // 2, H_INTERNE // 2 - 20))