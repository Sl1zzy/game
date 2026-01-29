import arcade
from arcade.particles import *
import time
from levels import Level
from database import GameDatabase
import random

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Bugilla!"
GRAVITY = 1
PLAYER_JUMP_SPEED = 20
PLAYER_MOVE_SPEED = 5

CAMERA_SPEED = 0.1
ZOOM_LEVEL = 0.8


class Player(arcade.Sprite):
    def __init__(self):
        super().__init__("assets/tagilla.png")
        self.scale = 0.15
        self.center_x = 50
        self.center_y = 150
        self.change_x = 0
        self.change_y = 0
        self.jumping = False
        self.rubless = 0
        self.score = 0
        self.lives = 3
        self.level = 1

class Rubles(arcade.Sprite):
    def __init__(self, x, y):
        super().__init__("assets/rubles.png", 0.1)
        self.center_x = x
        self.center_y = y

class PMC(arcade.Sprite):
    def __init__(self, x, y, left_bound, right_bound):
        super().__init__("assets/pmc.png", 0.1)
        self.center_x = x
        self.center_y = y
        self.change_x = 2
        self.left_bound = left_bound
        self.right_bound = right_bound

class Platform(arcade.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__("assets/block.png")
        self.center_x = x + width / 2
        self.center_y = y + height / 2
        self.width = width
        self.height = height

class Flag(arcade.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.flag_textures = []
        for i in range(3):
            texture = arcade.load_texture(f'assets/flag/flag{i}.png')
            self.flag_textures.append(texture)
        
        self.scale = 3.0
        self.texture = self.flag_textures[0]
        self.center_x = x
        self.center_y = y

        self.current_frame = 0
        self.animation_speed = 0.15
        self.animation_timer = 0.0
        self.animation_active = True
    
    def update_animation(self, delta_time):
        if not self.animation_active or len(self.flag_textures) == 0:
            return
        
        self.animation_timer += delta_time

        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0.0

            self.current_frame += 1

            if self.current_frame >= len(self.flag_textures):
                self.current_frame = 0

            self.texture = self.flag_textures[self.current_frame]
    
    def start_animation(self):
        self.animation_active = True
    
    def stop_animation(self):
        self.animation_active = False

class GameWindow(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        
        self.players = None
        self.platforms = None
        self.rubless = None
        self.pmcs = None
        self.flags = None
        self.physics_engine = None
        self.game_state = "menu"
        self.player_name = "Игрок"
        self.current_level = 1
        self.level_start_time = 0
        self.level_completion_time = 0
        self.pmcs_defeated = 0
        
        self.camera = None
        self.gui_camera = None
        self.camera_x = 0
        self.camera_y = 0
        self.target_zoom = ZOOM_LEVEL
        self.db = GameDatabase()
        
        self.emitters = []

        self.bg_music = None
        
        arcade.set_background_color(arcade.color.SKY_BLUE)
    
    def setup_level(self, level_num):
        self.camera = arcade.Camera2D()
        self.gui_camera = arcade.Camera2D()
        self.camera_x = self.player.center_x + 400
        self.camera_y = self.player.center_y + 400
        self.gui_camera.position = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        
        self.current_level = level_num
        levels = Level.get_level(level_num)
        
        self.player = Player()
        self.player.level = level_num
        self.player.center_x, self.player.center_y = levels['player_start']
        self.players = arcade.SpriteList()
        self.players.append(self.player)
        
        self.platforms = arcade.SpriteList()
        for plat in levels['platforms']:
            platform = Platform(*plat)
            self.platforms.append(platform)
        
        self.rubless = arcade.SpriteList()
        for rubles_pos in levels['rubless']:
            rubles = Rubles(*rubles_pos)
            self.rubless.append(rubles)
        
        self.pmcs = arcade.SpriteList()
        for pmc_data in levels['pmcs']:
            pmc = PMC(*pmc_data)
            self.pmcs.append(pmc)
        
        self.flags = arcade.SpriteList()
        self.flag = Flag(*levels['flag'])
        self.flags.append(self.flag)
        
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player,
            self.platforms,
            gravity_constant=GRAVITY
        )

        self.level_start_time = time.time()
        self.pmcs_defeated = 0

        arcade.set_background_color(levels['background_color'])
    
    def setup(self):
        self.game_state = "menu"
        self.start_background_music()
    
    def on_draw(self):
        self.clear()
        for e in self.emitters:
            e.draw()
        if self.game_state == "menu":
            self.draw_menu()
        elif self.game_state == "playing":
            self.draw_game()
        elif self.game_state == "level_complete":
            self.draw_level_complete()
        elif self.game_state == "game_over":
            self.draw_game_over()
    
    
    
    def start_background_music(self):
        music_file = "assets/music/background.mp3"
            
        import os
        if os.path.exists(music_file):
            self.background_music = arcade.load_sound(music_file)
            arcade.play_sound(self.background_music, volume=0.3, loop=True)
        


    def draw_game(self):
        self.camera.use()

        self.clear()
        self.platforms.draw()
        self.rubless.draw()
        self.pmcs.draw()
        self.flags.draw()
        self.players.draw()

        arcade.draw_text(f"Уровень: {self.current_level}", 10, SCREEN_HEIGHT - 30, 
                        arcade.color.WHITE, 18)
        arcade.draw_text(f"Очки: {self.player.score}", 10, SCREEN_HEIGHT - 60, 
                        arcade.color.WHITE, 18)
        arcade.draw_text(f"Монеты: {self.player.rubless}", 10, SCREEN_HEIGHT - 90, 
                        arcade.color.WHITE, 18)
        arcade.draw_text(f"Жизни: {self.player.lives}", 10, SCREEN_HEIGHT - 120, 
                        arcade.color.WHITE, 18)

        elapsed_time = int(time.time() - self.level_start_time)
        arcade.draw_text(f"Время: {elapsed_time} сек", SCREEN_WIDTH - 150, 
                        SCREEN_HEIGHT - 30, arcade.color.WHITE, 18)
        
        for emitter in self.emitters:
            emitter.draw()
    
    def draw_level_complete(self):
        self.gui_camera.use()
        arcade.draw_text("УРОВЕНЬ ПРОЙДЕН!", 
                        SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100,
                        arcade.color.GOLD, 36, anchor_x="center")
        
        arcade.draw_text(f"Уровень: {self.current_level}", 
                        SCREEN_WIDTH // 2, SCREEN_HEIGHT - 180,
                        arcade.color.WHITE, 24, anchor_x="center")
        
        arcade.draw_text(f"Собрано монет: {self.player.rubless}", 
                        SCREEN_WIDTH // 2, SCREEN_HEIGHT - 220,
                        arcade.color.WHITE, 24, anchor_x="center")
        
        arcade.draw_text(f"Побеждено врагов: {self.pmcs_defeated}", 
                        SCREEN_WIDTH // 2, SCREEN_HEIGHT - 260,
                        arcade.color.WHITE, 24, anchor_x="center")
        
        arcade.draw_text(f"Время прохождения: {int(self.level_completion_time)} сек", 
                        SCREEN_WIDTH // 2, SCREEN_HEIGHT - 300,
                        arcade.color.WHITE, 24, anchor_x="center")
        
        arcade.draw_text(f"Итоговые очки: {self.player.score}", 
                        SCREEN_WIDTH // 2, SCREEN_HEIGHT - 340,
                        arcade.color.GOLD, 28, anchor_x="center")
        
        if self.current_level < 3:
            arcade.draw_text("Нажмите SPACE для следующего уровня", 
                            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 400,
                            arcade.color.BLACK, 20, anchor_x="center")
        else:
            arcade.draw_text("ИГРА ПРОЙДЕНА! Нажмите SPACE для меню", 
                            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 400,
                            arcade.color.GOLD, 20, anchor_x="center")
        
        arcade.draw_text("Нажмите ESC для сохранения и выхода в меню", 
                        SCREEN_WIDTH // 2, SCREEN_HEIGHT - 450,
                        arcade.color.BLACK, 18, anchor_x="center")
    
    def draw_menu(self):
        arcade.draw_text("Bugilla!", 
                        SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100,
                        arcade.color.BLACK, 36, anchor_x="center")
        
        arcade.draw_text(f"Игрок: {self.player_name}", 
                        SCREEN_WIDTH // 2, SCREEN_HEIGHT - 180,
                        arcade.color.DARK_BLUE, 24, anchor_x="center")

        saved_game = self.db.load_game(self.player_name)
        if saved_game:
            arcade.draw_text(f"Сохранение: Уровень {saved_game['level']}, Очки: {saved_game['score']}", 
                            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 220,
                            arcade.color.BLUE, 18, anchor_x="center")
        
        arcade.draw_text("1 - Новая игра", 
                        SCREEN_WIDTH // 2, SCREEN_HEIGHT - 280,
                        arcade.color.BLACK, 24, anchor_x="center")
        
        arcade.draw_text("2 - Загрузить игру", 
                        SCREEN_WIDTH // 2, SCREEN_HEIGHT - 320,
                        arcade.color.BLACK, 24, anchor_x="center")
        
        arcade.draw_text("ESC - Выход", 
                        SCREEN_WIDTH // 2, SCREEN_HEIGHT - 400,
                        arcade.color.BLACK, 24, anchor_x="center")
    
    def draw_game_over(self):
        self.gui_camera.use()
        arcade.draw_text("GAME OVER", 
                        SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100,
                        arcade.color.RED, 48, anchor_x="center")
        
        arcade.draw_text(f"Ваш счет: {self.player.score}", 
                        SCREEN_WIDTH // 2, SCREEN_HEIGHT - 180,
                        arcade.color.WHITE, 28, anchor_x="center")
        
        arcade.draw_text("Нажмите SPACE для новой игры", 
                        SCREEN_WIDTH // 2, SCREEN_HEIGHT - 250,
                        arcade.color.GREEN, 24, anchor_x="center")
        
        arcade.draw_text("Нажмите ESC для выхода в меню", 
                        SCREEN_WIDTH // 2, SCREEN_HEIGHT - 300,
                        arcade.color.LIGHT_GRAY, 20, anchor_x="center")
    
    def on_update(self, delta_time):
        if self.game_state != "playing":
            return
        
        for flag in self.flags:
            flag.update_animation(delta_time)
            
        self.physics_engine.update()
        
        for pmc in self.pmcs:
            pmc.center_x += pmc.change_x

            if pmc.center_x <= pmc.left_bound:
                pmc.change_x = abs(pmc.change_x)
            elif pmc.center_x >= pmc.right_bound:
                pmc.change_x = -abs(pmc.change_x)

        pmc_hit_list = arcade.check_for_collision_with_list(self.player, self.pmcs)
        for pmc in pmc_hit_list:
            if self.player.change_y < 0 and self.player.bottom > pmc.top - 30:
                self.create_burst_explosion(pmc.center_x, pmc.center_y)
                
                pmc.remove_from_sprite_lists()
                self.pmcs_defeated += 1
                self.player.score += 100
                self.player.change_y = PLAYER_JUMP_SPEED / 2
            else:
                self.player.lives -= 1
                if self.player.lives <= 0:
                    self.game_state = "game_over"
                else:
                    levels = Level.get_level(self.current_level)
                    self.player.center_x, self.player.center_y = levels['player_start']
                    
        if self.player.top < 0:
            self.player.lives -= 1
            if self.player.lives <= 0:
                self.game_state = "game_over"
            else:
                levels = Level.get_level(self.current_level)
                self.player.center_x, self.player.center_y = levels['player_start']
        
        rubles_hit_list = arcade.check_for_collision_with_list(self.player, self.rubless)
        for rubles in rubles_hit_list:
            rubles.remove_from_sprite_lists()
            self.player.rubless += 1
            self.player.score += 10

        if arcade.check_for_collision(self.player, self.flag):
            self.complete_level()
        
        emitters_to_remove = []
        for emitter in self.emitters:
            emitter.update()
            if emitter.can_reap():
                emitters_to_remove.append(emitter)
        
        self.update_camera()
    
    def create_burst_explosion(self, x, y):
        colors = [
            arcade.color.RED,
            arcade.color.ORANGE_RED,
            arcade.color.ORANGE,
            arcade.color.YELLOW,
            arcade.color.WHITE
        ]
        
        for i, color in enumerate(colors):
            particle_count = 15 - i * 3

            emitter = arcade.particles.Emitter(
                center_xy=(x, y),
                emit_controller=arcade.particles.EmitBurst(particle_count),
                particle_factory=lambda emitter, col=color: arcade.particles.FadeParticle(
                    filename_or_texture=arcade.make_circle_texture(6 + i, col),
                    change_xy=(
                        random.uniform(-150, 150),
                        random.uniform(-150, 150)
                    ),
                    lifetime=random.uniform(0.3, 0.7),
                    scale=0.5 + i * 0.1,
                    start_alpha=150 + i * 20
                )
            )
            self.emitters.append(emitter)
    
    def update_camera(self):
        if not self.player or not self.camera:
            return
        
        target_center_x = self.player.center_x
        target_center_y = self.player.center_y

        current_center_x, current_center_y = self.camera.position

        new_center_x = current_center_x + (target_center_x - current_center_x) * CAMERA_SPEED
        new_center_y = current_center_y + (target_center_y - current_center_y) * CAMERA_SPEED

        self.camera.position = (new_center_x, new_center_y)
        
        self.camera.zoom = ZOOM_LEVEL
        
        
    def complete_level(self):
        self.game_state = "level_complete"
        self.level_completion_time = time.time() - self.level_start_time

        self.db.save_level_result(
            self.player_name,
            self.current_level,
            self.player.rubless,
            self.pmcs_defeated,
            self.level_completion_time,
            self.player.score
        )

        self.db.save_game(
            self.player_name,
            self.current_level + 1 if self.current_level < 3 else 3,
            self.player.rubless,
            self.player.score,
            self.player.lives
        )
    
    def on_key_press(self, key, modifiers):
        if self.game_state == "menu":
            if key == arcade.key.KEY_1:
                self.player = Player()
                self.player_name = "Игрок"
                self.setup_level(1)
                self.game_state = "playing"
            elif key == arcade.key.KEY_2:
                saved_game = self.db.load_game(self.player_name)
                if saved_game:
                    self.player = Player()
                    self.player.rubless = saved_game['rubless']
                    self.player.score = saved_game['score']
                    self.player.lives = saved_game['lives']
                    self.setup_level(saved_game['level'])
                    self.game_state = "playing"
            elif key == arcade.key.ESCAPE:
                arcade.close_window()
        
        elif self.game_state == "playing":
            if key == arcade.key.LEFT:
                self.player.change_x = -PLAYER_MOVE_SPEED
            elif key == arcade.key.RIGHT:
                self.player.change_x = PLAYER_MOVE_SPEED
            elif key == arcade.key.UP or key == arcade.key.SPACE:
                if self.physics_engine.can_jump():
                    self.player.change_y = PLAYER_JUMP_SPEED
            elif key == arcade.key.ESCAPE:
                self.db.save_game(
                    self.player_name,
                    self.current_level,
                    self.player.rubless,
                    self.player.score,
                    self.player.lives
                )
                self.game_state = "menu"
        
        elif self.game_state == "level_complete":
            if key == arcade.key.SPACE:
                if self.current_level < 3:
                    self.setup_level(self.current_level + 1)
                    self.game_state = "playing"
                else:
                    self.game_state = "menu"
            elif key == arcade.key.ESCAPE:
                self.game_state = "menu"
        
        elif self.game_state == "game_over":
            if key == arcade.key.SPACE:
                self.player = Player()
                self.setup_level(1)
                self.game_state = "playing"
            elif key == arcade.key.ESCAPE:
                self.game_state = "menu"
    
    def on_key_release(self, key, modifiers):
        if self.game_state == "playing":
            if key in (arcade.key.LEFT, arcade.key.RIGHT):
                self.player.change_x = 0
        
        arcade.run()