from pygame import init as game_init
from pygame import font
from pygame.display import set_mode, set_caption, update
from pygame.time import Clock
from pygame import quit as pg_quit
from pygame import draw
from pygame import Surface, Rect
from pygame import QUIT, KEYDOWN, event, MOUSEBUTTONDOWN
from pygame import K_a, K_b, K_c, K_d, K_e, K_f, K_g, K_h, K_i, K_j, K_k, K_l, K_m, K_n, K_o, K_p, K_q, K_r, K_s, K_t, \
    K_u, K_v, K_w, K_x, K_y, K_z, K_SPACE
from random import choice
from math import sqrt, sin
from numpy.random import normal as nm
from sqlite3 import connect

# VERSION
VERSION = "1.1.2"

# INITIALIZATION
game_init()
font.init()

# WINDOW
WIN_HEIGHT = 700
WIN_WIDTH = 900
WIN = set_mode((WIN_WIDTH, WIN_HEIGHT))
BG = Surface(WIN.get_size()).convert()
set_caption('Bubbles')

# PROCEDURE CONTROLLER
FPS = 180
FRAME_COUNT = 0
RUN = True
STAGE = 0

# CONSTANTS
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (255, 0, 255)
CYAN = (0, 255, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0) 
BUBBLE_RADIUS_MIN = WIN_WIDTH // 36
BUBBLE_RADIUS_MAX = WIN_WIDTH // 18
BUBBLE_RADIUS_MEAN = BUBBLE_RADIUS_MIN + int((BUBBLE_RADIUS_MAX - BUBBLE_RADIUS_MIN) * 0.4)
BUBBLE_RADIUS_STD = int((BUBBLE_RADIUS_MAX - BUBBLE_RADIUS_MIN) * 0.2)
BUBBLE_RESPAWN_CENTERS = [(WIN_WIDTH * 2 // 9 + BUBBLE_RADIUS_MAX + BUBBLE_RADIUS_MAX * 2 * i, WIN_HEIGHT + BUBBLE_RADIUS_MAX) for i in range(5)]
MAX_LIFE = 10
LIFE_COLOR_BEGIN = (10, 50, 50)
LIFE_COLOR_END = (150, 10, 10)
MAX_MOVE_KEY = FPS


# GAME VARIABLES
BUBBLES = []
KEY = None
SCORE = 0
LIFE = MAX_LIFE
MOVE_KEY = None

# ANIMATION CONTROLLER
ANI_SCORE = 0 
ANI_VIBRATE = 0
ANI_KEY = 0

# CLOCK
CLOCK = Clock()

# COUNTER
CTR_LOSE = 0


def init_leaderboard():
    """initialize leaderboard."""
    answer = input("Warning: This operation will clean up all the records, continue? [y/n]")
    if answer == "Y" or answer == "y":
        con = connect("Bubbles.db")
        print("Database opened successfully.")
        cur = con.cursor()
        cur.execute("UPDATE leaderboard SET score = 0")
        con.commit()
        con.close()
        print("Database closed")
    else:
        print("Mission canceled.")

def create_leaderboard():
    """create a leaderboard"""
    con = connect("Bubbles.db")
    print("Database opened successfully.")
    cur = con.cursor()

    cur.execute("CREATE TABLE leaderboard (rank INTEGER PRIMARY KEY, score INTEGER)")
    leaderboard = [
        (1, 0),
        (2, 0),
        (3, 0),
        (4, 0),
        (5, 0),
        (6, 0),
    ]
    cur.executemany("INSERT INTO leaderboard VALUES (?, ?)", leaderboard)
    con.commit()
    con.close()
    print("Database closed")

def get_data():
    """fetch data.
        Return:
          data: list, first 6 places of leading scores.
    """
    con = connect("Bubbles.db")
    print("Database opened successfully.")
    cur = con.cursor()
    data = []
    try:
        for row in cur.execute("SELECT score FROM leaderboard"):
            data.append(row[0])
    except :
        create_leaderboard()
        for row in cur.execute("SELECT score FROM leaderboard"):
            data.append(row[0])
    con.close()
    print("Database closed")
    return data

def set_data(data):
    """upload data.
        Args:
          data: list, first 6 places of leading scores.
    """
    con = connect("Bubbles.db")
    print("Database opened successfully.")
    cur = con.cursor()
    for i, score in enumerate(data):
        cur.execute("UPDATE leaderboard SET score = ? WHERE rank = ?", (score, i + 1))
    con.commit()
    con.close()
    print("Database closed")

def normal(mean, std, min_, max_):
    """randomly pick a number between min and max(endpoints included) from normal dist. with mean and std.
        Args:
          mean: float.
          std: float.
          min_: float, lower bound.
          max_: float, upper bound.
        Return:
          result: float, random float between min and max.
    """
    result = min(max(nm(mean, std), min_), max_)
    return result

def distance_of_points(point1, point2):
    """measrure the distance of two points.
        Args:
          point1: tuple, (x, y) coordinate of point1.
          point2: tuple, (x, y) coordinate of point2.
        Return:
          distance: float, distance of two points.
    """
    (x1, y1) = point1
    (x2, y2) = point2
    distance = sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
    return distance

def is_circles_collide(circle1, circle2):
    """check if two circles collide.
        Args:
          circle1: tuple, ((x, y), radius) center and radius of circle1.
          circle2: tuple, ((x, y), radius) center and radius of circle2.
        Return:
          result: bool, True if collide or False reversely.
    """
    point1, radius1 = circle1
    point2, radius2 = circle2
    result = False
    if distance_of_points(point1, point2) <= (radius1 + radius2):
        result = True
    return result

def can_respawn(index, bubbles):
    """check if current respawning bit can respawn new bubbles.
        Args:
          index: int, index of respawning bit.
          bubbles: list, list of instances of bubbles.
        Return:
          result: bool, True if non of bubbles intersects the area of respawning bit or False reversely.
    """
    global BUBBLE_RESPAWN_CENTERS, BUBBLE_RADIUS_MAX
    center = BUBBLE_RESPAWN_CENTERS[index]
    radius = BUBBLE_RADIUS_MAX
    respawning_area = (center, radius)
    result = True
    for bubble in bubbles:
        b_center = bubble.center
        b_radius = bubble.radius
        b_respawning_area = (b_center, b_radius)
        if is_circles_collide(respawning_area, b_respawning_area):
            result = False
            break
    return result

def spawn_bubble():
    """spawn a bubble at a randomly selected respawning bit."""
    global BUBBLE_RESPAWN_CENTERS, BUBBLES, BLUE, RED, GREEN, YELLOW, CYAN, PURPLE
    possible_indices = []
    colors = [BLUE, RED, GREEN, YELLOW, CYAN, PURPLE]
    letters = ["%c" % i for i in range(65, 91)]
    for index in range(5):
        if can_respawn(index, BUBBLES):
            possible_indices.append(index)
    try:
        index = choice(possible_indices)
        center = BUBBLE_RESPAWN_CENTERS[index]
        color = choice(colors)
        letter = choice(letters)
    except IndexError:
        return
    else:
        bubble = Bubble(color, letter, center)
        BUBBLES.append(bubble)

def start_animation(controller):
    """initialize the animation controller.
        Args:
          controller: int.
          bubbles: list, list of instances of bubbles.
    """
    global ANI_SCORE, ANI_VIBRATE, ANI_KEY
    if controller == "ANI_SCORE":
        ANI_SCORE = int(FPS * 0.2)
    if controller == "ANI_VIBRATE":
        ANI_VIBRATE = int(FPS * 0.2)
    if controller == "ANI_KEY":
        ANI_KEY = int(FPS)
   
def start_counter(counter):
    """initialize the counter.
        Args:
          counter: int.
    """
    global CTR_LOSE
    if counter == "CTR_LOSE":
        CTR_LOSE = FPS * 3

def vibrate_x_offset(controller):
    """give a random horizontal offset.
        Args:
          controller: int.
        Return:
          offset: int.
    """
    if 0 <= controller <= int(FPS * 0.2):
        offset = int(normal(0, 4, -6, 6))
        return offset
    else:
        return 0

def init_game():
    """initialize a new game"""
    global BUBBLES, KEY, SCORE, LIFE, FRAME_COUNT, ANI_SCORE, ANI_VIBRATE, MAX_LIFE
    # GAME VARIABLES
    BUBBLES = []
    KEY = None
    SCORE = 0
    LIFE = MAX_LIFE

    # PROCEDURE CONTROLLER
    FPS = 120
    FRAME_COUNT = 0

    # ANIMATION CONTROLLER
    ANI_SCORE = 0 
    ANI_VIBRATE = 0
    ANI_KEY = 0

def background_color(life, frame_count):
    """give a random horizontal offset.
        Args:
          life: int.
          frame_count: int.
        Return:
          color: tuple.
    """
    global MAX_LIFE, LIFE_COLOR_BEGIN, LIFE_COLOR_END, FPS
    r1, g1, b1 = LIFE_COLOR_BEGIN
    r2, g2, b2 = LIFE_COLOR_END
    ratio = sin(frame_count / FPS) * 0.5 + 1
    r = (r1 + (r2 - r1) * ((MAX_LIFE - life) / MAX_LIFE)) * ratio
    g = (g1 + (g2 - g1) * ((MAX_LIFE - life) / MAX_LIFE)) * ratio
    b = (b1 + (b2 - b1) * ((MAX_LIFE - life) / MAX_LIFE)) * ratio
    return(int(r), int(g), int(b))

def move_key_center(ani_key, to):
    """give a random horizontal offset.
        Args:
          ani_key: int.
          index: str, "u_left", "d_left", "u_right", "d_right"
        Return:
          center: tuple.
    """
    global MAX_MOVE_KEY
    x, y = (0, 0)
    if to == "u_left":
        x, y = WIN_WIDTH // 9 - 1, WIN_HEIGHT // 2
        y -= WIN_HEIGHT * ((MAX_MOVE_KEY - ani_key) / MAX_MOVE_KEY) ** 6
    if to == "d_left":
        x, y = WIN_WIDTH // 9 + 1, WIN_HEIGHT // 2
        y += WIN_HEIGHT * ((MAX_MOVE_KEY - ani_key) / MAX_MOVE_KEY) ** 6
    if to == "u_right":
        x, y = WIN_WIDTH * 8 // 9 - 1, WIN_HEIGHT // 2
        y -= WIN_HEIGHT * ((MAX_MOVE_KEY - ani_key) / MAX_MOVE_KEY) ** 6
    if to == "d_right":
        x, y = WIN_WIDTH * 8 // 9 + 1, WIN_HEIGHT // 2
        y += WIN_HEIGHT * ((MAX_MOVE_KEY - ani_key) / MAX_MOVE_KEY) ** 6
    return x, y

def game_update():
    """update process of game in terms of FPS"""
    global FRAME_COUNT, BUBBLES, ANI_SCORE, ANI_VIBRATE, ANI_KEY, CTR_LOSE
    update()
    FRAME_COUNT += 1
    ANI_SCORE -= 1
    ANI_VIBRATE -= 1
    ANI_KEY -= 1
    CTR_LOSE -= 1

class Event_dialogue:
    global CLOCK, FPS, RUN, BLACK, WIN_WIDTH, WIN_HEIGHT, WIN, WHITE
    def __init__(self, bg):
        self.bg = bg.copy()
        self.run = True
        self.stage = 0
        self.clock = CLOCK

    def pause(self):
        bg = self.bg.copy()
        self.run = True
        self.stage = 0
        while self.run:
            self.clock.tick(FPS)
            if self.stage == 0:
                for evnt in event.get():
                    if evnt.type == QUIT:
                        RUN = False
                        self.run = False
                        break
                    if evnt.type == KEYDOWN:
                        if evnt.key == K_SPACE:
                            self.run = False
                # blit background
                draw.rect(bg, BLACK, Rect(WIN_WIDTH * 7 // 20, WIN_HEIGHT * 4 // 9, 270, 80), 0)
                draw.rect(bg, WHITE, Rect(WIN_WIDTH * 7 // 20, WIN_HEIGHT * 4 // 9, 270, 80), 5)
                WIN.blit(bg, (0 + vibrate_x_offset(ANI_VIBRATE), 0))

                # blit pause
                myFont = font.SysFont('microsoftjhengheimicrosoftjhengheiuibold', 32, bold=True, italic=True)
                pause = myFont.render("PAUSE", True, WHITE)
                pause_rect = pause.get_rect(center=(WIN_WIDTH // 2, WIN_HEIGHT // 2)) 
                WIN.blit(pause, pause_rect)
                update()



class Bubble():
    """movable bubble with a letter and different colors for a corresponding faculty"""
    def __init__(self, color, letter, center):
        self.color = color # BLUE, RED, GREEN, YELLOW, CYAN, PURPPLE
        self.letter = letter
        self.center = center
        self.radius = int(normal(BUBBLE_RADIUS_MEAN, BUBBLE_RADIUS_STD, BUBBLE_RADIUS_MIN, BUBBLE_RADIUS_MAX)) # radius 25 ~ 50
        self.speed = self.radius // 5 - 4 # fast 1 ~ 6 slow
        self.status = "alive" # "alive", "dead"
        self.left_prob = normal(0.1, 0.08, 0, 0.2)

    def move(self, bubbles):
        global FRAME_COUNT, BUBBLES
        PROB_LEFT, PROB_RIGHT, PROB_ELSE = self.left_prob, 0.2 - self.left_prob, 1 - (self.left_prob + 0.2 - self.left_prob)
        choices = ["l"] * int(PROB_LEFT * 100) + ["r"] * int(PROB_RIGHT * 100) + ["e"] * int(PROB_ELSE * 100)
        if FRAME_COUNT % 200 % self.speed == 0:
            action = choice(choices)
            if action == "l":
                x, y = self.center
                self.center = (x - 1, y)
                if self._is_collide(BUBBLES) or self._is_hit_wall():
                    self.center = (x, y)
            elif action == "r":
                x, y = self.center
                self.center = (x + 1, y)
                if self._is_collide(BUBBLES) or self._is_hit_wall():
                    self.center = (x, y)
            x, y = self.center
            self.center = (x, y - 1)
            if self._is_collide(BUBBLES) and not self._is_hit_roof():
                self.center = (x, y)
            elif self._is_hit_roof():
                self.status = "dead"

    def _is_collide(self, others):
        cur_bubble = (self.center, self.radius)
        result = False
        for bubble in others:
            if bubble is not self and bubble.status == "alive":
                oth_bubble = (bubble.center, bubble.radius)
                if is_circles_collide(cur_bubble, oth_bubble):
                    result = True
                    break
        return result

    def _is_hit_wall(self):
        global WIN_WIDTH
        x, y = self.center
        radius = self.radius
        result = False
        if x - radius <= WIN_WIDTH * 2 // 9 or x + radius >= WIN_WIDTH * 7 // 9:
            result = True
        return result

    def _is_hit_roof(self):
        global WIN_HEIGHT
        x, y = self.center
        radius = self.radius
        result = False
        if y - radius <= WIN_HEIGHT // 9:
            result = True
        return result



if __name__ == "__main__":
    while RUN:
        CLOCK.tick(FPS)
        event_dialogue = Event_dialogue(BG)

        ##### STAGE 1 #####

        if STAGE == 1:
            for evnt in event.get():
                if evnt.type == QUIT:
                    RUN = False
                if evnt.type == MOUSEBUTTONDOWN:
                    pass
                if evnt.type == KEYDOWN:
                    pg_keys = ["K_%c" % i for i in range(97, 123)]
                    for key in pg_keys:
                        if evnt.key == eval(key):
                            KEY = key[-1].upper()
                        if evnt.key == K_SPACE:
                            event_dialogue.pause()
                            break

            # shoot a bubble
            if KEY != None:
                TEMP_BUBBLES = []
                for bubble in BUBBLES:
                    if bubble.letter == KEY:
                        TEMP_BUBBLES.append(bubble)
                if len(TEMP_BUBBLES) > 0:
                    TEMP_BUBBLES.sort(key=lambda x: x.center[1] - x.radius, reverse=True)
                    shot_bubble = TEMP_BUBBLES.pop()
                    SCORE += int((7 - shot_bubble.speed) ** 1.5 * 50)
                    BUBBLES.remove(shot_bubble)
                    start_animation("ANI_SCORE") 
                    start_animation("ANI_KEY")       
                    MOVE_KEY = KEY
                else:
                    LIFE -= 1
                    start_animation("ANI_VIBRATE")
                    MOVE_KEY = "OOPS!"
                    start_animation("ANI_KEY") 
                KEY = None

            # spawn bubbles
            bool_pool = [0] * (FPS // 2) + [1] * (FRAME_COUNT // FPS // 60 + 1)
            if choice(bool_pool):
                spawn_bubble()

            # move bubbles
            for bubble in BUBBLES:
                bubble.move(BUBBLES)

            # dispose of dead bubbles
            TEMP_BUBBLES = []
            if len(BUBBLES) > 0:
                for bubble in BUBBLES:
                    if bubble.status == "alive":
                        TEMP_BUBBLES.append(bubble)
                    else:
                        start_animation("ANI_VIBRATE")
                        LIFE -= 1
                BUBBLES = TEMP_BUBBLES

            # background
            BG.fill(background_color(LIFE, FRAME_COUNT))

            # draw railings
            draw.line(BG, (100, 100, 100), (WIN_WIDTH * 2 // 9, 0), (WIN_WIDTH * 2 // 9, WIN_HEIGHT), 3)
            draw.line(BG, (100, 100, 100), (WIN_WIDTH * 7 // 9, 0), (WIN_WIDTH * 7 // 9, WIN_HEIGHT), 3)
            draw.line(BG, (150, 0, 0), (WIN_WIDTH * 2 // 9, WIN_HEIGHT // 9), (WIN_WIDTH * 7 // 9, WIN_HEIGHT // 9), 4)
            # pg.draw.line(BG, (100, 100, 0), (WIN_WIDTH // 2, WIN_HEIGHT // 9 + WIN_HEIGHT // 30),  (WIN_WIDTH // 2, WIN_HEIGHT - WIN_HEIGHT // 30), 1)

            # draw bubbles
            for bubble in BUBBLES:
                draw.circle(BG, bubble.color, bubble.center, bubble.radius, 0)

            # blit background
            WIN.blit(BG, (0 + vibrate_x_offset(ANI_VIBRATE), 0))

            # blit letters
            for bubble in BUBBLES:
                myFont = font.SysFont('microsoftjhengheimicrosoftjhengheiuibold', int(bubble.radius * 1.2), bold=True)
                r, g, b = bubble.color
                letter_color = (int(r * 0.5), int(g * 0.5), int(b * 0.5))
                letter = myFont.render(bubble.letter, True, letter_color)
                letter_rect = letter.get_rect(center=bubble.center)     
                WIN.blit(letter, letter_rect)

            # blit score
            myFont = font.SysFont('microsoftjhengheimicrosoftjhengheiuibold', (max(ANI_SCORE, 0) // 5) ** 2 + 30, bold=True, italic=True)
            score = myFont.render(str(SCORE), True, WHITE)
            score_rect = score.get_rect(center=(WIN_WIDTH // 2, WIN_HEIGHT // 18)) 
            WIN.blit(score, score_rect)

            # blit key
            if ANI_KEY > 0:
                tos = ["u_left", "d_left", "d_right", "u_right"]
                colors = [RED, BLUE, RED, BLUE]
                for color, to in zip(colors, tos):
                    if MOVE_KEY == "OOPS!" and (to == "u_left" or to == "d_left"):
                        myFont = font.SysFont('microsoftjhengheimicrosoftjhengheiuibold', 40, bold=True, italic=True)
                        key = myFont.render(MOVE_KEY, True, RED)
                        key_rect = key.get_rect(center=(WIN_WIDTH // 9, WIN_HEIGHT // 2))
                    elif MOVE_KEY == "OOPS!" and (to == "u_right" or to == "d_right"):
                        myFont = font.SysFont('microsoftjhengheimicrosoftjhengheiuibold', 40, bold=True, italic=True)
                        key = myFont.render(MOVE_KEY, True, RED)
                        key_rect = key.get_rect(center=(WIN_WIDTH * 8 // 9, WIN_HEIGHT // 2))
                    else:
                        myFont = font.SysFont('microsoftjhengheimicrosoftjhengheiuibold', 100, bold=True, italic=True)
                        key = myFont.render(MOVE_KEY, True, color)
                        key_rect = key.get_rect(center=move_key_center(ANI_KEY, to))
                    WIN.blit(key, key_rect)

            # check live
            if LIFE <= 0:
                start_counter("CTR_LOSE")
                STAGE = 2

        ##### STAGE 2 #####

        elif STAGE == 2:
            for evet in event.get():
                if evet.type == QUIT:
                    RUN = False

            # background
            BG.fill(RED)

            # draw railings
            draw.line(BG, (80, 80, 80), (WIN_WIDTH * 2 // 9, 0), (WIN_WIDTH * 2 // 9, WIN_HEIGHT), 3)
            draw.line(BG, (80, 80, 80), (WIN_WIDTH * 7 // 9, 0), (WIN_WIDTH * 7 // 9, WIN_HEIGHT), 3)
            draw.line(BG, (150, 0, 0), (WIN_WIDTH * 2 // 9, WIN_HEIGHT // 9), (WIN_WIDTH * 7 // 9, WIN_HEIGHT // 9), 4)
            # pg.draw.line(BG, (100, 100, 0), (WIN_WIDTH // 2, WIN_HEIGHT // 9 + WIN_HEIGHT // 30),  (WIN_WIDTH // 2, WIN_HEIGHT - WIN_HEIGHT // 30), 1)

            # blit background
            WIN.blit(BG, (0, 0))

            # draw lose
            myFont = font.SysFont('microsoftjhengheimicrosoftjhengheiuibold', 80, bold=True, italic=True)
            lose = myFont.render("YOU LOSE", True, WHITE)
            lose_rect = lose.get_rect(center=(WIN_WIDTH // 2, WIN_HEIGHT // 2)) 
            WIN.blit(lose, lose_rect)

            # counter
            if CTR_LOSE < 0:
                STAGE = 0
                data = get_data()
                index = 6
                for i, score in enumerate(data):
                    if score < SCORE:
                        index = i
                        break
                data.insert(index, SCORE)
                set_data(data)
                init_game()

        ##### STAGE 0 #####

        elif STAGE == 0:
            for evet in event.get():
                if evet.type == QUIT:
                    RUN = False
                if evet.type == KEYDOWN:
                    STAGE = 1

            # background
            BG.fill((50, 0, 50))

            # draw railings
            draw.line(BG, (80, 80, 80), (WIN_WIDTH * 2 // 9, 0), (WIN_WIDTH * 2 // 9, WIN_HEIGHT), 3)
            draw.line(BG, (80, 80, 80), (WIN_WIDTH * 7 // 9, 0), (WIN_WIDTH * 7 // 9, WIN_HEIGHT), 3)
            draw.line(BG, (150, 0, 0), (WIN_WIDTH * 2 // 9, WIN_HEIGHT // 9), (WIN_WIDTH * 7 // 9, WIN_HEIGHT // 9), 4)
            # pg.draw.line(BG, (100, 100, 0), (WIN_WIDTH // 2, WIN_HEIGHT // 9 + WIN_HEIGHT // 30),  (WIN_WIDTH // 2, WIN_HEIGHT - WIN_HEIGHT // 30), 1)

            # blit background
            WIN.blit(BG, (0, 0))

            # blit leaderboard
            myFont = font.SysFont('microsoftjhengheimicrosoftjhengheiuibold', 40, bold=True, italic=True)
            leaderboard = myFont.render("LEADERBOARD", True, YELLOW)
            leaderboard_rect = leaderboard.get_rect(center=(WIN_WIDTH // 2, WIN_HEIGHT // 5)) 
            WIN.blit(leaderboard, leaderboard_rect)

            data = get_data()
            for i, score in enumerate(data):
                myFont = font.SysFont('microsoftjhengheimicrosoftjhengheiuibold', 36, bold=True, italic=True)
                row_data = myFont.render("{:<2d} : {:>15d}".format(i + 1, score), True, WHITE)
                pos = (WIN_WIDTH * 4 // 13, WIN_HEIGHT * (4 + i) // 13)
                WIN.blit(row_data, pos)
            
            # blit start
            myFont = font.SysFont('microsoftjhengheimicrosoftjhengheiuibold', 23, bold=True, italic=True)
            start = myFont.render("PRESS ANY KEY TO START", True, CYAN)
            start_rect = start.get_rect(center=(WIN_WIDTH // 2, WIN_HEIGHT * 12 // 14)) 
            WIN.blit(start, start_rect)

            # blit version
            myFont = font.SysFont('microsoftjhengheimicrosoftjhengheiuibold', 17, bold=True)
            start = myFont.render("version " + VERSION, True, (120, 120, 120))
            start_rect = start.get_rect(center=(WIN_WIDTH * 17 // 25, WIN_HEIGHT * 19 // 20)) 
            WIN.blit(start, start_rect)

        # UPDATE
        game_update()

    pg_quit()

