# bot_policy.py
import pickle
from env_blackjack import valeur_main, valeur_upcard, as_utilisable

class BlackjackQLPolicy:
    def __init__(self, path="policy_q.pkl"):
        with open(path, "rb") as f:
            self.Q = pickle.load(f)  # dict {(state, action): value}

    def act_from_state(self, state):
        # state = (total_joueur, upcard (2..11), as_utilisable (bool))
        q0 = self.Q.get((state,0), 0.0)
        q1 = self.Q.get((state,1), 0.0)
        return 1 if q1 > q0 else 0  # 1=TIRER, 0=RESTER

def gui_state_from_hands(main_joueur, main_croupier):
    """
    Convertit les mains de l'UI Tkinter en état (t_joueur, upcard, as_utilisable).
    Hypothèse : la carte visible du croupier est main_croupier[1] (comme dans ton app).
    """
    t = valeur_main(main_joueur)
    up = valeur_upcard(main_croupier[1])
    soft = as_utilisable(main_joueur)
    return (t, up, soft)
