# ete_theme.py
# Fichier fourre-tout pour les couleurs et les trucs de dessin qui reviennent tout le temps


import pygame, math

# Palette de couleurs (piquées sur coolors)
CIEL      = ( 30, 140, 255)
CIEL_BAS  = (135, 210, 255)
MER       = (  0, 180, 200)
MER_FONC  = (  0, 120, 160)
SABLE     = (255, 210, 100)
SABLE2    = (200, 150,  70)
SOLEIL    = (255, 235,  70)
SOLEIL2   = (255, 160,  20)
BLANC     = (255, 248, 220)
BRUN      = ( 60,  30,   0)
BRUN2     = (100,  60,  20)
ORANGE    = (255, 140,   0)
ROUGE_VIF = (255,  70,  50)
VERT_PALM = ( 60, 200,  80)
VERT_FONC = ( 20, 120,  40)
JAUNE_VIF = (255, 220,  40)
ROSE      = (255, 120, 160)
PANEL_BG  = (255, 248, 210)
PANEL_BD  = (200, 140,  50)
BOIS      = (210, 160,  75)
BOIS_FONC = (150, 100,  35)
GRIS_ETE  = (160, 130,  90)

# fond commun des mini jeux
GAME_BG   = (  8,  80, 120)

def draw_game_bg(surf):
    w, h = surf.get_size()
    
    #  un gradendé pour l'eau
    for y in range(h):
        ratio = y / h
        r = int(10  + (0   - 10 ) * ratio)
        g = int(90  + (60  - 90 ) * ratio)
        b = int(140 + (100 - 140) * ratio)
        pygame.draw.line(surf, (r, g, b), (0, y), (w, y))
        
    # ptits reflets a la surface avec un math.sin
    t = pygame.time.get_ticks() / 1000.0
    for i in range(12):
        rx = int((w * (i * 0.137 % 1.0)))
        ry = int((h * (i * 0.211 % 1.0)))
        alpha = int(20 + 15 * math.sin(t * 1.5 + i))
        calque = pygame.Surface((30, 6), pygame.SRCALPHA)
        calque.fill((*MER, alpha))
        surf.blit(calque, (rx, ry))

def draw_wood_panel(surf, rect, radius=6):
    # le fameux panneau de cabane de plage
    x, y, w, h = rect
    pygame.draw.rect(surf, BOIS, (x, y, w, h), border_radius=radius)
    # lignes du bois
    for i in range(6):
        lx = x + 8 + i * (w - 16) // 6
        pygame.draw.line(surf, SABLE2, (lx, y+4), (lx, y+h-4), 1)
    pygame.draw.rect(surf, BOIS_FONC, (x, y, w, h), 2, border_radius=radius)

def draw_wave_line(surf, y_base, t, color=(0, 200, 220), alpha=120, amp=4, freq=0.025):
    # trigo de l'enfer pour animer la vague
    w = surf.get_width()
    pts = [(x, y_base + int(amp * math.sin(x * freq + t * 2))) for x in range(w+1)]
    pts += [(w, y_base + 20), (0, y_base + 20)]
    
    ws = pygame.Surface((w, 20 + amp), pygame.SRCALPHA)
    
    #  zip pour les coords du polygone
    pygame.draw.polygon(ws, (*color, alpha), [(x, p[1]-y_base) for x,p in zip(range(w+1), pts)] + [(w,20),(0,20)])
    surf.blit(ws, (0, y_base))

def draw_score_hud(surf, score, label, best=None, font=None):
    # interface des scores superposee
    if font is None:
        try:    
            font = pygame.font.SysFont("Courier New", 16, bold=True)
        except: 
            font = pygame.font.Font(None, 20)
            
    draw_wood_panel(surf, (6, 6, 180, 28), radius=5)
    t = font.render(f"{label}: {score}", True, BRUN)
    surf.blit(t, (14, 12))
    
    if best is not None:
        draw_wood_panel(surf, (6, 38, 180, 24), radius=5)
        b = font.render(f"BEST: {best}", True, BRUN2)
        surf.blit(b, (14, 42))

def draw_game_over(surf, font_big=None):
    # ecran de la mort (quand le joueur est mauvais comme jack)
    if font_big is None:
        try:    
            font_big = pygame.font.SysFont("Courier New", 34, bold=True)
        except: 
            font_big = pygame.font.Font(None, 40)
            
    w, h = surf.get_size()
    
    # filtre sombre
    ov = pygame.Surface((w, h), pygame.SRCALPHA)
    ov.fill((20, 10, 0, 160))
    surf.blit(ov, (0,0))
    
    draw_wood_panel(surf, (w//2-200, h//2-30, 400, 60), radius=8)
    msg = font_big.render("GAME OVER", True, ROUGE_VIF)
    surf.blit(msg, (w//2 - msg.get_width()//2, h//2 - msg.get_height()//2))
    
    try:
        f_petit = pygame.font.SysFont("Courier New", 14)
    except:
        f_petit = pygame.font.Font(None, 18)
        
    sub = f_petit.render("[ ECHAP ] Retour", True, BRUN2)
    surf.blit(sub, (w//2 - sub.get_width()//2, h//2 + 26))