import numpy as np
import matplotlib.pyplot as plt

k = 10  # Number of arms
num_steps = 1000  # Number of trials allowed to the agent. It thus defines the number of steps and the length of the episode.
experiment_seed = 44 # Set random seed for reproducibility

# experiment setup
np.random.seed(experiment_seed)

# environment setup
true_rewards = np.random.normal(loc=0, scale=1, size=k)  # True reward means -> q*(a)
optimal_arm = np.argmax(true_rewards)

print("k-armed bandits experiment for k =", k)
print("\nEnvironment model setup for seed", experiment_seed)
print("True values of each arm:", true_rewards)
print("Best arm is arm number:", optimal_arm)

# experiment outputs
rewards = []  # Store rewards over time for analysis

def select_arm_policy():
    # The policy used to select an arm
    # For example, a random selection:
    return np.random.randint(k)

for t in range(1, num_steps + 1):

    # Select an arm based on the policy
    selected_arm = select_arm_policy()

    # Get reward (with noise)
    reward = np.random.normal(true_rewards[selected_arm], 1)

    # Store data for analysis
    rewards.append(reward)

print("\nEnd of the experiment:")
print("Cumulative reward over all steps:", sum(rewards))

# Plotting can be added here to visualize results after implementing the algorithm.
# plotting starting at step = 1
time_stamps = np.arange(1, num_steps + 1)
plt.xlabel('Step')
plt.ylabel('Cumulative Reward')
plt.xlim(0, num_steps+1)
plt.plot(time_stamps, np.cumsum(rewards), label='Cumulative Reward')

plt.title(f'Cumulative Reward over time for \nRandom choice policy on {k}-armed Bandit for {num_steps} steps with seed {experiment_seed}')
plt.legend()
plt.grid(True)
plt.show()