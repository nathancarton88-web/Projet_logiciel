"""
save_manager.py
───────────────
Gère la sauvegarde et le chargement de la partie dans saves/<nom>.json

Structure du fichier de sauvegarde :
{
    "player_name": "Ash",
    "skin":        "hero_01_white_f",   ← nom du fichier sans extension
    "map":         "map_0",
    "position":    [512, 288],
    "highscores":  {"tetris": 0, "pacman": 0, "snake": 0, "space": 0}
}
"""

import json, os

SAVE_DIR      = "saves"
SCORES_KEYS   = ("tetris", "pacman", "snake", "space")
DEFAULT_SCORES = {k: 0 for k in SCORES_KEYS}

# Skins disponibles : (id, chemin relatif spritesheet marche, chemin vélo)
SKINS = [
    {
        "id":    "hero_white_f",
        "label": "Héroïne (blanc)",
        "walk":  "assets/sprite/hero_01_white_f_walk.png",
        "bike":  "assets/sprite/hero_01_white_f_cycle_wheel.png",
        "run":   "assets/sprite/hero_01_white_f_run.png",
        "surf":  "assets/sprite/hero_01_white_f_surf.png",
    },
    {
        "id":    "hero_red_m",
        "label": "Héros (rouge)",
        "walk":  "assets/sprite/hero_01_red_m_walk.png",
        "bike":  "assets/sprite/hero_01_red_m_bike.png",
        "run":   "assets/sprite/hero_01_red_m_run.png",
        "surf":  "assets/sprite/hero_01_red_m_surf.png",
    },
]


def _ensure_dir():
    os.makedirs(SAVE_DIR, exist_ok=True)


def list_saves() -> list[str]:
    """Retourne la liste des noms de joueurs sauvegardés."""
    _ensure_dir()
    saves = []
    for f in os.listdir(SAVE_DIR):
        if f.endswith(".json"):
            saves.append(f[:-5])
    return sorted(saves)


def save_exists(name: str) -> bool:
    return os.path.exists(os.path.join(SAVE_DIR, f"{name}.json"))


def load_save(name: str) -> dict | None:
    path = os.path.join(SAVE_DIR, f"{name}.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Garantit que toutes les clés existent
        data.setdefault("player_name", name)
        data.setdefault("skin",        SKINS[0]["id"])
        data.setdefault("map",         "map_0")
        data.setdefault("position",    [512, 288])
        data.setdefault("highscores",  dict(DEFAULT_SCORES))
        return data
    except Exception:
        return None


def new_save(name: str, skin_id: str) -> dict:
    data = {
        "player_name": name,
        "skin":        skin_id,
        "map":         "map_0",
        "position":    [512, 288],
        "highscores":  dict(DEFAULT_SCORES),
    }
    write_save(data)
    return data


def write_save(data: dict) -> None:
    _ensure_dir()
    name = data.get("player_name", "joueur")
    path = os.path.join(SAVE_DIR, f"{name}.json")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[save_manager] Erreur sauvegarde : {e}")


def skin_by_id(skin_id: str) -> dict:
    for s in SKINS:
        if s["id"] == skin_id:
            return s
    return SKINS[0]
