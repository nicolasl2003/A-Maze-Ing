*This project has been created as part of the 42 curriculum by nilinott, jbenhass.*

---

# A-Maze-ing

> Generate, solve and explore mazes — right in your terminal.

---

## 📌 Description

**A-Maze-ing** est un générateur de labyrinthes en Python 3.10+.

Le programme lit un fichier de configuration, génère un labyrinthe aléatoire (parfait ou non) en utilisant l'algorithme **Recursive Backtracker (DFS)**, calcule le plus court chemin entrée → sortie avec **BFS**, écrit le résultat dans un fichier de sortie au format hexadécimal, et affiche le labyrinthe de manière interactive dans le terminal via une **TUI Rich**.

Fonctionnalités clés :
- Génération reproductible via une graine (`SEED`)
- Labyrinthe parfait (un seul chemin possible)
- Motif « **42** » incrusté visuellement dans le labyrinthe
- Affichage en temps réel : re-génération, affichage du chemin, rotation de palette de couleurs
- Code de génération packagé en module `mazegen` installable via `pip`

---

## ⚙️ Instructions

### Prérequis

- Python ≥ 3.10
- [`uv`](https://github.com/astral-sh/uv) (installé automatiquement par le Makefile si absent) **ou** `poetry` disponible globalement.

### Installation des dépendances

```bash
make install
```

Cette commande crée un environnement virtuel `.venv/` et installe les dépendances listées dans `pyproject.toml` :

| Paquet | Rôle |
|---|---|
| `rich` | Rendu TUI (couleurs, panneaux, tableau) |
| `readchar` | Lecture non-bloquante des touches clavier |

### Lancer le programme

```bash
make run
```

Équivaut à :

```bash
poetry run python a_maze_ing.py config.txt
```

Vous pouvez passer n'importe quel fichier de configuration :

```bash
poetry run python a_maze_ing.py mon_config.txt
```

### Mode debug (pdb)

```bash
make debug
```

### Linting (flake8 + mypy)

```bash
make lint          # vérifications standards
make lint-strict   # mypy --strict
```

### Nettoyage

```bash
make clean    # supprime .venv, caches, dist/
make fclean   # idem + fichiers .whl et .tar.gz
```

### Build du package `mazegen`

```bash
make build
```

Génère `mazegen-*.whl` et `mazegen-*.tar.gz` à la racine du dépôt.

---

## 🗂️ Structure du fichier de configuration

Le fichier de configuration est un fichier texte avec un paramètre `CLÉ=VALEUR` par ligne.
Les lignes commençant par `#` sont des commentaires et sont ignorées.

### Clés obligatoires

| Clé | Type | Description | Exemple |
|---|---|---|---|
| `WIDTH` | entier ≥ 1 | Nombre de colonnes (largeur en cellules) | `WIDTH=20` |
| `HEIGHT` | entier ≥ 1 | Nombre de lignes (hauteur en cellules) | `HEIGHT=15` |
| `ENTRY` | `x,y` | Coordonnées de l'entrée (0-indexé) | `ENTRY=0,0` |
| `EXIT` | `x,y` | Coordonnées de la sortie (0-indexé) | `EXIT=19,14` |
| `OUTPUT_FILE` | chaîne | Nom du fichier de sortie hexadécimal | `OUTPUT_FILE=maze.txt` |
| `PERFECT` | `True`/`False` | Labyrinthe parfait (un seul chemin) | `PERFECT=True` |

### Clé optionnelle

| Clé | Type | Description | Exemple |
|---|---|---|---|
| `SEED` | entier | Graine pour la reproductibilité | `SEED=42` |

### Exemple de fichier de configuration (`config.txt`)

```ini
# Fichier de configuration A-Maze-ing
WIDTH=15
HEIGHT=20
OUTPUT_FILE=maze.txt
ENTRY=0,0
EXIT=10,15
PERFECT=True
# SEED=42
```

---

## 🧠 Algorithme de génération : Recursive Backtracker (DFS)

### Choix de l'algorithme

Le **Recursive Backtracker** (DFS itératif avec pile) a été retenu pour plusieurs raisons :

- Génère naturellement des **labyrinthes parfaits** (spanning tree complet) : idéal pour le flag `PERFECT=True`
- Produit des couloirs longs et sinueux, visuellement agréables
- Simple à implémenter et à adapter (ajout du motif 42, gestion de la graine)
- Performances en O(W × H), sans surcharge mémoire significative

### Fonctionnement (dans `mazegen/maze.py`, méthode `gen`)

1. La grille est initialisée avec **toutes les murs fermés** (`0xF` par cellule)
2. Les cellules du **motif « 42 »** sont marquées comme visitées dès le départ (elles resteront entièrement fermées)
3. Une pile commence depuis la cellule d'entrée
4. À chaque étape : on choisit aléatoirement un voisin non visité, on **casse le mur** entre les deux cellules (en désactivant le bit correspondant dans chaque cellule), et on empile le voisin
5. Si aucun voisin n'est disponible, on **dépile** (backtrack)
6. Le processus s'arrête quand la pile est vide : toutes les cellules accessibles ont été visitées

Pour le mode `PERFECT=False` (non encore implémenté explicitement), des passages supplémentaires pourraient être ouverts aléatoirement après la génération.

---

## 🔍 Algorithme de résolution : BFS

Le solver (`solver_back` dans `mazegen/maze.py`) utilise un **Breadth-First Search** pour trouver le **plus court chemin** entre l'entrée et la sortie.

- Exploration par vagues depuis l'entrée
- À chaque cellule, on vérifie les 4 directions via les bits de `map_[y][x]`
- S'arrête dès que la sortie est atteinte
- Reconstruit le chemin par rétro-propagation de la liste `path`

Le chemin est ensuite converti en séquence de lettres `N/E/S/W` par `path_to_moves`.

---

## 🎮 Contrôles de la TUI

Le rendu terminal (`src/tui_render.py`) utilise la bibliothèque `Rich`.

| Touche | Action |
|---|---|
| `R` | Re-générer un nouveau labyrinthe |
| `P` | Afficher / Masquer le chemin solution |
| `C` | Changer la palette de couleurs (5 thèmes : Classic, Ocean, Gold, Neon, Matrix) |
| `↑` / `W` | Faire défiler vers le haut |
| `↓` / `S` | Faire défiler vers le bas |
| `Q` / `Ctrl+C` | Quitter |

Le motif « 42 » est affiché en **bleu** dans la grille.
L'entrée est en **vert**, la sortie en **rouge**.

---

## 📦 Code réutilisable — module `mazegen`

Le module `mazegen` est un package Python autonome, installable via `pip`.

### Installation depuis le fichier buildé

```bash
pip install mazegen-0.1.0-py3-none-any.whl
```

### API publique

#### Classe `Config` (`mazegen.conf`)

Charge et valide un fichier de configuration.

```python
from mazegen import Config

cfg = Config("config.txt")
print(cfg.width)       # int
print(cfg.height)      # int
print(cfg.entry)       # Cell(x=0, y=0)
print(cfg.exit_)       # Cell(x=10, y=15)
print(cfg.perfect)     # bool
print(cfg.seed)        # int | None
print(cfg.output_file) # str
```

#### Classe `Maze` (`mazegen.maze`)

Génère le labyrinthe, calcule le chemin, écrit le fichier de sortie.

```python
from mazegen import Config, Maze

cfg = Config("config.txt")
maze = Maze(cfg)  # génère automatiquement au __init__

# Accéder à la structure brute (liste de listes d'entiers hex)
print(maze.map_)     # list[list[int]], shape (height, width)

# Accéder au chemin solution (liste de Cell namedtuples)
print(maze.path)     # list[Cell] | None

# Convertir le chemin en lettres N/E/S/W
print(Maze.path_to_moves(maze.path))  # ex: "EESSSWNN..."

# Représentation hexadécimale (une ligne par rangée)
print(str(maze))

# Re-générer avec le même objet (nouvelle graine aléatoire)
maze.gen()
```

#### Paramètres avancés

```python
# Passer une graine directement dans le fichier de config
# SEED=42 → reproductibilité garantie

# Ne pas générer automatiquement à l'initialisation
maze = Maze(cfg, gen_on_init=False)
maze.gen()  # appel manuel
```

#### Types exportés

```python
from mazegen import Cell, DIRECTION, map_type

cell = Cell(x=3, y=5)        # namedtuple avec attributs x, y
cell.x                        # 3
cell.y                        # 5

DIRECTION.NORTH.value         # 0x1
DIRECTION.EAST.value          # 0x2
DIRECTION.SOUTH.value         # 0x4
DIRECTION.OUEST.value         # 0x8
```

#### Vérifier si un déplacement est possible

```python
# Depuis la cellule (x=2, y=3), peut-on aller à l'Est ?
maze.can_move(2, 3, "E")  # bool
```

### Construire le package depuis les sources

```bash
python -m venv .venv
source .venv/bin/activate
pip install poetry build
poetry build
# → dist/mazegen-0.1.0-py3-none-any.whl
```

> Le module `mazegen` expose la structure interne (`map_`) sous forme de `list[list[int]]`, qui **n'est pas identique** au format du fichier de sortie hexadécimal (qui est une chaîne de texte). La conversion est effectuée par `__str__` et `generate_output`.

---

## 👥 Team & Project Management

### Répartition des rôles

| Membre | Contributions |
|---|---|
| **nilinott** | Parsing (`conf.py`), solver BFS, point d'entrée `a_maze_ing.py`, correction de bugs / norme, rédaction du README |
| **jbenhass** | Makefile, affichage TUI (`tui_render.py`), génération DFS (`maze.py`), point d'entrée, correction de bugs |

### Planning prévu vs réel

| Phase | Prévu | Réel |
|---|---|---|
| Parsing config | 1 jour | 1 jour |
| Génération DFS | 1 jour | 1–2 jours (ajout du motif 42) |
| Solver BFS | 1 jour | 1 jour |
| Affichage TUI | 1 jour | 1–2 jours (gestion scroll, cache, palette) |
| Norme / debug | 1 jour | continu |

### Ce qui a bien fonctionné
- Bonne séparation des responsabilités (génération ↔ rendu)
- Modularité : `mazegen` facilement testable indépendamment du TUI
- Communication régulière et revue de code croisée

### Améliorations possibles
- Implémenter d'autres algorithmes (Kruskal, Prim, Wilson)
- Ajouter une animation de génération pas-à-pas dans la TUI

### Outils utilisés

| Outil | Usage |
|---|---|
| Git / GitHub | Gestion de version, branches par feature |
| VS Code | Développement principal |
| mypy | Vérification statique du typage |
| flake8 | Conformité PEP 8 |
| poetry | Gestion des dépendances et build du package |

---

## 📚 Resources

### Algorithmes et théorie

- [Maze generation algorithms — Wikipedia](https://en.wikipedia.org/wiki/Maze_generation_algorithm)
- [Recursive backtracker / DFS maze — tinyurl](https://en.wikipedia.org/wiki/Maze_generation_algorithm#Randomized_depth-first_search)
- [Breadth-First Search — Wikipedia](https://en.wikipedia.org/wiki/Breadth-first_search)
- [Spanning trees and perfect mazes](https://en.wikipedia.org/wiki/Spanning_tree)
- [Jamis Buck — Maze algorithms illustrated](https://weblog.jamisbuck.org/2011/2/7/maze-generation-algorithm-recap)

### Documentation technique

- [Rich — Python terminal formatting](https://rich.readthedocs.io/)
- [readchar — keyboard input](https://github.com/magmax/python-readchar)
- [Python `typing` module](https://docs.python.org/3/library/typing.html)
- [PEP 257 — Docstring conventions](https://peps.python.org/pep-0257/)
- [poetry — Python packaging](https://python-poetry.org/docs/)

### 🤖 Utilisation de l'IA

L'IA (Claude / ChatGPT) a été utilisée de manière ciblée et critique :

| Tâche | Usage |
|---|---|
| Clarification du BFS et reconstruction de chemin | Obtenir des explications sur la logique de backtrack dans BFS |
| Structure du package `pyproject.toml` | Vérifier la syntaxe poetry pour un package mono-fichier |
| Debug du rendu Rich | Identifier pourquoi `Live` coupait l'affichage sur certains terminaux |
| Rédaction du README | Structurer et compléter la documentation (relue et corrigée manuellement) |
