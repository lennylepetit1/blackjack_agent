# train_qlearning.py
import math, random, pickle
from collections import defaultdict
from env_blackjack import BlackjackEnv

class QAgent:
    def __init__(self, actions=(0,1), alpha=0.1, gamma=1.0,
                 eps_start=0.25, eps_end=0.05, eps_decay=800_000):
        self.Q = defaultdict(float)
        self.actions = actions
        self.alpha = alpha
        self.gamma = gamma
        self.eps_start = eps_start
        self.eps_end = eps_end
        self.eps_decay = eps_decay
        self.t = 0

    def _epsilon(self):
        return self.eps_end + (self.eps_start - self.eps_end) * math.exp(-self.t / self.eps_decay)

    def act(self, state, explore=True):
        self.t += 1
        if explore and random.random() < self._epsilon():
            return random.choice(self.actions)
        q0 = self.Q[(state,0)]
        q1 = self.Q[(state,1)]
        return 1 if q1 > q0 else 0

    def update(self, s, a, r, s2, done):
        best_next = 0.0 if done else max(self.Q[(s2,a2)] for a2 in self.actions)
        td = r + self.gamma * best_next - self.Q[(s,a)]
        self.Q[(s,a)] += self.alpha * td

def train(episodes=800_000, seed=42, verbose_every=50_000):
    env = BlackjackEnv(seed=seed)
    agent = QAgent()
    total = 0.0
    for ep in range(1, episodes+1):
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
        s = env.reset()
        done = False
        while not done:
            a = agent.act(s, explore=False)
            s, r, done, _ = env.step(a)
            score += r
    print(f"Évaluation: gain moyen sur {games} parties = {score/games:.4f}")

if __name__ == "__main__":
    agent = train(episodes=800_000)
    evaluate(agent, games=50_000)
    with open("policy_q.pkl", "wb") as f:
        pickle.dump(dict(agent.Q), f)
    print("Politique sauvegardée -> policy_q.pkl")
