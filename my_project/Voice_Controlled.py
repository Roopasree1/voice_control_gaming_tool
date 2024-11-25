import pygame
import speech_recognition as sr
import random
import sys
import threading
from queue import Queue
import time

# Initialize pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Voice Controlled Snake Game')

# Colors
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

# Snake settings
SNAKE_SIZE = 20
SNAKE_SPEED = 15  # Increased speed

# Clock for controlling FPS
clock = pygame.time.Clock()
font_style = pygame.font.SysFont("bahnschrift", 25)

# Command queue for thread communication
command_queue = Queue()

class VoiceCommandListener(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self, daemon=True)
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 3000  # Adjust sensitivity
        self.recognizer.dynamic_energy_threshold = True
        self.running = True

    def run(self):
        while self.running:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                try:
                    print("Listening...")
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=1)
                    command = self.recognizer.recognize_google(audio).lower()
                    print(f"Command received: {command}")
                    command_queue.put(command)
                except sr.UnknownValueError:
                    pass
                except sr.RequestError:
                    print("Could not request results")
                except sr.WaitTimeoutError:
                    pass

    def stop(self):
        self.running = False

def display_instructions():
    screen.fill(BLACK)
    messages = [
        "Voice Commands:",
        "'Start Game' - Begin the game",
        "'Up/Down/Left/Right' - Control snake",
        "'Quit' - Exit game",
        "",
        "Press ARROW KEYS for keyboard control",
        "Press SPACE to start"
    ]
    for i, message in enumerate(messages):
        text = font_style.render(message, True, WHITE)
        screen.blit(text, [SCREEN_WIDTH // 6, SCREEN_HEIGHT // 4 + i * 40])
    pygame.display.update()

def show_score(score):
    value = font_style.render("Score: " + str(score), True, WHITE)
    screen.blit(value, [10, 10])

def match_command(command):
    command_mapping = {
        'left': ['left'],
        'right': ['right'],
        'up': ['up'],
        'down': ['down'],
        'quit': ['quit', 'exit'],
        'start game': ['start', 'begin', 'play']
    }
    
    for key, values in command_mapping.items():
        if any(val in command for val in values):
            return key
    return None

def snake_game():
    x, y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
    x_change, y_change = 0, 0
    snake_body = [[x, y]]
    snake_length = 1

    food_x = random.randint(0, (SCREEN_WIDTH - SNAKE_SIZE) // SNAKE_SIZE) * SNAKE_SIZE
    food_y = random.randint(0, (SCREEN_HEIGHT - SNAKE_SIZE) // SNAKE_SIZE) * SNAKE_SIZE

    # Start voice command listener thread
    voice_listener = VoiceCommandListener()
    voice_listener.start()

    game_running = True
    while game_running:
        # Handle keyboard events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    x_change, y_change = -SNAKE_SIZE, 0
                elif event.key == pygame.K_RIGHT:
                    x_change, y_change = SNAKE_SIZE, 0
                elif event.key == pygame.K_UP:
                    x_change, y_change = 0, -SNAKE_SIZE
                elif event.key == pygame.K_DOWN:
                    x_change, y_change = 0, SNAKE_SIZE

        # Check voice commands without blocking
        while not command_queue.empty():
            command = command_queue.get()
            matched = match_command(command)
            if matched == "left":
                x_change, y_change = -SNAKE_SIZE, 0
            elif matched == "right":
                x_change, y_change = SNAKE_SIZE, 0
            elif matched == "up":
                x_change, y_change = 0, -SNAKE_SIZE
            elif matched == "down":
                x_change, y_change = 0, SNAKE_SIZE
            elif matched == "quit":
                game_running = False

        # Update snake position
        x += x_change
        y += y_change

        # Check boundaries
        if x < 0 or x >= SCREEN_WIDTH or y < 0 or y >= SCREEN_HEIGHT:
            game_running = False

        # Check self-collision
        if [x, y] in snake_body[:-1]:
            game_running = False

        # Update snake body
        snake_body.append([x, y])
        if len(snake_body) > snake_length:
            del snake_body[0]

        # Check food collision
        if x == food_x and y == food_y:
            food_x = random.randint(0, (SCREEN_WIDTH - SNAKE_SIZE) // SNAKE_SIZE) * SNAKE_SIZE
            food_y = random.randint(0, (SCREEN_HEIGHT - SNAKE_SIZE) // SNAKE_SIZE) * SNAKE_SIZE
            snake_length += 1

        # Draw everything
        screen.fill(BLACK)
        for block in snake_body:
            pygame.draw.rect(screen, GREEN, [block[0], block[1], SNAKE_SIZE, SNAKE_SIZE])
        pygame.draw.rect(screen, RED, [food_x, food_y, SNAKE_SIZE, SNAKE_SIZE])
        show_score(snake_length - 1)
        pygame.display.update()

        clock.tick(SNAKE_SPEED)

    # Clean up
    voice_listener.stop()
    pygame.quit()
    sys.exit()

def main():
    display_instructions()
    waiting_for_start = True
    
    # Start voice listener for menu
    voice_listener = VoiceCommandListener()
    voice_listener.start()
    
    while waiting_for_start:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    waiting_for_start = False
                    snake_game()
        
        # Check voice commands
        while not command_queue.empty():
            command = command_queue.get()
            matched = match_command(command)
            if matched == "start game":
                waiting_for_start = False
                snake_game()
            elif matched == "quit":
                voice_listener.stop()
                pygame.quit()
                sys.exit()
        
        clock.tick(30)

if __name__ == "__main__":
    main()