# Gorillas

Remake web du jeu QBASIC Gorillas, avec une direction « QBASIC Deluxe ».
Deux gorilles se lancent des bananes en tenant compte de l'angle, de la
puissance, de la gravité, du vent et des immeubles destructibles.

Jouer : <https://jean-marie-cardoso.github.io/Gorilla.bas/>

## Lancer en local

Python 3.12 conseillé.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install pygame==2.6.1
python game/main.py
```

Modes :

- solo contre une IA facile, normale ou difficile ;
- duel local à deux joueurs ;
- entraînement sur cible immobile.

Contrôles :

- souris ou tactile : régler les curseurs, puis toucher `TIRER` ;
- flèches : angle et puissance ; `Maj` fait un grand pas ;
- `Entrée` ou `Espace` : tirer ;
- `R` : remettre la visée à 45° / 180 ;
- `M` : couper ou remettre le son ;
- `F` ou `F11` : plein écran ;
- `Échap` : revenir au menu.

## Tester

```bash
python -m compileall -q game scripts tests
python -m unittest discover -s tests -v
```

## Construire la version web

`game/` est la source. Le script prend seulement les fichiers autorisés et
fabrique les deux formats demandés par le chargeur Pygbag :

```bash
python scripts/build_web_archives.py
python -m http.server 8000
```

Puis ouvrir <http://localhost:8000/>.

Le build est reproductible. Pour fixer une autre date interne :

```bash
SOURCE_DATE_EPOCH=1735689600 python scripts/build_web_archives.py
```

## IA

Le menu propose `facile`, `normal` et `difficile`. La simulation utilise la
même trajectoire que le jeu, avec pas fixe et collision sur tout le segment.

## Structure

- `game/` : source Python, interface et assets ;
- `scripts/build_web_archives.py` : build web reproductible ;
- `tests/` : physique, IA, shell web et archive ;
- `index.html` : chargeur Pygbag pour GitHub Pages.

Le rendu logique reste en 640×400 et conserve toujours son ratio. Sur petit
écran vertical, la page demande de passer en paysage.

## Publication

Chaque push sur `main` compile le code, lance les tests, reconstruit les
archives, puis publie seulement les fichiers web sur GitHub Pages.
