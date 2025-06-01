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

    selected_row = 0  # 0: Overall, 1: Fatigue, 2: Confidence
    selected_col = 0  # 0: Trial1, 1: Trial2

    preferences = {
        'overall': None,
        'fatigue': None,
        'confidence': None
    }

    has_joystick = pygame.joystick.get_count() > 0
    if has_joystick:
        joystick = pygame.joystick.Joystick(0)
        joystick.init()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return "2", preferences

        if has_joystick:
            x_axis = joystick.get_axis(0)
            y_axis = joystick.get_axis(1)
            try_button = joystick.get_button(2)
            confirm_button = joystick.get_button(0)
        else:
            keys = pygame.key.get_pressed()
            x_axis = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * 0.99
            y_axis = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * 0.99
            try_button = keys[pygame.K_x]
            confirm_button = keys[pygame.K_z]

        if y_axis < -0.5 and selected_row > 0:
            selected_row -= 1
        elif y_axis > 0.5 and selected_row < 2:
            selected_row += 1

        if x_axis < -0.5:
            selected_col = 0
        elif x_axis > 0.5:
            selected_col = 1

        if try_button: 
            current_params = trial_history[trial1] if selected_col == 0 else trial_history[trial2]

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

        if confirm_button:
            if selected_row == 0:
                preferences['overall'] = "1" if selected_col == 0 else "2"
            elif selected_row == 1:
                preferences['fatigue'] = "1" if selected_col == 0 else "2"
            else:
                preferences['confidence'] = "1" if selected_col == 0 else "2"

            if all(v is not None for v in preferences.values()):
                pygame.quit()
                return preferences['overall'], preferences

        screen.fill(WHITE)

        title = title_font.render("Compare and Select", True, BLACK)
        screen.blit(title, (width // 2 - title.get_width() // 2, height // 6))

        row_titles = ["Overall Preference", "Fatigue", "Confidence"]
        row_spacing = 80

        for i, row_title in enumerate(row_titles):
            row_color = HIGHLIGHT if selected_row == i else BLACK
            row_text = font.render(row_title, True, row_color)
            screen.blit(row_text, (width // 4 - row_text.get_width(), height // 2 + i * row_spacing))

            left_color = HIGHLIGHT if selected_row == i and selected_col == 0 else BLACK
            trial1_text = font.render(f"Trial {trial1}", True, left_color)
            screen.blit(trial1_text, (width // 2 - trial1_text.get_width() // 2, height // 2 + i * row_spacing))

            right_color = HIGHLIGHT if selected_row == i and selected_col == 1 else BLACK
            trial2_text = font.render(f"Trial {trial2}", True, right_color)
            screen.blit(trial2_text, (3 * width // 4 - trial2_text.get_width() // 2, height // 2 + i * row_spacing))

            if i == 0 and preferences['overall']:
                choice = "✓" if preferences['overall'] == "1" else "✓"
                choice_text = font.render(choice, True, HIGHLIGHT)
                x_pos = width // 2 - choice_text.get_width() // 2 if preferences['overall'] == "1" else 3 * width // 4 - choice_text.get_width() // 2
                screen.blit(choice_text, (x_pos, height // 2 + i * row_spacing - 30))
            elif i == 1 and preferences['fatigue']:
                choice = "✓" if preferences['fatigue'] == "1" else "✓"
                choice_text = font.render(choice, True, HIGHLIGHT)
                x_pos = width // 2 - choice_text.get_width() // 2 if preferences['fatigue'] == "1" else 3 * width // 4 - choice_text.get_width() // 2
                screen.blit(choice_text, (x_pos, height // 2 + i * row_spacing - 30))
            elif i == 2 and preferences['confidence']:
                choice = "✓" if preferences['confidence'] == "1" else "✓"
                choice_text = font.render(choice, True, HIGHLIGHT)
                x_pos = width // 2 - choice_text.get_width() // 2 if preferences['confidence'] == "1" else 3 * width // 4 - choice_text.get_width() // 2
                screen.blit(choice_text, (x_pos, height // 2 + i * row_spacing - 30))

        params_y = height // 2 + 3 * row_spacing
        speed1_text = font.render(f"Speed: {params1['speed_factor']:.2f}", True, BLACK)
        friction1_text = font.render(f"Friction: {params1['friction']:.3f}", True, BLACK)
        speed2_text = font.render(f"Speed: {params2['speed_factor']:.2f}", True, BLACK)
        friction2_text = font.render(f"Friction: {params2['friction']:.3f}", True, BLACK)

        screen.blit(speed1_text, (width // 2 - speed1_text.get_width() // 2, params_y))
        screen.blit(friction1_text, (width // 2 - friction1_text.get_width() // 2, params_y + 40))
        screen.blit(speed2_text, (3 * width // 4 - speed2_text.get_width() // 2, params_y))
        screen.blit(friction2_text, (3 * width // 4 - friction2_text.get_width() // 2, params_y + 40))

        if has_joystick:
            hint_text = hint_font.render("Use Joysticks to Select Row/Column, Press A to Confirm, Press X to try", True, GRAY)
        else:
            hint_text = hint_font.render("Use Arrow Keys to Select Row/Column, Press Z to Confirm, Press X to try", True, GRAY)
        screen.blit(hint_text, (width // 2 - hint_text.get_width() // 2, height * 5 // 6))

        pygame.display.flip()
        time.sleep(0.016)

    return "2", preferences


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

    mock_history = create_mock_trial_history()

    result, preferences = get_user_preference(0, 1, mock_history)
    print(f"Selected: {result}")
    print(f"All preferences: {preferences}")