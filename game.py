import random
import tkinter as tk
from tkinter import messagebox

# ===== Modèle (logique du jeu) =====
VALEURS_CARTES = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
    "V": 10, "D": 10, "R": 10, "A": 11
}
NOMS_CARTES = list(VALEURS_CARTES.keys())
COULEURS = ["Pique", "Carreau", "Trèfle", "Cœur"]

def creer_paquet():
    return [(val, coul) for val in NOMS_CARTES for coul in COULEURS]

def valeur_main(main):
    total = 0
    as_count = 0
    for (val, _) in main:
        total += VALEURS_CARTES[val]
        if val == "A":
            as_count += 1
    # Ajuste les As de 11 -> 1 si on dépasse 21
    while total > 21 and as_count:
        total -= 10
        as_count -= 1
    return total

def carte_str(c):
    return f"{c[0]} {c[1]}"

# ===== Vue-Contrôleur (Tkinter) =====
class BlackjackGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Blackjack - Tkinter")

        # État du jeu
        self.paquet = []
        self.main_joueur = []
        self.main_croupier = []
        self.manche_terminee = False

        # ---- Layout ----
        titre = tk.Label(root, text="Blackjack", font=("Arial", 18, "bold"))
        titre.pack(pady=6)

        # Croupier
        self.frame_croupier = tk.LabelFrame(root, text="Croupier", padx=10, pady=10)
        self.frame_croupier.pack(fill="x", padx=10, pady=5)
        self.lbl_croupier_cartes = tk.Label(self.frame_croupier, text="", font=("Consolas", 12))
        self.lbl_croupier_cartes.pack(anchor="w")
        self.lbl_croupier_total = tk.Label(self.frame_croupier, text="", font=("Arial", 12))
        self.lbl_croupier_total.pack(anchor="w")

        # Joueur
        self.frame_joueur = tk.LabelFrame(root, text="Joueur", padx=10, pady=10)
        self.frame_joueur.pack(fill="x", padx=10, pady=5)
        self.lbl_joueur_cartes = tk.Label(self.frame_joueur, text="", font=("Consolas", 12))
        self.lbl_joueur_cartes.pack(anchor="w")
        self.lbl_joueur_total = tk.Label(self.frame_joueur, text="", font=("Arial", 12))
        self.lbl_joueur_total.pack(anchor="w")

        # Message
        self.lbl_msg = tk.Label(root, text="", font=("Arial", 12))
        self.lbl_msg.pack(pady=5)

        # Boutons
        btns = tk.Frame(root)
        btns.pack(pady=8)

        self.btn_tirer = tk.Button(btns, text="Tirer", width=12, command=self.action_tirer)
        self.btn_rester = tk.Button(btns, text="Rester", width=12, command=self.action_rester)
        self.btn_nouvelle = tk.Button(btns, text="Nouvelle main", width=12, command=self.nouvelle_main)
        self.btn_quitter = tk.Button(btns, text="Quitter", width=12, command=root.destroy)

        self.btn_tirer.grid(row=0, column=0, padx=5)
        self.btn_rester.grid(row=0, column=1, padx=5)
        self.btn_nouvelle.grid(row=0, column=2, padx=5)
        self.btn_quitter.grid(row=0, column=3, padx=5)

        # Première main
        self.nouvelle_main()

    # ----- Helpers d’affichage -----
    def afficher_mains(self, cacher_croupier=False):
    # Croupier
        if cacher_croupier and not self.manche_terminee and len(self.main_croupier) >= 2:
            visibles = ["[Carte cachée]"] + [carte_str(c) for c in self.main_croupier[1:]]
        # Calculer la valeur de la ou des cartes visibles
            total_visible = valeur_main(self.main_croupier[1:])
            self.lbl_croupier_cartes.config(text=", ".join(visibles))
            self.lbl_croupier_total.config(text=f"Total visible = {total_visible}")
        else:
            self.lbl_croupier_cartes.config(text=", ".join(carte_str(c) for c in self.main_croupier))
            self.lbl_croupier_total.config(text=f"Total = {valeur_main(self.main_croupier)}")

        # Joueur
        self.lbl_joueur_cartes.config(text=", ".join(carte_str(c) for c in self.main_joueur))
        self.lbl_joueur_total.config(text=f"Total = {valeur_main(self.main_joueur)}")


    def set_message(self, txt):
        self.lbl_msg.config(text=txt)

    def activer_boutons_jeu(self, actif: bool):
        self.btn_tirer.config(state=("normal" if actif else "disabled"))
        self.btn_rester.config(state=("normal" if actif else "disabled"))

    # ----- Flux de manche -----
    def construire_paquet_si_besoin(self):
        # Recrée et mélange si le paquet devient trop court
        if len(self.paquet) < 15:
            self.paquet = creer_paquet()
            random.shuffle(self.paquet)

    def tirer_carte(self, main):
        if not self.paquet:
            self.construire_paquet_si_besoin()
        main.append(self.paquet.pop())

    def distribuer_initial(self):
        self.main_joueur = []
        self.main_croupier = []
        for _ in range(2):
            self.tirer_carte(self.main_joueur)
            self.tirer_carte(self.main_croupier)

    def nouvelle_main(self):
        self.manche_terminee = False
        self.construire_paquet_si_besoin()
        self.distribuer_initial()
        self.afficher_mains(cacher_croupier=True)
        self.set_message("À toi de jouer : Tirer ou Rester ?")
        self.activer_boutons_jeu(True)

    # ----- Actions -----
    def action_tirer(self):
        if self.manche_terminee:
            return
        self.tirer_carte(self.main_joueur)
        self.afficher_mains(cacher_croupier=True)
        total = valeur_main(self.main_joueur)
        if total > 21:
            self.set_message("Tu dépasses 21 ! Manche perdue.")
            self.fin_de_manche()

    def action_rester(self):
        if self.manche_terminee:
            return
        # Tour du croupier
        self.activer_boutons_jeu(False)
        self.afficher_mains(cacher_croupier=False)
        self.root.update_idletasks()

        while valeur_main(self.main_croupier) < 17:
            self.tirer_carte(self.main_croupier)
            self.afficher_mains(cacher_croupier=False)
            self.root.update_idletasks()

        self.evaluer_resultat()

    def evaluer_resultat(self):
        total_j = valeur_main(self.main_joueur)
        total_c = valeur_main(self.main_croupier)

        if total_c > 21:
            msg = "Le croupier dépasse 21, tu gagnes !"
        elif total_j > total_c:
            msg = " Tu gagnes !"
        elif total_j < total_c:
            msg = "Le croupier gagne."
        else:
            msg = "Égalité."
        self.set_message(msg)
        self.fin_de_manche()

    def fin_de_manche(self):
        self.manche_terminee = True
        # Révèle la main du croupier
        self.afficher_mains(cacher_croupier=False)
        # Désactive Tirer/Rester, laisse "Nouvelle main" pour enchaîner
        self.activer_boutons_jeu(False)

# ----- Lancement -----
if __name__ == "__main__":
    root = tk.Tk()
    app = BlackjackGUI(root)
    root.mainloop()
