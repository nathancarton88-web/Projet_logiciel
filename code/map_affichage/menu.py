# menu.py 
# menu principal de L'ILE AUX MINI-JEUX


import pygame, math, random
from save_manager import list_saves, load_save, new_save, SKINS, skin_by_id

# couleurs de base pour le theme plage
CIEL1 = (30, 140, 255)
CIEL2 = (135, 210, 255)
MER1 = (0, 180, 200)
MER2 = (0, 120, 160)
SABLE = (255, 210, 100)
SABLE_SOMBRE = (240, 175, 60)
SOLEIL = (255, 240, 80)
ORANGE = (255, 140, 0)
BLANC = (255, 255, 240)
ROUGE = (255, 70, 50)
VERT_PALMIER = (60, 200, 80)
VERT_FONCE = (20, 120, 40)
BOIS_CLAIR = (255, 250, 220)
BOIS = (200, 140, 50)

FICHIER_ZIK = "assets/music/menu.ogg"

def load_fonts():

    try:
        return {
            "title": pygame.font.SysFont("Courier New", 48, bold=True),
            "big":   pygame.font.SysFont("Courier New", 26, bold=True),
            "mid":   pygame.font.SysFont("Courier New", 19, bold=True),
            "small": pygame.font.SysFont("Courier New", 14),
            "pixel": pygame.font.SysFont("Consolas",    17),
        }
    except Exception as e:
        print("erreur chargement fonts :", e)
        return {
            "title": pygame.font.Font(None, 56),
            "big":   pygame.font.Font(None, 32),
            "mid":   pygame.font.Font(None, 24),
            "small": pygame.font.Font(None, 18),
            "pixel": pygame.font.Font(None, 20),
        }

def centrer_texte(ecran, txt_surf, y):
    # centrer n'importe quel texte facilement
    x = ecran.get_width() // 2 - txt_surf.get_width() // 2
    ecran.blit(txt_surf, (x, y))

def filtre_retro(ecran):
    # rajoute des fausses lignes de tele cathodique par dessus tout
    calque = pygame.Surface(ecran.get_size(), pygame.SRCALPHA)
    for y in range(0, ecran.get_height(), 3):
        pygame.draw.line(calque, (0, 0, 0, 18), (0, y), (ecran.get_width(), y))
    ecran.blit(calque, (0, 0))

#Fonctions de dessin

def dessine_soleil(ecran, cx, cy, r, t):
    # fait une boucle pour le halo lumineux
    for i in range(3):
        alpha = 60 - i * 18
        rayon_halo = r + 14 + i * 10
        halo = pygame.Surface((rayon_halo*2, rayon_halo*2), pygame.SRCALPHA)
        pygame.draw.circle(halo, (*SOLEIL, alpha), (rayon_halo, rayon_halo), rayon_halo)
        ecran.blit(halo, (cx - rayon_halo, cy - rayon_halo))
        
    pygame.draw.circle(ecran, ORANGE, (cx, cy), r + 2)
    pygame.draw.circle(ecran, SOLEIL,  (cx, cy), r)
    
    # ptits calculs de trigo pour faire tourner les rayons
    nb_rayons = 12
    for i in range(nb_rayons):
        angle = math.radians(i * 360 / nb_rayons + t * 15)
        x1 = cx + int((r + 5)  * math.cos(angle))
        y1 = cy + int((r + 5)  * math.sin(angle))
        x2 = cx + int((r + 14) * math.cos(angle))
        y2 = cy + int((r + 14) * math.sin(angle))
        pygame.draw.line(ecran, SOLEIL, (x1, y1), (x2, y2), 3)

