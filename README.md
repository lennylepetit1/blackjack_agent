# blackjack_agent
L'objectif est de créer un bot qui comprend parfaitement la meilleure stratégie a adopter pour jouer de la meilleure façon possible au blackjack.

La partie env_blackjack sert à expliciter les règles du jeu à l'ordinateur. Ensuite, train_qlearning sert à entrainer notre bot afin qu'il trouve la meilleure stratégieà adopter. La partie bot_policy sert à stocker la stratégie optimale que le bot va adopter en situation réelle (et non en entranement). Enfin, blackjack_gui donne une interface graphique qui permet à l'utilisateur soit de jouer au blackjack lui même, soit de faire jouer le bot à sa place. La stratégie du Bot est résumé par la carte de stratégie disponible sur l'interface blackjack_gui (bouton carte de stratégie).

Le rendement moyen du bot est de -5% (logique puisque le casino gagne toujours). Il est à noter que la carte de stratégie peut légèrement varier d'une simulation à une autre, cela dépend des cas explorés même si une large majorité des cas seront cohérent avec le choix optimal.
