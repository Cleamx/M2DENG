import random


class Personne:

    def __init__(self, nom, etat, position):
        self.nom = nom
        self.etat = 'susceptible'
        self.position = (0, 0)

    def se_deplacer(self):
        x, y = self.position
        x += random.choice([-1, 0, 1])
        y += random.choice([-1, 0, 1])
        self.position = (x, y)
        return self.position

    def changer_etat(self, nouvel_etat):
        self.etat = nouvel_etat
        return self.etat
