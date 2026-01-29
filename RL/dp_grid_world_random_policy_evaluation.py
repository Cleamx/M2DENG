# Sutton's 5x5 gridworld with special states A and B, uniform random policy
# p. 60, example 3.5

# environment parameters / MDP definition
SIZE = 5
A, A_PRIME, A_REWARD = (0,1), (4,1), 10.0
B, B_PRIME, B_REWARD = (0,3), (2,3), 5.0
ACTIONS = {'U':(-1,0), 'D':(1,0), 'L':(0,-1), 'R':(0,1)}
STATES = [(i,j) for i in range(SIZE) for j in range(SIZE)]
POLICY_PROB = 0.25  # uniform random policy

state_values = {s: 0.0 for s in STATES} # initialize V : state-value function values to zero

def step(state, action):
    if state == A:
        return A_PRIME, A_REWARD
    if state == B:
        return B_PRIME, B_REWARD
    di, dj = ACTIONS[action]
    ni, nj = state[0] + di, state[1] + dj
    if 0 <= ni < SIZE and 0 <= nj < SIZE:
        return (ni, nj), 0.0
    return state, -1.0

def print_values(state_values):
    for i in range(SIZE):
        print(' '.join(f'{state_values[(i,j)]:6.2f}' for j in range(SIZE)))
    print()

def policy_evaluation(discount=0.9, theta=1e-6): # discounting is needed for infinite horizon
    print('Initial state_values:')
    print_values(state_values)
    while True:
        delta = 0.0
        for s in STATES:
            v_old = state_values[s]
            v = 0.0
            for a in ACTIONS:
                new_state, reward = step(s, a)
                v += POLICY_PROB * (reward + discount * state_values[new_state])
            state_values[s] = v # update value for state s in place, asynchronous sweeping
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