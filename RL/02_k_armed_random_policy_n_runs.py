# This template for a k-armed bandit experiment using a random policy for multiple independent runs.

import numpy as np
import matplotlib.pyplot as plt

####### experiment parameters
k = 10  # Number of arms
num_runs = 2000 # Number of independent runs to average results
num_steps = 1000  # Number of trials allowed to the agent. It thus defines the number of steps and the length of the episode.
experiment_seed = 42 # Set random seed for reproducibility

# environment setup
np.random.seed(experiment_seed)

print(f"k-armed bandits experiment for k = {k} and {num_runs} runs of {num_steps} steps each and seed = {experiment_seed}")

def select_arm_policy(q):
    if np.random.random() < 0.1:
        return np.random.randint(k)
    else:
        return np.argmax(q)

# run a single episode of num_steps steps
def run_xp():
    true_rewards = np.random.normal(0, 1, k)  # True reward means -> q*(a)
    optimal_arm = np.argmax(true_rewards)
    rewards = []  
    optimal_choices = np.zeros(num_steps)

    q = np.zeros(k)
    n = np.zeros(k)

    for t in range(1, num_steps + 1):

        selected_arm = select_arm_policy(q)

        reward = np.random.normal(true_rewards[selected_arm], 1)

        rewards.append(reward)
        optimal_choices[t-1] = 1 if selected_arm == optimal_arm else 0

        n[selected_arm] += 1
        q[selected_arm] += (reward - q[selected_arm]) / n[selected_arm]

    return rewards, optimal_choices

# experiment runs outputs data
all_rewards = np.zeros((num_runs, num_steps))
all_optimal = np.zeros((num_runs, num_steps))

# Run multiple episodes and store results
for run in range(num_runs):
    rewards, optimal = run_xp()
    all_rewards[run] = rewards
    all_optimal[run] = optimal
    
print("\nExperiment completed for all runs.")

# === PLOT RESULTS ===
time_stamps = np.arange(1, num_steps + 1)
average_of_all_rewards_over_time = np.mean(all_rewards, axis=0)
optimal_pct = np.mean(all_optimal, axis=0) * 100

fig, ax1 = plt.subplots(figsize=(10, 6))
plt.xlim(0, num_steps+1)

color1 = 'tab:blue'
ax1.set_xlabel('Steps')
ax1.set_ylabel('Average Reward', color=color1)
plt.plot(time_stamps, np.cumsum(average_of_all_rewards_over_time) / time_stamps, label='Average Reward')
ax1.tick_params(axis='y', labelcolor=color1)

ax2 = ax1.twinx()
color2 = 'tab:red'
ax2.set_ylabel('% Optimal Action', color=color2)
ax2.plot(time_stamps,optimal_pct, color=color2, label='% Optimal Action')
ax2.tick_params(axis='y', labelcolor=color2)
ax2.set_ylim(0, 100)

fig.tight_layout()
plt.title(f'Random choice policy on {k}-armed Bandit for {num_steps} steps\n averaged over {num_runs} runs with initial seed {experiment_seed}')
fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))
plt.grid(True, alpha=0.3)
plt.show()