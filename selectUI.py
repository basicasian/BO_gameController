"""
selectUI.py

This module provides a user interface for selecting preferences between two joystick control parameter trials.
It uses Pygame to display trial information and allows users to select, confirm, or retry trials using a joystick.

Key characteristics:
- Single-criterion selection: Lets the user select which of two trials is better, using a single overall preference.
- UI: The user moves left/right to select a trial and confirms the choice.
- Input: Only supports joystick input.
- Output: Returns the selected trial index as a string ("1" or "2").
- For simple, single-criterion selection.

Main components:
- get_user_preference: Displays two trials and records user selection or trial retry.
- create_mock_trial_history: Generates example trial parameter sets for testing.
- Main block: Initializes Pygame, checks for joystick, and runs a sample preference selection.

Dependencies: pygame, time, task_switcher.
"""

import pygame
import time
from task_switcher import TaskSwitcher, TaskType


def get_user_preference(trial1, trial2, trial_history, task_type=TaskType.AIMING):
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    width, height = screen.get_size()

    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GRAY = (128, 128, 128)
    HIGHLIGHT = (0, 255, 0)

    font = pygame.font.Font(None, 48)
    hint_font = pygame.font.Font(None, 36)
    title_font = pygame.font.Font(None, 64)

    params1 = trial_history[trial1]
    params2 = trial_history[trial2]

    selected = 0

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return "2"

        joystick = pygame.joystick.Joystick(0)
        x_axis = joystick.get_axis(0)

        if x_axis < -0.5:
            selected = 0
        elif x_axis > 0.5:
            selected = 1

        if joystick.get_button(2):
            current_params = trial_history[trial1] if selected == 0 else trial_history[trial2]

            pygame.display.quit()
            pygame.quit()

            switcher = TaskSwitcher()
            params = {
                "duration": 10,
                "sampling_rate": 20,
                "friction": current_params['friction'],
                "speed_factor": current_params['speed_factor'],
            }
            switcher.run_task(task_type, params)

            pygame.init()
            pygame.joystick.init()
            screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            width, height = screen.get_size()

            font = pygame.font.Font(None, 48)
            hint_font = pygame.font.Font(None, 36)
            title_font = pygame.font.Font(None, 64)

            time.sleep(0.5)
            continue

        if joystick.get_button(0):
            pygame.quit()
            return "1" if selected == 0 else "2"
        screen.fill(WHITE)

        title = title_font.render("Which one is better?", True, BLACK)
        screen.blit(title, (width // 2 - title.get_width() // 2, height // 6))

        left_color = HIGHLIGHT if selected == 0 else BLACK
        trial1_text = font.render(f"Trial {trial1}", True, left_color)
        speed1_text = font.render(f"Speed: {params1['speed_factor']:.2f}", True, left_color)
        friction1_text = font.render(f"Friction: {params1['friction']:.3f}", True, left_color)

        x1 = width // 4
        screen.blit(trial1_text, (x1 - trial1_text.get_width() // 2, height // 2))
        screen.blit(speed1_text, (x1 - speed1_text.get_width() // 2, height // 2 + 60))
        screen.blit(friction1_text, (x1 - friction1_text.get_width() // 2, height // 2 + 120))

        right_color = HIGHLIGHT if selected == 1 else BLACK
        trial2_text = font.render(f"Trial {trial2}", True, right_color)
        speed2_text = font.render(f"Speed: {params2['speed_factor']:.2f}", True, right_color)
        friction2_text = font.render(f"Friction: {params2['friction']:.3f}", True, right_color)

        x2 = 3 * width // 4
        screen.blit(trial2_text, (x2 - trial2_text.get_width() // 2, height // 2))
        screen.blit(speed2_text, (x2 - speed2_text.get_width() // 2, height // 2 + 60))
        screen.blit(friction2_text, (x2 - friction2_text.get_width() // 2, height // 2 + 120))

        hint_text = hint_font.render("Use Joysticks to Select, Press A to Confirm, Press X to try", True, GRAY)
        screen.blit(hint_text, (width // 2 - hint_text.get_width() // 2, height * 5 // 6))

        pygame.display.flip()
        time.sleep(0.016)

    return "2"


def create_mock_trial_history():
    return [
        {
            'speed_factor': 5.5,
            'friction': 0.95
        },
        {
            'speed_factor': 7.2,
            'friction': 0.98
        },
        {
            'speed_factor': 3.8,
            'friction': 0.96
        }
    ]


if __name__ == "__main__":
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("No game controller")
        pygame.quit()
        exit()

    mock_history = create_mock_trial_history()

    result = get_user_preference(0, 1, mock_history)
    print(f"Selected: {result}")