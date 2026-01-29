# Sutton's 5x5 gridworld with special states A and B, uniform random policy
# p. 60, example 3.5
import random

# environment parameters / MDP definition
SIZE = 5
A, A_PRIME, A_REWARD = (0,1), (4,1), 10.0
B, B_PRIME, B_REWARD = (0,3), (2,3), 5.0
ACTIONS = {'U':(-1,0), 'D':(1,0), 'L':(0,-1), 'R':(0,1)}
STATES = [(i,j) for i in range(SIZE) for j in range(SIZE)]

# Build a table mapping states to actions for storing the policy
policy = {s: random.choice(list(ACTIONS.keys())) for s in STATES}  # random initial policy
state_values = {s: 0.0 for s in STATES} # initialize V : state-value function values to zero

def step(state, action):
    if state == A:
        return A_PRIME, A_REWARD
    if state == B:
        return B_PRIME, B_REWARD
    di, dj = ACTIONS[action]
    ni, nj = state[0]+di, state[1]+dj
    if 0<=ni<SIZE and 0<=nj<SIZE:
        return (ni,nj), 0.0
    return state, -1.0

def print_values(state_values):
    for i in range(SIZE):
        print(' '.join(f'{state_values[(i,j)]:6.2f}' for j in range(SIZE)))
    print()

def policy_evaluation(discount=0.9, theta=1e-6):
    while True:
        delta = 0.0
        for s in STATES:
            v_old = state_values[s]
            a = policy[s]
            new_state, reward = step(s, a)
            v = reward + discount * state_values[new_state]
            state_values[s] = v
            delta = max(delta, abs(v_old - v))
        if delta < theta:
            break

def policy_improvement(discount=0.9):
    """ Implement the policy improvement step of policy iteration using the algo given p. 80 
        Hint: The policy is unstable if any state changes its action, i.e, if you change the policy table for any state.
    """
    policy_stable = True
    for s in STATES:
        old_action = policy[s]
        best_action = None
        best_value = -float('inf')
        for a in ACTIONS:
            new_state, reward = step(s, a)
            value = reward + discount * state_values[new_state]
            if value > best_value:
                best_value = value
                best_action = a
        policy[s] = best_action
        if old_action != best_action:
            policy_stable = False
            
    return policy_stable

def policy_iteration(discount=0.9, theta=1e-6):
    iteration = 0
    while True:
        iteration += 1
        policy_evaluation(discount, theta)
        policy_stable = policy_improvement(discount)
        print(f"Iteration {iteration}")
        print("State values:")
        print_values(state_values)
        print("Policy:")
        for i in range(SIZE):
            print(' '.join(policy[(i,j)] for j in range(SIZE)))
        print()
        if policy_stable:
            break
    print('Final state_values:')
    print_values(state_values)
    print('Final policy:')
    for i in range(SIZE):
        print(' '.join(policy[(i,j)] for j in range(SIZE)))
    print()

def main():
    policy_iteration()

if __name__ == "__main__":
    main()