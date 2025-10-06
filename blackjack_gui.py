# blackjack_gui.py
import random
import tkinter as tk
from tkinter import messagebox

# ---- Import du bot entraîné ----
from bot_policy import BlackjackQLPolicy  # charge policy_q.pkl

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
    while total > 21 and as_count:
        total -= 10
        as_count -= 1
    return total

def as_utilisable(main):
    # True si un As peut compter 11 (main "soft")
    total_1 = 0
    nb_as = 0
    for (v, _) in main:
        if v == "A":
            nb_as += 1
            total_1 += 1   # As compté 1
        else:
            total_1 += VALEURS_CARTES[v]
    return nb_as > 0 and (total_1 + 10) <= 21

def valeur_upcard(carte):
    v = carte[0]
    if v == "A": return 11
    if v in ("V", "D", "R"): return 10
    return int(v)

def carte_str(c):
    return f"{c[0]} {c[1]}"

# ===== Fenêtre Carte de stratégie (lisibilité ++, axes, tooltip) =====
class PolicyWindow(tk.Toplevel):
    def __init__(self, master, policy: BlackjackQLPolicy):
        super().__init__(master)
        self.title("Carte de stratégie du bot (Q-learning)")
        self.policy = policy
        self.cell = 36               # cellules plus grandes
        self.pad = 40                # marge pour axes visibles
        self.font_cell = ("Arial", 12, "bold")
        self.font_axis = ("Arial", 11)
        self.bg = "white"

        header = tk.Label(
            self,
            text=("Grille gauche = main DURE | Grille droite = main SOFT\n"
                  "Colonnes = upcard croupier : 2 3 4 5 6 7 8 9 10 A  |  "
                  "Lignes = total joueur : 4 → 21\n"
                  "Couleur: Rouge = HIT, Vert = RESTER. Cliquer/Survoler une case = Q-valeurs."),
            justify="center"
        )
        header.pack(pady=6)

        wrap = tk.Frame(self)
        wrap.pack(padx=8, pady=8)

        w = self.cell*11 + self.pad*2
        h = self.cell*18 + self.pad*2
        self.canvas_hard = tk.Canvas(wrap, width=w, height=h, bg=self.bg, highlightthickness=1, highlightbackground="#ccc")
        self.canvas_soft = tk.Canvas(wrap, width=w, height=h, bg=self.bg, highlightthickness=1, highlightbackground="#ccc")
        self.canvas_hard.grid(row=0, column=0, padx=10)
        self.canvas_soft.grid(row=0, column=1, padx=10)

        self.info = tk.Label(self, text="Q(RESTER)=..., Q(HIT)=...", font=("Consolas", 11))
        self.info.pack(pady=(4,10))

        self._draw_grid(self.canvas_hard, soft=False, title="HARD (main dure)")
        self._draw_grid(self.canvas_soft, soft=True,  title="SOFT (main soft)")

    def _action_for(self, total, up, soft):
        state = (total, up, bool(soft))
        q0 = self.policy.Q.get((state,0), 0.0)  # RESTER
        q1 = self.policy.Q.get((state,1), 0.0)  # HIT
        action = 1 if q1 > q0 else 0
        return action, q0, q1

    def _draw_axes(self, canvas, title):
        W = int(canvas["width"]); H = int(canvas["height"])
        # Titre
        canvas.create_text(W/2, 16, text=title, font=("Arial", 12, "bold"))
        # Axes
        up_labels = ["2","3","4","5","6","7","8","9","10","A"," "]
        for j, lab in enumerate(up_labels[:-1]):  # 11 colonnes (2..A)
            x = self.pad + j*self.cell + self.cell/2
            canvas.create_text(x, self.pad-14, text=lab, font=self.font_axis)   # haut
            canvas.create_text(x, H-self.pad+14, text=lab, font=self.font_axis) # bas
        for i, tot in enumerate(range(4, 22)):  # 18 lignes (4..21)
            y = self.pad + i*self.cell + self.cell/2
            canvas.create_text(self.pad-18, y, text=str(tot), font=self.font_axis)            # gauche
            canvas.create_text(W-self.pad+18, y, text=str(tot), font=self.font_axis)          # droite

        # cadre et grilles
        canvas.create_rectangle(self.pad, self.pad, W-self.pad, H-self.pad, outline="#888")
        for j in range(1, 11):
            x = self.pad + j*self.cell
            canvas.create_line(x, self.pad, x, H-self.pad, fill="#eee")
        for i in range(1, 18):
            y = self.pad + i*self.cell
            canvas.create_line(self.pad, y, W-self.pad, y, fill="#eee")

        # légende
        canvas.create_rectangle(W-180, 22, W-20, 42, fill="#45a049", outline="#333")
        canvas.create_text(W-205, 32, text="RESTER", anchor="e", font=("Arial",10))
        canvas.create_rectangle(W-180, 46, W-20, 66, fill="#d84a4a", outline="#333")
        canvas.create_text(W-205, 56, text="HIT", anchor="e", font=("Arial",10))

    def _draw_grid(self, canvas, soft: bool, title=""):
        self._draw_axes(canvas, title)
        # cellules
        for i, tot in enumerate(range(4, 22)):
            for j, up in enumerate(range(2, 12)):
                x0 = self.pad + j*self.cell
                y0 = self.pad + i*self.cell
                x1 = x0 + self.cell
                y1 = y0 + self.cell

                action, q0, q1 = self._action_for(tot, up, soft)
                color = "#d84a4a" if action == 1 else "#45a049"   # rouge = HIT, vert = RESTER
                letter = "H" if action == 1 else "S"

                rect = canvas.create_rectangle(x0+1, y0+1, x1-1, y1-1, fill=color, outline="#ddd")
                txt  = canvas.create_text((x0+x1)/2, (y0+y1)/2, text=letter, font=self.font_cell, fill="white")

                # tooltip / click
                def show_info(_evt=None, t=tot, u=up, s=soft):
                    a, q_stay, q_hit = self._action_for(t, u, s)
                    as_text = "SOFT" if s else "HARD"
                    up_txt = "A" if u==11 else str(u)
                    self.info.config(text=f"État: total={t} | upcard={up_txt} | {as_text}   "
                                          f"Q(RESTER)={q_stay:.4f}   Q(HIT)={q_hit:.4f}   "
                                          f"Action={'HIT' if a==1 else 'RESTER'}")
                canvas.tag_bind(rect, "<Enter>", show_info)
                canvas.tag_bind(txt,  "<Enter>", show_info)
                canvas.tag_bind(rect, "<Button-1>", show_info)
                canvas.tag_bind(txt,  "<Button-1>", show_info)

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

        # ---- Bot ----
        self.bot = BlackjackQLPolicy("policy_q.pkl")  # charge la politique apprise
        self.mode_bot = False  # OFF par défaut

        # ---- Stats ----
        self.stats = {"played": 0, "wins": 0, "losses": 0, "pushes": 0, "bot_played": 0, "bot_wins": 0}

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

        # Message + Choix du bot pour l'état courant
        msgrow = tk.Frame(root)
        msgrow.pack(fill="x", padx=10, pady=(0,6))
        self.lbl_msg = tk.Label(msgrow, text="", font=("Arial", 12))
        self.lbl_msg.pack(side="left")
        self.lbl_bot_choice = tk.Label(msgrow, text="", font=("Consolas", 11))
        self.lbl_bot_choice.pack(side="right")

        # Boutons principaux
        btns = tk.Frame(root)
        btns.pack(pady=8)

        self.btn_tirer = tk.Button(btns, text="Tirer", width=12, command=self.action_tirer)
        self.btn_rester = tk.Button(btns, text="Rester", width=12, command=self.action_rester)
        self.btn_nouvelle = tk.Button(btns, text="Nouvelle main", width=12, command=self.nouvelle_main)
        self.btn_bot = tk.Button(btns, text="Bot: OFF", width=12, command=self.toggle_bot)
        self.btn_policy = tk.Button(btns, text="Carte de stratégie", width=16, command=self.open_policy_window)
        self.btn_quitter = tk.Button(btns, text="Quitter", width=12, command=root.destroy)

        self.btn_tirer.grid(row=0, column=0, padx=5)
        self.btn_rester.grid(row=0, column=1, padx=5)
        self.btn_nouvelle.grid(row=0, column=2, padx=5)
        self.btn_bot.grid(row=0, column=3, padx=5)
        self.btn_policy.grid(row=0, column=4, padx=5)
        self.btn_quitter.grid(row=0, column=5, padx=5)

        # ----- Bloc SIMULATION AUTO -----
        auto = tk.LabelFrame(root, text="Simulation automatique (bot)", padx=10, pady=8)
        auto.pack(fill="x", padx=10, pady=(0,8))

        tk.Label(auto, text="Manches à jouer :").grid(row=0, column=0, sticky="w")
        self.entry_auto_n = tk.Entry(auto, width=8)
        self.entry_auto_n.insert(0, "200")
        self.entry_auto_n.grid(row=0, column=1, padx=(4,12))

        tk.Label(auto, text="Délai (ms) entre actions :").grid(row=0, column=2, sticky="w")
        self.entry_auto_delay = tk.Entry(auto, width=8)
        self.entry_auto_delay.insert(0, "30")
        self.entry_auto_delay.grid(row=0, column=3, padx=(4,12))

        self.lbl_auto_status = tk.Label(auto, text="Prêt.", font=("Consolas", 10))
        self.lbl_auto_status.grid(row=0, column=4, padx=(6,12))

        self.btn_auto_start = tk.Button(auto, text="Start", width=10, command=self.auto_start)
        self.btn_auto_stop  = tk.Button(auto, text="Stop",  width=10, command=self.auto_stop, state="disabled")
        self.btn_auto_start.grid(row=0, column=5, padx=4)
        self.btn_auto_stop.grid(row=0, column=6, padx=4)

        # État auto
        self.auto_mode = False
        self.auto_left = 0
        self.auto_delay = 30

        # Stats panel
        statf = tk.LabelFrame(root, text="Performances", padx=10, pady=8)
        statf.pack(fill="x", padx=10, pady=(0,8))
        self.lbl_stats = tk.Label(statf, text="", font=("Consolas", 11))
        self.lbl_stats.pack(anchor="w")
        self.btn_reset_stats = tk.Button(statf, text="Réinitialiser les stats", command=self.reset_stats)
        self.btn_reset_stats.pack(anchor="e", pady=(6,0))

        # Première main
        self.nouvelle_main()

    # ----- Helpers d’affichage -----
    def rafraichir_stats(self):
        p = self.stats
        wr = (p["wins"]/p["played"]*100) if p["played"] else 0.0
        wr_bot = (p["bot_wins"]/p["bot_played"]*100) if p["bot_played"] else 0.0
        self.lbl_stats.config(
            text=(f"Manches: {p['played']}  |  W: {p['wins']}  L: {p['losses']}  D: {p['pushes']}  "
                  f"|  WinRate: {wr:.1f}%   ||   Bot Manches: {p['bot_played']}  Bot W: {p['bot_wins']}  "
                  f"(WinRate: {wr_bot:.1f}%)")
        )

    def afficher_mains(self, cacher_croupier=False):
        # Croupier
        if cacher_croupier and not self.manche_terminee and len(self.main_croupier) >= 2:
            visibles = ["[Carte cachée]"] + [carte_str(c) for c in self.main_croupier[1:]]
            total_visible = valeur_main(self.main_croupier[1:])
            self.lbl_croupier_cartes.config(text=", ".join(visibles))
            self.lbl_croupier_total.config(text=f"Total visible = {total_visible}")
        else:
            self.lbl_croupier_cartes.config(text=", ".join(carte_str(c) for c in self.main_croupier))
            self.lbl_croupier_total.config(text=f"Total = {valeur_main(self.main_croupier)}")

        # Joueur
        self.lbl_joueur_cartes.config(text=", ".join(carte_str(c) for c in self.main_joueur))
        self.lbl_joueur_total.config(text=f"Total = {valeur_main(self.main_joueur)}")

        # Indicateur “Choix du bot” pour l’état courant
        self.update_bot_choice_hint()

    def update_bot_choice_hint(self):
        if self.manche_terminee or len(self.main_croupier) < 2:
            self.lbl_bot_choice.config(text="")
            return
        state = self.etat_pour_bot()
        q0 = self.bot.Q.get((state,0), 0.0)
        q1 = self.bot.Q.get((state,1), 0.0)
        action = "HIT" if q1 > q0 else "RESTER"
        soft = "SOFT" if state[2] else "HARD"
        up = state[1] if state[1] != 11 else "A"
        self.lbl_bot_choice.config(
            text=f"Bot ({soft}) total={state[0]} vs {up} → {action} | Q(S)={q0:.3f} Q(H)={q1:.3f}"
        )

    def set_message(self, txt):
        self.lbl_msg.config(text=txt)

    def activer_boutons_jeu(self, actif: bool):
        self.btn_tirer.config(state=("normal" if actif else "disabled"))
        self.btn_rester.config(state=("normal" if actif else "disabled"))

    # ----- Flux de manche -----
    def construire_paquet_si_besoin(self):
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

        if self.mode_bot:
            self.root.after(max(1, getattr(self, "auto_delay", 600)), self.tour_bot)

    # ----- Bot -----
    def toggle_bot(self):
        self.mode_bot = not self.mode_bot
        self.btn_bot.config(text=f"Bot: {'ON' if self.mode_bot else 'OFF'}")
        if self.mode_bot and not self.manche_terminee:
            self.root.after(max(1, getattr(self, "auto_delay", 300)), self.tour_bot)

    def etat_pour_bot(self):
        total_j = valeur_main(self.main_joueur)
        up = valeur_upcard(self.main_croupier[1])  # carte visible = 2e
        soft = as_utilisable(self.main_joueur)
        return (total_j, up, soft)

    def tour_bot(self):
        if self.manche_terminee or not self.mode_bot:
            return
        if str(self.btn_tirer['state']) == 'disabled':
            return

        state = self.etat_pour_bot()
        action = self.bot.act_from_state(state)  # 1 = Tirer, 0 = Rester

        if action == 1:
            self.action_tirer()
            if not self.manche_terminee and self.mode_bot:
                self.root.after(max(1, getattr(self, "auto_delay", 250)), self.tour_bot)
        else:
            self.action_rester()

    def open_policy_window(self):
        PolicyWindow(self.root, self.bot)

    def reset_stats(self):
        for k in self.stats: self.stats[k] = 0
        self.rafraichir_stats()

    # ===== SIMULATION AUTO (boucle non bloquante via after) =====
    def auto_start(self):
        try:
            n = int(self.entry_auto_n.get())
            d = int(self.entry_auto_delay.get())
            assert n > 0 and d >= 0
        except Exception:
            messagebox.showerror("Entrée invalide", "Veuillez saisir un nombre de manches (>0) et un délai (>=0).")
            return

        self.auto_mode = True
        self.auto_left = n
        self.auto_delay = d
        self.mode_bot = True            # force le bot ON
        self.btn_bot.config(text="Bot: ON")
        self.btn_auto_start.config(state="disabled")
        self.btn_auto_stop.config(state="normal")
        self.lbl_auto_status.config(text=f"Auto… manches restantes: {self.auto_left}")

        if self.manche_terminee:
            self.nouvelle_main()
        self.root.after(max(1, self.auto_delay), self.auto_tick)

    def auto_stop(self):
        self.auto_mode = False
        self.btn_auto_start.config(state="normal")
        self.btn_auto_stop.config(state="disabled")
        self.lbl_auto_status.config(text="Arrêté.")

    def auto_tick(self):
        if not self.auto_mode:
            return

        if self.manche_terminee:
            self.auto_left -= 1
            self.lbl_auto_status.config(text=f"Auto… manches restantes: {self.auto_left}")
            if self.auto_left <= 0:
                self.auto_stop()
                return
            self.nouvelle_main()
            self.root.after(max(1, self.auto_delay), self.auto_tick)
            return

        # Manche en cours : laisser le bot jouer une action
        if str(self.btn_tirer['state']) != 'disabled':
            self.tour_bot()

        self.root.after(max(1, self.auto_delay), self.auto_tick)

    # ----- Actions -----
    def action_tirer(self):
        if self.manche_terminee:
            return
        self.tirer_carte(self.main_joueur)
        self.afficher_mains(cacher_croupier=True)
        total = valeur_main(self.main_joueur)
        if total > 21:
            self.set_message("Tu dépasses 21 ! Manche perdue.")
            self.fin_de_manche(resultat="loss")

    def action_rester(self):
        if self.manche_terminee:
            return
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
            self.set_message("Le croupier dépasse 21, tu gagnes !")
            self.fin_de_manche(resultat="win")
        elif total_j > total_c:
            self.set_message("Tu gagnes !")
            self.fin_de_manche(resultat="win")
        elif total_j < total_c:
            self.set_message("Le croupier gagne.")
            self.fin_de_manche(resultat="loss")
        else:
            self.set_message("Égalité.")
            self.fin_de_manche(resultat="push")

    def fin_de_manche(self, resultat=None):
        self.manche_terminee = True
        self.afficher_mains(cacher_croupier=False)
        self.activer_boutons_jeu(False)

        # maj stats
        self.stats["played"] += 1
        if resultat == "win":
            self.stats["wins"] += 1
            if self.mode_bot: self.stats["bot_wins"] += 1
        elif resultat == "loss":
            self.stats["losses"] += 1
        else:
            self.stats["pushes"] += 1
        if self.mode_bot:
            self.stats["bot_played"] += 1

        self.rafraichir_stats()

# ----- Lancement -----
if __name__ == "__main__":
    root = tk.Tk()
    app = BlackjackGUI(root)
    root.mainloop()