def dessine_palmier(ecran, bx, by, inverser=False):

    for i in range(7):
        w = 10 - i
        col = (160 + i*8, 100 + i*5, 40) # marron
        decalage = (2 if inverser else -2)*i//3
        pygame.draw.rect(ecran, col, (bx - w//2 + decalage, by - i*18, w, 20))
        
    tx, ty = bx + (-5 if inverser else 5), by - 7*18 + 10
    
    feuilles = [(-60, -30), (-40, -55), (-15, -65), (15, -60), (40, -50), (55, -25)]
    if inverser:
        feuilles = [(-x, y) for x, y in feuilles]
        
    for dx, dy in feuilles:
        pygame.draw.line(ecran, VERT_FONCE, (tx, ty), (tx + dx, ty + dy), 5)
        pygame.draw.line(ecran, VERT_PALMIER, (tx, ty), (tx + dx, ty + dy), 3)

def dessine_vague(ecran, y_base, t, couleur, alpha=180, amp=8, freq=0.018):
    W = ecran.get_width()
    pts = []
    for x in range(W + 1):
        y = y_base + int(amp * math.sin(x * freq + t * 2))
        pts.append((x, y))
    pts.append((W, ecran.get_height()))
    pts.append((0, ecran.get_height()))
    
    surf_vague = pygame.Surface((W, ecran.get_height()), pygame.SRCALPHA)
    pygame.draw.polygon(surf_vague, (*couleur, alpha), pts)
    ecran.blit(surf_vague, (0, 0))


class MainMenu:
    # options de base
    OPTIONS = ["NOUVELLE PARTIE", "CONTINUER", "QUITTER"]

    def __init__(self, ecran):
        self.ecran = ecran
        self.W, self.H = ecran.get_size()
        self.fonts = load_fonts()
        
        self.etat = "MAIN" # MAIN, SELECT, NEW_NAME, SKIN
        self.result = None
        self.running = True
        
        self.index_menu = 0
        self.liste_sauvegardes = []
        self.index_save = 0
        
        self.texte_input = ""
        self.erreur_input = ""
        self.index_skin = 0
        self.nom_en_attente = ""
        
        self.cache_skins = {}
        self.load_images_skins()
        
        self.timer_clignotement = 0
        self.temps = 0.0
        
        # generation des nuages au pif
        self.nuages = []
        for i in range(6):
            n = {
                "x": random.uniform(0, self.W), 
                "y": random.uniform(50, 160),
                "vx": random.uniform(0.2, 0.6), 
                "scale": random.uniform(0.7, 1.3)
            }
            self.nuages.append(n)
            
        # pareil pour les mouettes
        self.mouettes = []
        for i in range(5):
            m = {
                "x": random.uniform(0, self.W), 
                "y": random.uniform(80, 180),
                "vx": random.uniform(0.5, 1.2), 
                "phase": random.uniform(0, math.pi*2)
            }
            self.mouettes.append(m)
            
        self.start_zik()

    def start_zik(self):
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(FICHIER_ZIK)
            pygame.mixer.music.set_volume(0.4)
            pygame.mixer.music.play(-1)
        except Exception as e:
            print("erreur musique menu :", e)

    def load_images_skins(self):
        # decoupe les spritesheets pour afficher le perso dans le menu
        for sk in SKINS:
            try:
                sheet = pygame.image.load(sk["walk"]).convert_alpha()
                w = sheet.get_width() // 4
                h = sheet.get_height() // 4
                frame = sheet.subsurface(pygame.Rect(0, 0, w, h))
                # on le grossit x5 pour bien le voir
                self.cache_skins[sk["id"]] = pygame.transform.scale(frame, (w*5, h*5))
            except Exception as e:
                print("bug chargement skin", sk["id"])
                self.cache_skins[sk["id"]] = None

    def run(self):
        clock = pygame.time.Clock()
        
        while self.running:
            dt = clock.tick(60)
            self.timer_clignotement = (self.timer_clignotement + dt) % 1000
            self.temps += dt / 1000.0
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # clic sur la croix rouge
                    return None
                
                #  inputs selon la page ou on est
                if event.type == pygame.KEYDOWN:
                    if self.etat == "MAIN":
                        self.input_main(event)
                    elif self.etat == "SELECT":
                        self.input_select(event)
                    elif self.etat == "NEW_NAME":
                        self.input_name(event)
                    elif self.etat == "SKIN":
                        self.input_skin(event)

            self.dessiner_tout()
            pygame.display.flip()
            
            if self.result is not None:
                try:
                    pygame.mixer.music.fadeout(600)
                except:
                    pass
                return self.result
                
        return None



    def input_main(self, event):
        k = event.key
        if k == pygame.K_UP or k == pygame.K_LEFT:
            self.index_menu = (self.index_menu - 1) % len(self.OPTIONS)
        elif k == pygame.K_DOWN or k == pygame.K_RIGHT:
            self.index_menu = (self.index_menu + 1) % len(self.OPTIONS)
        elif k == pygame.K_RETURN:
            opt = self.OPTIONS[self.index_menu]
            if opt == "NOUVELLE PARTIE":
                self.etat = "NEW_NAME"
                self.texte_input = ""
                self.erreur_input = ""
            elif opt == "CONTINUER":
                self.liste_sauvegardes = list_saves()
                self.index_save = 0
                self.etat = "SELECT"
            else:
                self.running = False

    def input_select(self, event):
        k = event.key
        if not self.liste_sauvegardes:
            if k == pygame.K_ESCAPE: 
                self.etat = "MAIN"
            return
            
        if k == pygame.K_UP or k == pygame.K_LEFT:
            self.index_save = (self.index_save - 1) % len(self.liste_sauvegardes)
        elif k == pygame.K_DOWN or k == pygame.K_RIGHT:
            self.index_save = (self.index_save + 1) % len(self.liste_sauvegardes)
        elif k == pygame.K_RETURN:
            fichier = self.liste_sauvegardes[self.index_save]
            data = load_save(fichier)
            if data: 
                self.result = data
        elif k == pygame.K_ESCAPE:
            self.etat = "MAIN"

    def input_name(self, event):
        k = event.key
        if k == pygame.K_ESCAPE:
            self.etat = "MAIN"
        elif k == pygame.K_RETURN:
            nom = self.texte_input.strip()
            if len(nom) < 2:
                self.erreur_input = "MIN. 2 CARACTERES !"
            elif len(nom) > 12:
                self.erreur_input = "MAX. 12 CARACTERES !"
            else:
                self.nom_en_attente = nom
                self.index_skin = 0
                self.etat = "SKIN"
        elif k == pygame.K_BACKSPACE:
            self.texte_input = self.texte_input[:-1]
            self.erreur_input = ""
        else:
            c = event.unicode
            if c and c.isprintable() and len(self.texte_input) < 12:
                self.texte_input += c
                self.erreur_input = ""

    def input_skin(self, event):
        k = event.key
        if k == pygame.K_LEFT or k == pygame.K_UP:
            self.index_skin = (self.index_skin - 1) % len(SKINS)
        elif k == pygame.K_RIGHT or k == pygame.K_DOWN:
            self.index_skin = (self.index_skin + 1) % len(SKINS)
        elif k == pygame.K_RETURN:
            self.result = new_save(self.nom_en_attente, SKINS[self.index_skin]["id"])
        elif k == pygame.K_ESCAPE:
            self.etat = "NEW_NAME"

    # --- RENDU GRAPHIQUE ---

    def dessiner_tout(self):
        self.draw_bg()
        
        # dispatch selon letat
        if self.etat == "MAIN":
            self.draw_page_principale()
        elif self.etat == "SELECT":
            self.draw_page_saves()
        elif self.etat == "NEW_NAME":
            self.draw_page_nom()
        elif self.etat == "SKIN":
            self.draw_page_skin()
            
        filtre_retro(self.ecran)

    def draw_bg(self):
        t = self.temps
        
        # bg ciel degrade manuel
        hauteur_ciel = int(self.H * 0.58)
        for y in range(hauteur_ciel):
            ratio = y / hauteur_ciel
            r = int(CIEL1[0] + (CIEL2[0] - CIEL1[0]) * ratio)
            g = int(CIEL1[1] + (CIEL2[1] - CIEL1[1]) * ratio)
            b = int(CIEL1[2] + (CIEL2[2] - CIEL1[2]) * ratio)
            pygame.draw.line(self.ecran, (r, g, b), (0, y), (self.W, y))

        dessine_soleil(self.ecran, self.W - 140, 80, 44, t)

        for n in self.nuages:
            n["x"] += n["vx"]
            if n["x"] > self.W + 100:
                n["x"] = -100
            
            # dessine le nuage avec des petits cercles
            cx, cy = int(n["x"]), int(n["y"])
            s = n["scale"]
            blobs = [(0, 0, 28), (-26, 8, 20), (26, 8, 20), (-14, 14, 16), (14, 14, 16)]
            for dx, dy, rayon in blobs:
                pygame.draw.circle(self.ecran, BLANC, (int(cx + dx*s), int(cy + dy*s)), int(rayon*s))

        # anim des mouettes en arriere plan
        for m in self.mouettes:
            m["x"] += m["vx"]
            if m["x"] > self.W + 40:
                m["x"] = -40
            
            wing = int(5 * math.sin(t * 4 + m["phase"]))
            gx, gy = int(m["x"]), int(m["y"])
            pygame.draw.line(self.ecran, (60, 60, 90), (gx - 10, gy + wing), (gx, gy), 2)
            pygame.draw.line(self.ecran, (60, 60, 90), (gx, gy), (gx + 10, gy + wing), 2)

        # degrade de la mer
        mer_y = hauteur_ciel
        for y in range(mer_y, self.H - 60):
            ratio = (y - mer_y) / (self.H - 60 - mer_y)
            r = int(MER1[0] + (MER2[0] - MER1[0]) * ratio)
            g = int(MER1[1] + (MER2[1] - MER1[1]) * ratio)
            b = int(MER1[2] + (MER2[2] - MER1[2]) * ratio)
            pygame.draw.line(self.ecran, (r, g, b), (0, y), (self.W, y))

        dessine_vague(self.ecran, hauteur_ciel + 5, t, MER1, 120, 6, 0.020)
        dessine_vague(self.ecran, hauteur_ciel + 18, t, (0, 200, 220), 80, 5, 0.016)

        # degrade sable en bas
        sand_y = self.H - 60
        for y in range(sand_y, self.H):
            ratio = (y - sand_y) / (self.H - sand_y)
            r = int(SABLE[0] + (SABLE_SOMBRE[0] - SABLE[0]) * ratio)
            g = int(SABLE[1] + (SABLE_SOMBRE[1] - SABLE[1]) * ratio)
            b = int(SABLE[2] + (SABLE_SOMBRE[2] - SABLE[2]) * ratio)
            pygame.draw.line(self.ecran, (r, g, b), (0, y), (self.W, y))

        dessine_palmier(self.ecran, 90, self.H - 10, False)
        dessine_palmier(self.ecran, self.W - 80, self.H - 10, True)

    def draw_page_principale(self):
        # panneau titre
        pw, ph = 640, 110
        px = self.W // 2 - pw // 2
        py = 28
        
        # ombre sale
        ombre = pygame.Surface((pw, ph), pygame.SRCALPHA)
        ombre.fill((0, 0, 0, 60))
        self.ecran.blit(ombre, (px + 6, py + 6))
        
        pygame.draw.rect(self.ecran, (200, 150, 70), (px, py, pw, ph), border_radius=8)
        pygame.draw.rect(self.ecran, (160, 110, 40), (px, py, pw, ph), 3, border_radius=8)

        # lignes bois
        for i in range(6):
            lx = px + 8 + i * (pw - 16) // 6
            pygame.draw.line(self.ecran, (180, 130, 55), (lx, py + 6), (lx, py + ph - 6), 1)

        titre1 = self.fonts["title"].render("L'ILE AUX", True, (120, 60, 0))
        centrer_texte(self.ecran, titre1, py + 8)

        titre2 = self.fonts["title"].render("MINI-JEUX", True, ROUGE)
        centrer_texte(self.ecran, titre2, py + 57)

        # boucle affichage boutons
        y_depart = 168
        for i in range(len(self.OPTIONS)):
            opt = self.OPTIONS[i]
            est_select = (i == self.index_menu)
            y = y_depart + i * 62

            # on change un peu la couleur selon le bouton
            if i == 0:
                fond = (255, 240, 180)
                bord = (200, 140, 50)
            elif i == 1:
                fond = (220, 255, 200)
                bord = (50, 160, 60)
            else:
                fond = (255, 210, 200)
                bord = (200, 80, 60)

            w_btn, h_btn = 460, 48
            x_btn = self.W // 2 - w_btn // 2

            pygame.draw.rect(self.ecran, fond, (x_btn, y, w_btn, h_btn), border_radius=7)
            epaisseur = 3 if est_select else 2
            pygame.draw.rect(self.ecran, bord, (x_btn, y, w_btn, h_btn), epaisseur, border_radius=7)

            # curseur de menu avec timer
            clignote = self.timer_clignotement < 500
            if est_select and clignote:
                prefix = ">> "
            elif est_select:
                prefix = "   "
            else:
                prefix = "   "
                
            couleur_txt = (40, 20, 0) if est_select else (90, 60, 20)
            txt_rendu = self.fonts["big"].render(prefix + opt, True, couleur_txt)
            
            # centre le text dans le bouton
            self.ecran.blit(txt_rendu, (x_btn + w_btn//2 - txt_rendu.get_width()//2, y + h_btn//2 - txt_rendu.get_height()//2))

        # petits tips en bas de l'ecran
        info = self.fonts["small"].render("[ FLECHES ] NAVIGUER     [ ENTREE ] VALIDER", True, (100, 70, 20))
        centrer_texte(self.ecran, info, self.H - 38)
        
        version = self.fonts["small"].render("v1.0", True, (160, 120, 60))
        self.ecran.blit(version, (10, self.H - 22))

    def draw_top_bar(self, titre):
        # header generique pour les sous menus
        w_bar = 520
        h_bar = 44
        x = self.W // 2 - w_bar // 2
        y = 78
        pygame.draw.rect(self.ecran, (200, 150, 70), (x, y, w_bar, h_bar), border_radius=6)
        pygame.draw.rect(self.ecran, (160, 110, 40), (x, y, w_bar, h_bar), 2, border_radius=6)
        
        txt = self.fonts["mid"].render(titre, True, (60, 30, 0))
        centrer_texte(self.ecran, txt, y + h_bar // 2 - txt.get_height() // 2)

    def draw_page_saves(self):
        self.draw_top_bar(" CHARGER UNE PARTIE ")
        
        if not self.liste_sauvegardes:
            msg = self.fonts["mid"].render("AUCUNE SAUVEGARDE TROUVEE.", True, ROUGE)
            centrer_texte(self.ecran, msg, self.H // 2)
        else:
            for i in range(len(self.liste_sauvegardes)):
                fichier = self.liste_sauvegardes[i]
                est_selec = (i == self.index_save)
                
                # essaye de recup le best score pour l'afficher (un peu moche mais marche)
                data = load_save(fichier) or {}
                hs = data.get("highscores", {})
                meilleur_score = max(hs.values()) if hs else 0
                
                curseur = ">" if est_selec else " "
                label = f"{curseur} {fichier:<12}  BEST:{meilleur_score:>6}"
                
                couleur_fond = (255, 245, 200) if est_selec else (230, 220, 180)
                couleur_bord = BOIS if est_selec else (180, 140, 80)
                
                y_btn = 185 + i * 48
                w_btn, h_btn = 520, 38
                x_btn = self.W // 2 - w_btn // 2
                
                pygame.draw.rect(self.ecran, couleur_fond, (x_btn, y_btn, w_btn, h_btn), border_radius=6)
                pygame.draw.rect(self.ecran, couleur_bord, (x_btn, y_btn, w_btn, h_btn), 2, border_radius=6)
                
                c_txt = (40, 20, 0) if est_selec else (100, 70, 30)
                txt = self.fonts["mid"].render(label, True, c_txt)
                centrer_texte(self.ecran, txt, y_btn + 9)
                
        aide = self.fonts["small"].render("[ FLECHES ] CHOISIR   [ ENTREE ] JOUER   [ ECHAP ] RETOUR", True, (100, 70, 20))
        centrer_texte(self.ecran, aide, self.H - 34)

    def draw_page_nom(self):
        self.draw_top_bar(">> NOUVELLE PARTIE <<")
        
        lbl = self.fonts["mid"].render("ENTRE TON NOM :", True, (60, 30, 0))
        centrer_texte(self.ecran, lbl, 215)
        
        bw, bh = 380, 48
        bx = self.W // 2 - bw // 2
        by = 255
        pygame.draw.rect(self.ecran, (255, 250, 210), (bx, by, bw, bh), border_radius=7)
        pygame.draw.rect(self.ecran, BOIS, (bx, by, bw, bh), 2, border_radius=7)
        
        c = "_" if self.timer_clignotement < 500 else " "
        input_rendu = self.fonts["big"].render(self.texte_input + c, True, (60, 30, 0))
        self.ecran.blit(input_rendu, (bx + 14, by + 10))
        
        if self.erreur_input != "":
            err = self.fonts["small"].render("! " + self.erreur_input, True, ROUGE)
            centrer_texte(self.ecran, err, by + bh + 12)
            
        aide = self.fonts["small"].render("[ ENTREE ] VALIDER   [ ECHAP ] RETOUR", True, (100, 70, 20))
        centrer_texte(self.ecran, aide, self.H - 34)

    def draw_page_skin(self):
        self.draw_top_bar(">> CHOIX DU PERSONNAGE <<")
        
        skin_actuel = SKINS[self.index_skin]
        img = self.cache_skins.get(skin_actuel["id"])
        
        fx, fy = self.W // 2 - 70, 185
        fw, fh = 140, 160
        
        pygame.draw.rect(self.ecran, (255, 248, 210), (fx, fy, fw, fh), border_radius=8)
        pygame.draw.rect(self.ecran, BOIS, (fx, fy, fw, fh), 2, border_radius=8)
        
        if img:
            self.ecran.blit(img, (fx + fw//2 - img.get_width()//2, fy + fh//2 - img.get_height()//2))
        else:
            ph = self.fonts["mid"].render("???", True, (160, 130, 90))
            centrer_texte(self.ecran, ph, fy + fh//2)
            
        nom_skin = self.fonts["big"].render(skin_actuel["label"].upper(), True, (60, 30, 0))
        centrer_texte(self.ecran, nom_skin, fy + fh + 14)
        
        if len(SKINS) > 1:
            nav = self.fonts["mid"].render(f"<  {self.index_skin + 1} / {len(SKINS)}  >", True, (160, 130, 90))
            centrer_texte(self.ecran, nav, fy + fh + 44)
            
        aide = self.fonts["small"].render("[ FLECHES ] CHANGER   [ ENTREE ] CHOISIR   [ ECHAP ] RETOUR", True, (100, 70, 20))
        centrer_texte(self.ecran, aide, self.H - 34)