# env_blackjack.py
import random

VALEURS_CARTES = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,"10":10,"V":10,"D":10,"R":10,"A":11}
NOMS_CARTES = list(VALEURS_CARTES.keys())
COULEURS = ["Pique","Carreau","Trèfle","Cœur"]

def creer_paquet():
    return [(v,c) for v in NOMS_CARTES for c in COULEURS]

def valeur_main(main):
    total = 0
    as_count = 0
    for (v,_) in main:
        total += VALEURS_CARTES[v]
        if v == "A": as_count += 1
    while total > 21 and as_count:
        total -= 10
        as_count -= 1
    return total

def as_utilisable(main):
    # True si au moins un As peut compter 11 (soft total)
    total_1 = 0; nb_as = 0
    for (v,_) in main:
        if v == "A": nb_as += 1; total_1 += 1
        else: total_1 += VALEURS_CARTES[v]
    return nb_as > 0 and (total_1 + 10) <= 21

def valeur_upcard(carte):  # carte est un tuple (valeur, couleur)
    v = carte[0]
    return 11 if v == "A" else (10 if v in ("V","D","R") else int(v))

class BlackjackEnv:
    """
    Actions: 0=RESTER (stick), 1=TIRER (hit)
    Etat: (total_joueur, upcard_croupier (2..11, 11=As), as_utilisable_joueur (bool))
    Règles alignées avec ton app: 1 paquet, mélange quand besoin, croupier tire <17
    """
    def __init__(self, reshuffle_threshold=15, seed=None):
        self.reshuffle_threshold = reshuffle_threshold
        self.rng = random.Random(seed)
        self.deck = []
        self.joueur = []
        self.croupier = []
        self.termine = False

    def _melanger_si_besoin(self):
        if len(self.deck) < self.reshuffle_threshold:
            self.deck = creer_paquet()
            self.rng.shuffle(self.deck)

    def _tirer(self):
        if not self.deck:
            self._melanger_si_besoin()
        return self.deck.pop()

    def reset(self):
        self.termine = False
        self._melanger_si_besoin()
        self.joueur = [self._tirer(), self._tirer()]
        self.croupier = [self._tirer(), self._tirer()]
        return self._obs()

    def _obs(self):
        return (
            valeur_main(self.joueur),
            valeur_upcard(self.croupier[1]),  # on prend la 2e carte comme "visible" (comme ton UI)
            as_utilisable(self.joueur)
        )

    def step(self, action):
        """
        retourne (obs_suivante, reward, done, info)
        reward: +1 victoire, -1 défaite, 0 égalité.
        """
        if self.termine:
            raise RuntimeError("Episode terminé. reset() d'abord.")
        # HIT
        if action == 1:
            self.joueur.append(self._tirer())
            if valeur_main(self.joueur) > 21:
                self.termine = True
                return self._obs(), -1.0, True, {"resultat":"joueur_bust"}
            return self._obs(), 0.0, False, {}
        # STICK -> croupier joue
        while valeur_main(self.croupier) < 17:
            self.croupier.append(self._tirer())
        tj = valeur_main(self.joueur)
        tc = valeur_main(self.croupier)
        self.termine = True
        if tc > 21 or tj > tc:   return self._obs(), +1.0, True, {"resultat":"joueur_gagne"}
        if tj < tc:              return self._obs(), -1.0, True, {"resultat":"croupier_gagne"}
        return self._obs(), 0.0, True, {"resultat":"egalite"}
