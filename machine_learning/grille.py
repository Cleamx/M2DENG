class Grille:
    def __init__(self, largeur, hauteur):
        self.largeur = largeur
        self.hauteur = hauteur
        self.grille = [['.' for _ in range(largeur)] for _ in range(hauteur)]

    def afficher(self):
        for ligne in self.grille:
            print(' '.join(ligne))

    def placer_personne(self, x, y, symbole):
        if 0 <= x < self.largeur and 0 <= y < self.hauteur:
            self.grille[y][x] = symbole
        else:
            raise ValueError("Coordonnées hors de la grille")
