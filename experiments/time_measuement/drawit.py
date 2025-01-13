import matplotlib
matplotlib.use('Agg')  # Set backend to avoid GUI issues
import matplotlib.pyplot as plt

# Sample data
number_of_attributes_or_nodes = [10, 20, 30, 40, 50, 60]  # Replace with your data
execution_time = [0.5, 0.8, 1.3, 1.9, 2.5, 3.1]  # Replace with your data

# Create the plot
plt.figure(figsize=(8, 6))  # Set figure size
plt.plot(number_of_attributes_or_nodes, execution_time, marker='o', linestyle='-', color='b', label='Execution Time')

# Add labels, title, and grid
plt.xlabel('Number of Attributes/Nodes', fontsize=12)
plt.ylabel('Execution Time (s)', fontsize=12)
plt.title('Execution Time vs. Number of Attributes/Nodes', fontsize=14)
plt.grid(True, which='both', linestyle='--', linewidth=0.5)
plt.legend(fontsize=10)

# Save the plot
plt.savefig("results/execution_time_plot.png", dpi=300)  # Save as image
print("Plot saved as 'execution_time_plot.png'")
