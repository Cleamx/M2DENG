# Sutton's Example 4.1: 4x4 gridworld, uniform random policy
# p. 66, Example 4.1

# environment parameters / MDP definition
SIZE = 4
ACTIONS = {'U':(-1,0), 'D':(1,0), 'L':(0,-1), 'R':(0,1)}
STATES = [(i,j) for i in range(SIZE) for j in range(SIZE)]
POLICY_PROB = 0.25  # uniform random policy

state_values = {s: 0.0 for s in STATES} # initialize V(s) to zero

# Terminal states: top-left and bottom-right
TERMINAL_STATES = [(0,0), (SIZE-1,SIZE-1)]

def step(state, action):
    if state in TERMINAL_STATES:
        return state, 0.0
    di, dj = ACTIONS[action]
    ni, nj = state[0] + di, state[1] + dj
    if 0 <= ni < SIZE and 0 <= nj < SIZE:
        return (ni,nj), -1.0
    return state, -1.0

def print_values(state_values):
    for i in range(SIZE):
        print(' '.join(f'{state_values[(i,j)]:6.2f}' for j in range(SIZE)))
    print()

def policy_evaluation(discount=1.0, theta=1e-2): # no discounting for episodic tasks
    print('Initial state_values:')
    print_values(state_values)
    iteration = 0
    while True:
        iteration += 1
        print(f"Iteration {iteration}")
        delta = 0.0
        for s in STATES:
            v_old = state_values[s]
            v = 0.0
            for a in ACTIONS:
                new_state, reward = step(s, a)
                v += POLICY_PROB * (reward + discount * state_values[new_state])
            state_values[s] = v
            delta = max(delta, abs(v_old - v))
        print_values(state_values)
        if delta < theta:
            break
    print('Final state_values:')
    print_values(state_values)

def main():
    policy_evaluation()

if __name__ == "__main__":
    main()