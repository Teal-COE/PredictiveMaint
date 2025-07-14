import numpy as np
import matplotlib.pyplot as plt

# Parameters
num_points = 1001  # Number of points from 0 to 100
x = np.linspace(0, 1000, num_points)
wavelength_factor = 0.1  # Factor to increase the wavelength
y = np.sin(wavelength_factor * x)

# Plot
plt.figure(figsize=(10, 5))
plt.plot(x, y, label='Sine Wave with Increased Wavelength')
plt.xlabel('x')
plt.ylabel('y')
plt.title('Sine Wave with Increased Wavelength')
plt.legend()
plt.grid(True)
plt.show()

# Print x and y values
for i in range(num_points):
    print(f'x = {x[i]:.2f}, y = {y[i]:.2f}')
