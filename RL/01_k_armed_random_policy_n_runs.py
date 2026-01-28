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

def select_arm_policy():
    return np.random.randint(k)

# run a single episode of num_steps steps
def run_xp():
    # Initialize
    true_rewards = np.random.normal(0, 1, k)  # True reward means -> q*(a)
    rewards = []  

    for t in range(1, num_steps + 1):

        selected_arm = select_arm_policy()

        reward = np.random.normal(true_rewards[selected_arm], 1)

        rewards.append(reward)
        
    return rewards


# experiment runs outputs data
all_rewards = np.zeros((num_runs, num_steps))

# Run multiple episodes and store results
for run in range(num_runs):
    all_rewards[run] = run_xp()

print("\nExperiment completed for all runs.")
average_of_all_rewards_over_time = np.mean(all_rewards, axis=0)

# === PLOT RESULTS ===
time_stamps = np.arange(1, num_steps + 1)
plt.xlabel('Step')
plt.ylabel('Average Reward')
plt.xlim(0, num_steps+1)
plt.plot(time_stamps, np.cumsum(average_of_all_rewards_over_time) / time_stamps, label='Averaged Reward')
plt.title(f'Random choice policy on {k}-armed Bandit for {num_steps} steps\n averaged over {num_runs} runs with initial seed {experiment_seed}')
plt.legend()
plt.grid(True)
plt.show()