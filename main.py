__version__ = "0.1.0"

import random
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget


CELL = 20
COLS = 25
ROWS = 25
GAME_W = COLS * CELL
GAME_H = ROWS * CELL

TOP_BAR_H = 50
Window.size = (GAME_W, GAME_H + TOP_BAR_H)


OFFSETS = {
    "up": (0, 1),
    "down": (0, -1),
    "left": (-1, 0),
    "right": (1, 0),
}


def wrap(x, y):
    return x % COLS, y % ROWS


class SnakeGame(Widget):
    def __init__(self, on_state_change, **kwargs):
        super().__init__(**kwargs)
        self.on_state_change = on_state_change

        # Game config
        self.tick_s = 0.12
        self.start_lives = 1
        self.max_lives = 5
        self.life_spawn_chance = 0.30
        self.life_despawn_s = 8.0

        # State
        self.running = True
        self.game_over = False

        self.snake = []
        self.snake_dir = "up"
        self.food = None
        self.obstacles = set()

        self.life_active = False
        self.life_pos = None
        self._life_despawn_ev = None

        self.score = 0
        self.lives = self.start_lives

        # swipe control
        self._touch_start = None

        self.new_game()
        Clock.schedule_interval(self.step, self.tick_s)

    # ---------- Spawning helpers ----------
    def random_free_cell(self):
        while True:
            x = random.randrange(COLS)
            y = random.randrange(ROWS)
            p = (x, y)
            if p in self.obstacles:
                continue
            if p in self.snake:
                continue
            if self.food is not None and p == self.food:
                continue
            if self.life_active and self.life_pos is not None and p == self.life_pos:
                continue
            return p

    def create_obstacles(self, count):
        obs = set()
        tries = 0
        while len(obs) < count and tries < 5000:
            tries += 1
            p = (random.randrange(COLS), random.randrange(ROWS))
            if p in self.snake:
                continue
            obs.add(p)
        return obs

    # ---------- Lives / reset ----------
    def new_game(self):
        self.score = 0
        self.lives = self.start_lives
        self.running = True
        self.game_over = False

        # fresh map
        self.obstacles = self.create_obstacles(count=random.randint(5, 15))
        self.reset_round(regen_map=False)

        self._notify()

    def reset_round(self, regen_map=False):
        """Respawn snake after losing a life (or at new game)."""
        if regen_map:
            self.obstacles = self.create_obstacles(count=random.randint(5, 15))

        self.remove_extra_life()

        # start snake in the middle, going up
        cx, cy = COLS // 2, ROWS // 2
        self.snake = [(cx, cy - 2), (cx, cy - 1), (cx, cy)]
        self.snake_dir = "up"

        self.food = self.random_free_cell()
        self.running = True

        self.draw()

    def lose_life(self):
        self.lives -= 1
        self._notify()
        self.remove_extra_life()

        if self.lives <= 0:
            self.running = False
            self.game_over = True
            self._notify()
            return

        # still have lives -> respawn snake, keep obstacles/score
        self.reset_round(regen_map=False)

    # ---------- Extra life pickup ----------
    def remove_extra_life(self):
        self.life_active = False
        self.life_pos = None
        if self._life_despawn_ev is not None:
            self._life_despawn_ev.cancel()
            self._life_despawn_ev = None

    def maybe_spawn_extra_life(self):
        if self.life_active:
            return
        if random.random() > self.life_spawn_chance:
            return
        self.life_pos = self.random_free_cell()
        self.life_active = True
        self._life_despawn_ev = Clock.schedule_once(
            lambda dt: self.remove_extra_life(), self.life_despawn_s
        )

    # ---------- Input (swipe) ----------
    def on_touch_down(self, touch):
        if self.game_over:
            return super().on_touch_down(touch)
        self._touch_start = touch.pos
        return True

    def on_touch_up(self, touch):
        if self.game_over or self._touch_start is None:
            return super().on_touch_up(touch)

        x0, y0 = self._touch_start
        x1, y1 = touch.pos
        dx, dy = x1 - x0, y1 - y0

        if abs(dx) < 20 and abs(dy) < 20:
            return True  # tiny swipe, ignore

        if abs(dx) > abs(dy):
            self.set_dir("right" if dx > 0 else "left")
        else:
            self.set_dir("up" if dy > 0 else "down")

        self._touch_start = None
        return True

    def set_dir(self, d):
        # block reverse direction
        if (self.snake_dir == "up" and d == "down") or (self.snake_dir == "down" and d == "up"):
            return
        if (self.snake_dir == "left" and d == "right") or (self.snake_dir == "right" and d == "left"):
            return
        self.snake_dir = d

    # ---------- Game loop ----------
    def step(self, dt):
        if not self.running:
            return

        head_x, head_y = self.snake[-1]
        ox, oy = OFFSETS[self.snake_dir]
        nx, ny = wrap(head_x + ox, head_y + oy)
        new_head = (nx, ny)

        # collisions
        if new_head in self.snake:
            self.lose_life()
            self.draw()
            return
        if new_head in self.obstacles:
            self.lose_life()
            self.draw()
            return

        # move
        self.snake.append(new_head)

        ate_food = (self.food == new_head)
        if ate_food:
            self.score += 1

            # new obstacles every time food is eaten (like your turtle version)
            self.obstacles = self.create_obstacles(count=random.randint(5, 15))

            # respawn food
            self.food = self.random_free_cell()

            # maybe spawn extra life pickup
            self.maybe_spawn_extra_life()
            self._notify()
        else:
            self.snake.pop(0)

        # extra life pickup collision
        if self.life_active and self.life_pos == new_head:
            if self.lives < self.max_lives:
                self.lives += 1
            self.remove_extra_life()
            self._notify()

        self.draw()

    # ---------- Drawing ----------
    def draw_cell(self, x, y):
        return (x * CELL, y * CELL), (CELL, CELL)

    def draw(self):
        self.canvas.clear()
        with self.canvas:
            # background (optional)
            # Color(0.68, 0.85, 0.90, 1)  # light blue
            # Rectangle(pos=self.pos, size=self.size)

            # obstacles
            Color(1, 1, 1, 1)
            for (x, y) in self.obstacles:
                pos, size = self.draw_cell(x, y)
                Rectangle(pos=pos, size=size)

            # food
            if self.food is not None:
                Color(1, 0.55, 0, 1)  # orange
                pos, size = self.draw_cell(*self.food)
                Rectangle(pos=pos, size=size)

            # extra life
            if self.life_active and self.life_pos is not None:
                Color(1, 0, 0, 1)
                pos, size = self.draw_cell(*self.life_pos)
                Rectangle(pos=pos, size=size)

            # snake
            Color(0, 0.6, 0, 1)
            for (x, y) in self.snake:
                pos, size = self.draw_cell(x, y)
                Rectangle(pos=pos, size=size)

    def _notify(self):
        # tell UI to update labels/overlay
        if self.on_state_change:
            self.on_state_change(
                lives=self.lives,
                score=self.score,
                game_over=self.game_over,
            )


