"""
switch_ui.py

NOTE: Not used in the main process

Provides a fullscreen graphical prompt using pygame to instruct the user to physically switch joystick parameters
(keycap type, rocker length, cap size) before continuing an experiment.

This script:
- Displays the required physical parameters and waits for the user to confirm the change by pressing the Y button on a connected game controller.
- Uses pygame for rendering the interface and handling joystick input.
- Can be run directly to test the prompt with sample parameter sets.

Modules used:
- pygame: For graphical display and joystick input.
- time: For timing control.

Run this script directly to test the switch prompt interface.
"""

import pygame
import time

def show_switch_prompt(keycap_type, rocker_length, cap_size):

    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    width, height = screen.get_size()

    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    BLUE = (0, 0, 255)

    title_font = pygame.font.Font(None, 64)
    param_font = pygame.font.Font(None, 48)
    hint_font = pygame.font.Font(None, 36)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return False

        # Check for Y button press
        joystick = pygame.joystick.Joystick(0)
        if joystick.get_button(3):  # Y button
            pygame.quit()
            return True

        # Draw interface
        screen.fill(WHITE)

        # Title
        title = title_font.render("Please Switch Physical Parameters", True, BLACK)
        screen.blit(title, (width//2 - title.get_width()//2, height//6))

        # Parameters
        params = [
            f"Keycap Type: {keycap_type}",
            f"Rocker Length: {rocker_length:.2f}mm",
            f"Cap Size: {cap_size:.2f}mm"
        ]

        for i, param in enumerate(params):
            text = param_font.render(param, True, BLUE)
            screen.blit(text, (width//2 - text.get_width()//2, height//2 + i*60))

        # Hint
        hint = hint_font.render("Press Y to continue after switching", True, BLACK)
        screen.blit(hint, (width//2 - hint.get_width()//2, height*3//4))

        pygame.display.flip()
        time.sleep(0.016)

    return False

if __name__ == "__main__":
    pygame.init()
    pygame.joystick.init()
    
    if pygame.joystick.get_count() == 0:
        print("Error: No game controller detected!")
        pygame.quit()
        exit()
    
    test_params = [
        (0, 25.0, 30.0),
        (2, 40.0, 45.0),
        (4, 15.0, 20.0)
    ]
    
    for keycap_type, rocker_length, cap_size in test_params:
        print(f"\nTesting with parameters:")
        print(f"Cap Type: {keycap_type}")
        print(f"Rocker Length: {rocker_length:.2f}mm")
        print(f"Cap Size: {cap_size:.2f}mm")
        
        result = show_switch_prompt(keycap_type, rocker_length, cap_size)
        print(f"User confirmed: {result}")
        
        time.sleep(1)
