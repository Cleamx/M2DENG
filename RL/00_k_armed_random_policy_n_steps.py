import numpy as np
import matplotlib.pyplot as plt

k = 10  # Number of arms
num_steps = 50000  # Number of trials allowed to the agent. It thus defines the number of steps and the length of the episode.
experiment_seed = 42 # Set random seed for reproducibility

#experiment setup
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
optimal_choices = np.zeros(num_steps)  # Track optimal choice for each step

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
    optimal_choices[t-1] = 1 if selected_arm == optimal_arm else 0

print("\nEnd of the experiment:")
print("Cumulative reward over all steps:", sum(rewards))
optimal_percentage = sum(optimal_choices) / num_steps * 100
print("Percentage of optimal action selected:", optimal_percentage)
# Plotting can be added here to visualize results after implementing the algorithm.


# plotting starting at step = 1
time_stamps = np.arange(1, num_steps + 1)
average_rewards_over_time = np.cumsum(rewards) / time_stamps
print("rewards:", rewards)
print("average_rewards_over_time:", average_rewards_over_time)

plt.xlabel('Step')
plt.ylabel('Average Reward')
plt.xlim(0, num_steps+1)
plt.plot(time_stamps,average_rewards_over_time, label='Average Reward')

plt.title(f'Random choice policy on {k}-armed Bandit for {num_steps} steps with seed {experiment_seed}, optimal action chosen {optimal_percentage:.2f}% of the time')
plt.legend()
plt.grid(True)
plt.show()