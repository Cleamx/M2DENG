# Compare greedy and epsilon-greedy (eps=0.1 and eps=0.01) on the k-armed bandit.
# This script runs the three policies using the same true rewards per run (fair comparison),
# plots cumulative average reward and % optimal action for each policy on the same figure,
# and saves the figure to a PNG file.

import numpy as np
import matplotlib.pyplot as plt

####### experiment parameters
k = 10  # Number of arms
num_runs = 2000  # Number of independent runs to average results
num_steps = 1000  # Number of trials allowed to the agent
experiment_seed = 42  # Set random seed for reproducibility

# environment setup
np.random.seed(experiment_seed)

print(f"k-armed bandits experiment for k = {k} and {num_runs} runs of {num_steps} steps each and seed = {experiment_seed}")

policies = {
    'greedy': 0.0,
    'eps=0.1': 0.1,
    'eps=0.01': 0.01,
}

def select_arm_epsilon_greedy(Q, epsilon):
    if np.random.rand() < epsilon:
        return np.random.randint(len(Q))
    # break ties randomly
    max_q = np.max(Q)
    candidates = np.flatnonzero(Q == max_q)
    return np.random.choice(candidates)

# run a single episode using provided epsilon
def run_xp(epsilon):
    # Initialize
    true_rewards = np.random.normal(0, 1, k)  # True reward means -> q*(a)
    optimal_arm = np.argmax(true_rewards)
    rewards = []  
    # Q = np.zeros(k)
    Q = np.full(k, 5.0)      # Estimated value of each arm
    N = np.zeros(k)      # Number of times each arm pulled
    optimal_choices = np.zeros(num_steps)

    for t in range(1, num_steps + 1):
        selected_arm = select_arm_epsilon_greedy(Q, epsilon)
        reward = np.random.normal(true_rewards[selected_arm], 1)
        rewards.append(reward)

        # Update counts and estimates (sample-average)
        N[selected_arm] += 1
        Q[selected_arm] += (reward - Q[selected_arm]) / N[selected_arm]

        optimal_choices[t - 1] = 1 if selected_arm == optimal_arm else 0

    return rewards, optimal_choices

# storage: for each policy store rewards and optimal choices across runs
all_rewards = {name: np.zeros((num_runs, num_steps)) for name in policies}
all_optimal = {name: np.zeros((num_runs, num_steps)) for name in policies}

# Run experiments. For fairness, for each run we draw one set of true_rewards and use it for all policies.
for run in range(num_runs):

    for name, eps in policies.items():
        rewards, optimal = run_xp(eps)
        all_rewards[name][run] = rewards
        all_optimal[name][run] = optimal

print("\nExperiment completed for all runs.")

# === PLOT RESULTS ===
time_stamps = np.arange(1, num_steps + 1)

fig, ax1 = plt.subplots(figsize=(10, 6))
plt.xlim(0, num_steps + 1)
ax1.set_xlabel('Steps')
ax1.set_ylabel('Average reward (cumulative average)')

colors = {
    'greedy': 'tab:blue',
    'eps=0.1': 'tab:orange',
    'eps=0.01': 'tab:green'
}

# Plot average cumulative reward for each policy on ax1
for name in policies:
    avg_rewards_over_time = np.mean(all_rewards[name], axis=0)
    average_of_all_rewards_over_time = np.cumsum(avg_rewards_over_time) / time_stamps
    ax1.plot(time_stamps, average_of_all_rewards_over_time, label=f'{name} - Avg reward', color=colors[name])

ax2 = ax1.twinx()
ax2.set_ylabel('% Optimal action')
ax2.set_ylim(0, 100)

# Plot % optimal action for each policy on ax2 (dashed lines)
for name in policies:
    optimal_pct = np.mean(all_optimal[name], axis=0) * 100
    ax2.plot(time_stamps, optimal_pct, label=f'{name} - % optimal', color=colors[name], linestyle='--')

# Combine legends from both axes
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
all_lines = lines1 + lines2
all_labels = labels1 + labels2
fig.legend(all_lines, all_labels, loc='upper left', bbox_to_anchor=(0.12, 0.92))

plt.title(f'Greedy and Epsilon-Greedy comparison on {k}-armed Bandit for {num_steps} steps\naveraged over {num_runs} runs (seed {experiment_seed})')
plt.grid(True, alpha=0.3)
plt.tight_layout()

# save figure
#out_file = f'k_armed_epsilon_comparison_k{k}_steps{num_steps}_runs{num_runs}_seed{experiment_seed}.png'
#plt.savefig(out_file, dpi=150)
#print(f"Plot saved to {out_file}")

plt.show()