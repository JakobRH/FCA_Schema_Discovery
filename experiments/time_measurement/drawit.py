import matplotlib
matplotlib.use('Agg')  # Set backend to avoid GUI issues
import matplotlib.pyplot as plt

# Sample data
number_of_attributes_or_nodes_label = [10,25,50,75,100]  # Replace with your data
execution_time_label = [1.49,20.11,75.63,161.91,272.32]  # Replace with your data
execution_time_prop = [1.47,18.77,84.05,206.96,414.40]  # Replace with your data
execution_time_label_prop = [2.16,52.33,259.92,689.28,1418.93]  # Replace with your data

# Create the plot
plt.figure(figsize=(8, 6))  # Set figure size
plt.plot(number_of_attributes_or_nodes_label, execution_time_label, marker='o', linestyle='-', color='b', label='Label-Based')
plt.plot(number_of_attributes_or_nodes_label, execution_time_prop, marker='o', linestyle='-', color='g', label='Property-Based')
plt.plot(number_of_attributes_or_nodes_label, execution_time_label_prop, marker='o', linestyle='-', color='r', label='Label-Property-Based')

# Add labels, title, and grid
plt.xlabel('Number of Types', fontsize=12)
plt.ylabel('Execution Time (s)', fontsize=12)
plt.grid(True, which='both', linestyle='--', linewidth=0.5)
plt.legend(fontsize=10)

# Save the plot
plt.savefig("results/type_graph.png", dpi=300)  # Save as image

