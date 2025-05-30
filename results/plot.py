import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np

tracking_op_para = [
    (7.36, 0.933),
    (2.69, 0.980),
    (7.34, 0.96),
    (9.6, 0.976)
]

aiming_op_para = [
    (4.55, 0.998),
    (6.6, 0.990),
    (7.4, 0.999),
    (6.8, 0.989)
]

aiming_op_para2 = [
    (4.52, 0.951),
    (4.33, 0.960),
    (5.23, 0.946),
    (6.32, 0.943)
]

tracking_op_para2 = [
    (6.23, 0.940),
    (5.44, 0.938),
    (7.34, 0.933)
]

tracking_x = [x for x, y in tracking_op_para]
tracking_y = [y for x, y in tracking_op_para]

aiming_x = [x for x, y in aiming_op_para]
aiming_y = [y for x, y in aiming_op_para]

tracking_x2 = [x for x, y in tracking_op_para2]
tracking_y2 = [y for x, y in tracking_op_para2]

aiming_x2 = [x for x, y in aiming_op_para2]
aiming_y2 = [y for x, y in aiming_op_para2]

plt.figure(figsize=(10, 6))

plt.scatter(tracking_x, tracking_y, color='red', label='Tracking')
plt.scatter(aiming_x, aiming_y, color='blue', label='Aiming')
plt.scatter(tracking_x2, tracking_y2, color='green', label='Tracking 2')
plt.scatter(aiming_x2, aiming_y2, color='orange', label='Aiming 2')

plt.xlim(0, 10)
plt.ylim(0.9, 1.0)

plt.xlabel('Speed Factor')
plt.ylabel('Damping Factor')
plt.title('Parameter Distribution for Tracking and Aiming Tasks')

plt.legend()

plt.grid(True, linestyle='--', alpha=0.7)

plt.show()