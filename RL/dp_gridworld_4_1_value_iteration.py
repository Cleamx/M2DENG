# Sutton's Example 4.1: 4x4 gridworld
# p. 76, 
# Value Iteration Algorithm

# environment parameters / MDP definition
SIZE = 4
ACTIONS = {'U':(-1,0), 'D':(1,0), 'L':(0,-1), 'R':(0,1)}
STATES = [(i,j) for i in range(SIZE) for j in range(SIZE)]
state_values = {s: 0.0 for s in STATES} # initialize V(s) to zero

# Terminal states: top-left and bottom-right
TERMINAL_STATES = [(0,0), (SIZE-1,SIZE-1)]

def step(state, action):
    if state in TERMINAL_STATES:
        return state, 0.0
    di, dj = ACTIONS[action]
    ni, nj = state[0]+di, state[1]+dj
    if 0<=ni<SIZE and 0<=nj<SIZE:
        return (ni,nj), -1.0
    return state, -1.0

def print_values(state_values):
    for i in range(SIZE):
        print(' '.join(f'{state_values[(i,j)]:6.2f}' for j in range(SIZE)))
    print()

def value_iteration(discount=1.0, theta=1e-6): # no discounting for episodic tasks
    print('Initial state_values:')
    print_values(state_values)
    iteration = 0
    while True:
        iteration += 1
        print(f"Iteration {iteration}")
        delta = 0.0
        for s in STATES:
            v_old = state_values[s]
            action_outcomes = []
            for a in ACTIONS:
                next_state, reward = step(s, a)
                action_outcomes.append(reward + discount * state_values[next_state])
            state_values[s] = max(action_outcomes)
            delta = max(delta, abs(v_old - state_values[s]))
        print_values(state_values)
        if delta < theta:
            break
    print('Final state_values:')
    print_values(state_values)

def compute_optimal_policy():
    optimal_policy = {}
    for s in STATES:
        if s in TERMINAL_STATES:
            optimal_policy[s] = None
        else:
            action_returns = {}
            for a in ACTIONS:
                new_state, reward = step(s, a)
                action_returns[a] = reward + state_values[new_state]
            best_action = max(action_returns, key=action_returns.get)
            optimal_policy[s] = best_action
    return optimal_policy

def print_policy(policy):
    for i in range(SIZE):
        row = []
        for j in range(SIZE):
            a_probs = policy[(i,j)]
            if a_probs is None:
                row.append('.')
            else:
                row.append('/'.join(policy[(i,j)]))
        print(' '.join(row))
    print()

def main():
    value_iteration()
    print("Computed Optimal Policy:")
    optimal_policy = compute_optimal_policy()
    print_policy(optimal_policy)
    

if __name__ == "__main__":
    main()