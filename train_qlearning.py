# train_qlearning.py
import math, random, pickle
from collections import defaultdict
from env_blackjack import BlackjackEnv

# -------- Double Q-Learning agent --------
class DoubleQAgent:
    def __init__(self, actions=(0,1), alpha=0.1, gamma=1.0,
                 eps_start=0.5, eps_end=0.05, eps_decay=800_000):
        self.actions = actions
        self.alpha = alpha
        self.gamma = gamma
        self.eps_start = eps_start
        self.eps_end = eps_end
        self.eps_decay = eps_decay
        self.t = 0

        # deux tables Q indépendantes
        self.Qa = defaultdict(float)
        self.Qb = defaultdict(float)

    # epsilon décroissant (par pas d'action)
    def _epsilon(self):
        return self.eps_end + (self.eps_start - self.eps_end) * math.exp(-self.t / self.eps_decay)

    # valeur Q totale (moyenne) – utilisée pour l'évaluation et la sauvegarde
    def Qmean(self, key):
        return (self.Qa[key] + self.Qb[key]) / 2.0

    # politique ε-greedy sur Qa+Qb (moyenne). Bris d'égalité aléatoire.
    def act(self, state, explore=True):
        self.t += 1
        if explore and random.random() < self._epsilon():
            return random.choice(self.actions)
        q0 = self.Qmean((state,0))
        q1 = self.Qmean((state,1))
        if abs(q1 - q0) < 1e-12:               # égalité → aléatoire
            return random.choice(self.actions)
        return 1 if q1 > q0 else 0

    # mise à jour Double Q (Hasselt 2010)
    def update(self, s, a, r, s2, done):
        # on choisit aléatoirement quelle table mettre à jour
        if random.random() < 0.5:
            # MAJ Qa en s'appuyant sur l'action *greedy* de Qa et la valeur de Qb
            if done:
                target = r
            else:
                # a* = argmax_a Qa(s',a)
                a_star = 0 if self.Qa[(s2,0)] >= self.Qa[(s2,1)] else 1
                target = r + self.gamma * self.Qb[(s2, a_star)]
            self.Qa[(s, a)] += self.alpha * (target - self.Qa[(s, a)])
        else:
            # MAJ Qb en s'appuyant sur l'action *greedy* de Qb et la valeur de Qa
            if done:
                target = r
            else:
                a_star = 0 if self.Qb[(s2,0)] >= self.Qb[(s2,1)] else 1
                target = r + self.gamma * self.Qa[(s2, a_star)]
            self.Qb[(s, a)] += self.alpha * (target - self.Qb[(s, a)])


def train(episodes=800_000, seed=42, verbose_every=50_000):
    env = BlackjackEnv(seed=seed)
    agent = DoubleQAgent(alpha=0.1, gamma=1.0,
                         eps_start=1.0, eps_end=0.05, eps_decay=800_000)

    total = 0.0
    for ep in range(1, episodes+1):
        # IMPORTANT : paquet frais pour chaque main en entraînement
        # (on vide le deck avant reset pour forcer un reshuffle)
        env.deck = []
        s = env.reset()
        done = False

        while not done:
            a = agent.act(s, explore=True)
            s2, r, done, _ = env.step(a)
            agent.update(s, a, r, s2, done)
            s = s2
            total += r

        if verbose_every and ep % verbose_every == 0:
            print(f"[{ep}/{episodes}] Gain moyen: {total/ep:.4f}")
    return agent


def evaluate(agent, games=50_000, seed=123):
    env = BlackjackEnv(seed=seed)
    score = 0.0
    for _ in range(games):
        env.deck = []          # paquet neuf pour chaque partie d'éval
        s = env.reset()
        done = False
        while not done:
            # politique *greedy* sur la moyenne Qa+Qb
            q0 = agent.Qmean((s,0))
            q1 = agent.Qmean((s,1))
            a = 1 if q1 > q0 else (0 if q0 > q1 else random.choice((0,1)))
            s, r, done, _ = env.step(a)
            score += r
    print(f"Évaluation: gain moyen sur {games} parties = {score/games:.4f}")


if __name__ == "__main__":
    agent = train(episodes=800_000)
    evaluate(agent, games=50_000)

    # on sauve la politique moyenne (compatible avec bot_policy.py / GUI)
    Q_mean = {}
    # petite astuce : on ne parcourt que les clés vues dans Qa ∪ Qb
    keys = set(list(agent.Qa.keys()) + list(agent.Qb.keys()))
    for k in keys:
        Q_mean[k] = (agent.Qa[k] + agent.Qb[k]) / 2.0

    with open("policy_q.pkl", "wb") as f:
        pickle.dump(Q_mean, f)
    print("Politique sauvegardée -> policy_q.pkl")
