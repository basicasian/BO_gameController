"""
gesture_showcase.py

NOTE: Not used for now, can be used for future use.

This module displays a fullscreen image of a gesture for user selection or demonstration.
It uses Pygame to render a gesture image (from the 'pic' directory) and waits for the user to press any key to continue.

Key characteristics:
- Fullscreen display: Shows a scaled gesture image centered on the screen.
- Simple interaction: Waits for any key press to proceed.
- Intended for use in experiments or demos where users need to view and select gestures.

Main components:
- show_gesture: Loads and displays the gesture image, handles user input to continue.
- main: Entry point for running the gesture showcase with a specified image index.

Dependencies: pygame, sys, os, time.
"""

import pygame
import sys
import os
import time

def show_gesture(image_index):
    pygame.init()
    pygame.joystick.init()
    
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    width, height = screen.get_size()
    pygame.display.set_caption("Gesture Showcase")

    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GRAY = (128, 128, 128)

    title_font = pygame.font.Font(None, 48)
    hint_font = pygame.font.Font(None, 36)
    
    image_path = os.path.join('pic', f'{image_index}.png')
    try:
        image = pygame.image.load(image_path)
        image_ratio = min(height * 0.6 / image.get_height(), width * 0.6 / image.get_width())
        scaled_size = (int(image.get_width() * image_ratio), int(image.get_height() * image_ratio))
        image = pygame.transform.scale(image, scaled_size)
    except pygame.error as e:
        print(e)
        return

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                waiting = False
            elif event.type == pygame.KEYDOWN:
                waiting = False

        screen.fill(WHITE)

        title = title_font.render("Please choose the gesture below", True, BLACK)
        screen.blit(title, (width // 2 - title.get_width() // 2, height // 8-10))
        
        image_x = width // 2 - image.get_width() // 2
        image_y = height // 2 - image.get_height() // 2
        screen.blit(image, (image_x, image_y))

        hint_text = hint_font.render("Press any key to continue", True, GRAY)
        screen.blit(hint_text, (width // 2 - hint_text.get_width() // 2, height * 5 // 6))
        
        pygame.display.flip()
        time.sleep(0.016)

    pygame.quit()

def main():
    try:
        image_index = 1
        if 1 <= image_index <= 3:
            show_gesture(image_index)
        else:
            print("Error Index")
    except ValueError as e:
        print(e)

if __name__ == "__main__":
    main()