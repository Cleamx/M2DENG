import random

from personne import Personne
from grille import Grille

etat = ["susceptible", "infecte"]

grille = Grille(10, 10)
for i in range(10):
    p = Personne("Nom" + str(i), random.choice((etat)),
                 (random.randint(0, 3), random.randint(0, 3)))
    x, y = p.position
    symbole = 'S' if p.etat == 'susceptible' else 'I'
    grille.placer_personne(x, y, symbole)
grille.afficher()
