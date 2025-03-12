import pygame
import sys
import time
import numpy as np

pygame.init()

WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Test Gizmo")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
Green_trans = (159, 255, 159)

LINE_X = WIDTH // 2
BALL_RADIUS = 10
TARGET_HEIGHT = 200
TARGET_SIZE = 100
GRAVITY = 0.4
JUMP_SPEED = -5

class Ball:
    def __init__(self):
        self.x = LINE_X
        self.y = HEIGHT - BALL_RADIUS
        self.velocity = 0
    
    def jump(self):
        self.velocity = JUMP_SPEED
    
    def update(self):
        self.velocity += GRAVITY
        self.y += self.velocity


        if self.y > HEIGHT - BALL_RADIUS:
            self.y = HEIGHT - BALL_RADIUS
            self.velocity = 0
    
    def draw(self, screen):
        pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), BALL_RADIUS)

def main():
    # 确保每次运行时重新初始化pygame
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Test Gizmo")
    
    clock = pygame.time.Clock()
    ball = Ball()
    
    target_center = HEIGHT - TARGET_HEIGHT
    target_top = target_center - TARGET_SIZE // 2
    target_bottom = target_center + TARGET_SIZE // 2
    
    running = True
    last_sample_time = time.time()
    
    while running:
        current_time = time.time()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    ball.jump()

        ball.update()

        if current_time - last_sample_time >= 0.05:
            distance = abs(ball.y - target_center)
            if hasattr(main, 'distance_queue'):
                main.distance_queue.put(distance)
            last_sample_time = current_time

        screen.fill(WHITE)

        pygame.draw.line(screen, BLACK, (LINE_X, 0), (LINE_X, HEIGHT), 2)

        pygame.draw.line(screen, GREEN, 
                        (LINE_X - 20, target_top), 
                        (LINE_X + 20, target_top), 4)
        pygame.draw.line(screen, GREEN, 
                        (LINE_X - 20, target_bottom), 
                        (LINE_X + 20, target_bottom), 4)
        pygame.draw.rect(screen, Green_trans, (LINE_X - 20, target_top+4, 40, TARGET_SIZE-4))
        pygame.draw.line(screen, BLACK,
                         (LINE_X - 30, (target_top+target_bottom)/2),
                         (LINE_X + 30, (target_top+target_bottom)/2), 1)

        ball.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.display.quit()
    pygame.quit()

if __name__ == "__main__":
    main()