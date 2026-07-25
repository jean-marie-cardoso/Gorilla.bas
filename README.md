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

Chaque nouvelle ville reçoit une ambiance différente : crépuscule, grand
soleil, nuit éclairée, pluie, neige ou tempête. La météo suit exactement le
vent affiché : sens de la flèche, force et vitesse des particules.
Une lune éclaire le ciel nocturne à la place du soleil.
Les deux gorilles sont immédiatement reconnaissables : maillot bleu numéro 1
et maillot orange numéro 2.
Le gorille touché affiche une mine triste. La banane reste une vraie banane,
sans visage ni bras. La lune nocturne possède son propre petit visage.
La ville reste vivante pendant la visée : fenêtres qui s'allument ou
s'éteignent, silhouettes derrière les vitres et balises d'antenne.
Pendant une revanche, le vainqueur précédent porte une petite couronne.
Les villes alternent entre New York, Paris, Tokyo, bord de mer et Néo-City,
avec leurs propres silhouettes et objets de toit destructibles.
Les impacts laissent un gros cratère, une fumée persistante et des débris.
La banane disparaît dès l'impact. Les gorilles respirent, bougent, clignent des
yeux, rient clairement des ratés et paniquent lors d'un tir proche.
La tempête possède éclairs, éclairage des façades et tonnerre. Le téléphone
vibre au tir et à l'explosion. Le tir gagnant est rejoué au ralenti.

Contrôles :

- souris ou tactile : régler les curseurs, puis toucher `TIRER` ;
- `BOUGER` : une fois par ville, choisir un toit voisin puis tirer ;
- bouton `⛶` : passer en plein écran sur Android, iPad et ordinateur ;
- flèches : angle et puissance ; `Maj` fait un grand pas ;
- `Entrée` ou `Espace` : tirer ;
- `B` : choisir un autre toit ;
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

Le rendu logique garde une hauteur de 400 pixels. Sa largeur suit le format
réel du téléphone : le jeu remplit l'écran sans étirer les gorilles ni le texte.
Sur petit écran vertical, la page demande de passer en paysage.

### Plein écran sur téléphone

Sur Android et iPad, toucher le bouton `⛶` masque directement les barres du
navigateur et tente de verrouiller le jeu en paysage.

Safari iPhone ne permet pas encore le plein écran d'un élément web. Toucher
`⛶` affiche donc la méthode fiable : `Partager` → `Sur l'écran d'accueil`,
puis ouvrir Gorillas depuis son icône. Le manifeste lance alors le jeu comme
une application, sans les barres Safari.

Les encoches, la Dynamic Island, la barre d'accueil et les changements de
taille de Safari sont pris en compte avec les zones sûres du téléphone.

## Publication

Chaque push sur `main` compile le code, lance les tests, reconstruit les
archives, puis publie seulement les fichiers web sur GitHub Pages.