class SnakeApp(App):
    def build(self):
        root = BoxLayout(orientation="vertical")

        # top bar
        top = BoxLayout(size_hint_y=None, height=TOP_BAR_H, padding=8, spacing=8)
        self.info = Label(text="Lives: 3   Score: 0", color=(1, 1, 1, 1))
        btn_reset = Button(text="Reset", size_hint_x=None, width=120)
        btn_reset.bind(on_release=lambda *_: self.game.new_game())
        top.add_widget(self.info)
        top.add_widget(btn_reset)

        # game area + overlay
        layer = FloatLayout(size_hint=(1, 1))
        self.overlay = Label(
            text="GAME OVER\nTap Reset",
            halign="center",
            valign="middle",
            font_size=36,
            opacity=0,
            color=(1, 0, 0, 1),
        )
        self.overlay.bind(size=self.overlay.setter("text_size"))

        self.game = SnakeGame(on_state_change=self.on_state_change, size_hint=(None, None), size=(GAME_W, GAME_H))
        layer.add_widget(self.game)
        layer.add_widget(self.overlay)

        root.add_widget(top)
        root.add_widget(layer)

        # initialize label
        self.on_state_change(lives=self.game.lives, score=self.game.score, game_over=self.game.game_over)
        return root

    def on_state_change(self, lives, score, game_over):
        self.info.text = f"Lives: {lives}   Score: {score}"
        self.overlay.opacity = 1 if game_over else 0


if __name__ == "__main__":
    SnakeApp().run()
