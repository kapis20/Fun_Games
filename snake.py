import turtle
import random

w = 500
h = 500
food_size = 10
delay = 100
cell = 20  # grid step (snake moves by 20)

offsets = {
    "up": (0, cell),
    "down": (0, -cell),
    "left": (-cell, 0),
    "right": (cell, 0)
}
running = True
button_rect = None  # (x1, y1, x2, y2)

ui = turtle.Turtle(visible=False)
ui.penup()
ui.color("red")

btn = turtle.Turtle(visible=False)
btn.penup()
btn.color("black")
def show_game_over():
    global button_rect

    # text
    ui.clear()
    ui.goto(0, 40)
    ui.write("GAME OVER", align="center", font=("Arial", 28, "bold"))
    ui.goto(0, 10)
    ui.write("Click RESET to play again", align="center", font=("Arial", 14, "normal"))

    # button (draw a filled rectangle + text)
    btn.clear()
    btn.goto(-70, -60)
    btn.pendown()
    btn.fillcolor("white")
    btn.begin_fill()
    for _ in range(2):
        btn.forward(140)
        btn.right(90)
        btn.forward(45)
        btn.right(90)
    btn.end_fill()
    btn.penup()

    btn.goto(0, -92)
    btn.color("black")
    btn.write("RESET", align="center", font=("Arial", 16, "bold"))

    # clickable area: left, top, right, bottom
    button_rect = (-70, -60, 70, -105)

def hide_game_over():
    global button_rect
    ui.clear()
    btn.clear()
    button_rect = None

def on_click(x, y):
    # if game over and click is inside button -> reset
    if button_rect is None:
        return
    x1, y1, x2, y2 = button_rect
    if x1 <= x <= x2 and y2 <= y <= y1:
        reset()

def reset():
    global snake, snake_dir, food_position, obstacles, running
    running = True
    hide_game_over()
    snake = [[0, 0], [0, 20], [0, 40], [0, 60], [0, 80]]
    snake_dir = "up"

    # create random obstacles each reset
    obstacles = create_obstacles(count=12)
    draw_obstacles()

    food_position = get_random_food_position()
    food.goto(food_position)

    move_snake()

def create_obstacles(count=10):
    """Return a list of (x, y) obstacle positions aligned to the grid."""
    obs = set()
    attempts = 0
    max_attempts = 5000

    while len(obs) < count and attempts < max_attempts:
        attempts += 1
        x = random.randint(int(-w/2 + cell), int(w/2 - cell))
        y = random.randint(int(-h/2 + cell), int(h/2 - cell))

        # snap to grid
        x = (x // cell) * cell
        y = (y // cell) * cell
        pos = (x, y)

        # don't place on snake start
        if list(pos) in snake:
            continue

        obs.add(pos)

    return list(obs)

def draw_obstacles():
    wall_pen.clearstamps()
    for (x, y) in obstacles:
        wall_pen.goto(x, y)
        wall_pen.stamp()

def move_snake():
    global snake_dir, running
    if not running:
        return

    new_head = snake[-1].copy()
    new_head[0] += offsets[snake_dir][0]
    new_head[1] += offsets[snake_dir][1]

    # wrap around (your behavior)
    if new_head[0] > w / 2:
        new_head[0] -= w
    elif new_head[0] < -w / 2:
        new_head[0] += w
    if new_head[1] > h / 2:
        new_head[1] -= h
    elif new_head[1] < -h / 2:
        new_head[1] += h

    # collision with self
    if new_head in snake[:-1]:
        running = False
        show_game_over()
        screen.update()
        return

    # collision with obstacles
    if (new_head[0], new_head[1]) in obstacles:
        running = False
        show_game_over()    
        screen.update()
        return

    snake.append(new_head)

    if not food_collision():
        snake.pop(0)

    pen.clearstamps()
    for segment in snake:
        pen.goto(segment[0], segment[1])
        pen.stamp()

    screen.update()
    turtle.ontimer(move_snake, delay)

def food_collision():
    global food_position
    if get_distance(snake[-1], food_position) < 20:
        food_position = get_random_food_position()
        food.goto(food_position)
        return True
    return False

def get_random_food_position():
    while True:
        x = random.randint(int(-w/2 + food_size), int(w/2 - food_size))
        y = random.randint(int(-h/2 + food_size), int(h/2 - food_size))

        # snap to grid so food sits on same cells
        x = (x // cell) * cell
        y = (y // cell) * cell
        pos = (x, y)

        # avoid snake and obstacles
        if [x, y] in snake:
            continue
        if pos in obstacles:
            continue

        return pos

def get_distance(pos1, pos2):
    x1, y1 = pos1
    x2, y2 = pos2
    return ((y2 - y1) ** 2 + (x2 - x1) ** 2) ** 0.5

def go_up():
    global snake_dir
    if snake_dir != "down":
        snake_dir = "up"

def go_right():
    global snake_dir
    if snake_dir != "left":
        snake_dir = "right"

def go_down():
    global snake_dir
    if snake_dir != "up":
        snake_dir = "down"

def go_left():
    global snake_dir
    if snake_dir != "right":
        snake_dir = "left"

screen = turtle.Screen()
screen.setup(w, h)
screen.title("Snake")
screen.bgcolor("lightblue")
screen.tracer(0)

screen.onclick(on_click)

pen = turtle.Turtle("square")
pen.color("green")
pen.penup()

# obstacle pen
wall_pen = turtle.Turtle("square")
wall_pen.color("white")
wall_pen.penup()

food = turtle.Turtle("square")
food.color("darkorange")
food.shapesize(food_size / 20)
food.penup()

screen.listen()
screen.onkey(go_up, "Up")
screen.onkey(go_right, "Right")
screen.onkey(go_down, "Down")
screen.onkey(go_left, "Left")

reset()
turtle.done()
