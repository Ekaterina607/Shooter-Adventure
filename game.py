import pygame
from pygame import mixer
import os
import random
import csv
import button


Enemy_group = pygame.sprite.Group()

bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
burst_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()
water_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()
chest_group = pygame.sprite.Group()


mixer.init()

pygame.mixer.music.load('audio/music2.wav')
pygame.mixer.music.set_volume(0.3)
pygame.mixer.music.play(-1, 0.0, 5000)
jump_fx = pygame.mixer.Sound('audio/jump.wav')
jump_fx.set_volume(0.05)
shot_fx = pygame.mixer.Sound('audio/shot.wav')
shot_fx.set_volume(0.05)
grenade_fx = pygame.mixer.Sound('audio/grenade.wav')
grenade_fx.set_volume(0.05)


BG = (144, 201, 120)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
PINK = (235, 65, 54)


def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))


def draw_bg():
    screen.fill(BG)
    width = mountain_img.get_width()
    for x in range(5):
        screen.blit(mountain_img, ((x * width) - bg_scroll * 0.5, 0))
        screen.blit(mountain_img, ((x * width) - bg_scroll * 0.6, SCREEN_HEIGHT - mountain_img.get_height() - 300))
        screen.blit(mountain_img, ((x * width) - bg_scroll * 0.7, SCREEN_HEIGHT - mountain_img.get_height() - 150))
        screen.blit(mountain_img, ((x * width) - bg_scroll * 0.8, SCREEN_HEIGHT - mountain_img.get_height()))


def reset_level():
    Enemy_group.empty()
    bullet_group.empty()
    grenade_group.empty()
    burst_group.empty()
    item_box_group.empty()
    decoration_group.empty()
    water_group.empty()
    exit_group.empty()
    chest_group.empty()

    # пустой список файлов
    data = []
    for row in range(ROWS):
        r = [-1] * COLS
        data.append(r)

    return data


class Player(pygame.sprite.Sprite):
    def __init__(self, skin, x, y, scale, speed, ammo, grenades):
        pygame.sprite.Sprite.__init__(self)
        self.alive = True
        self.skin = skin
        self.speed = speed
        self.ammo = ammo
        self.start_ammo = ammo
        self.shoot_cooldown = 0
        self.grenades = grenades
        self.health = 100
        self.max_health = self.health
        self.direction = 1
        self.vel_y = 0
        self.jump = False
        self.in_air = True
        self.flip = False
        self.animation_list = []
        self.frame_index = 0
        self.action = 0
        self.update_time = pygame.time.get_ticks()
        # иск интелект
        self.move_counter = 0
        self.vision = pygame.Rect(0, 0, 150, 20)
        self.idling = False
        self.idling_counter = 0

        # изображение для игрока
        animation_types = ['Idle', 'Run', 'Jump', 'Death']
        for animation in animation_types:
            temp_list = []
            num_of_frames = len(os.listdir(f'img/{self.skin}/{animation}'))
            for i in range(num_of_frames):
                img = pygame.image.load(f'img/{self.skin}/{animation}/{i}.png').convert_alpha()
                img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
                temp_list.append(img)
            self.animation_list.append(temp_list)

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def update(self):
        self.update_animation()
        self.check_alive()
        # перезарядка
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def move(self, move_left, move_right):
        screen_scroll = 0
        dx = 0
        dy = 0

        # move right/left
        if move_left:
            dx = -self.speed
            self.flip = True
            self.direction = -1
        if move_right:
            dx = self.speed
            self.flip = False
            self.direction = 1

        # jump
        if self.jump == True and self.in_air == False:
            self.vel_y = -11
            self.jump = False
            self.in_air = True

        # gravity
        self.vel_y += GRAVITY
        if self.vel_y > 10:
            self.vel_y
        dy += self.vel_y

        # столкновение
        for platform in world.obstacle_list:
            # столкновение по x
            if platform[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                dx = 0
                if self.skin == 'enemy':
                    self.direction *= -1
                    self.move_counter = 0
            # столкновение по y
            if platform[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                if self.vel_y < 0:
                    self.vel_y = 0
                    dy = platform[1].bottom - self.rect.top
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    self.in_air = False
                    dy = platform[1].top - self.rect.bottom

        # столкновение с водой
        if pygame.sprite.spritecollide(self, water_group, False):
            self.health = 0
            # print('dead')

        # столкновение с выходом, переход на следующий уровень
        level_complete = False
        if pygame.sprite.spritecollide(self, exit_group, False):
            level_complete = True

        chest = False
        if pygame.sprite.spritecollide(self, chest_group, False):
            chest = True


        # если игрок вне карты, то dead
        if self.rect.bottom > SCREEN_HEIGHT:
            self.health = 0

        # проверка изображения на выход из карты
        if self.skin == 'player':
            if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
                dx = 0

        self.rect.x += dx
        self.rect.y += dy

        if self.skin == 'player':
            if (self.rect.right > SCREEN_WIDTH - SCROLL_THRESH and bg_scroll < (
                    world.level_length * Platform_SIZE) - SCREEN_WIDTH) \
                    or (self.rect.left < SCROLL_THRESH and bg_scroll > abs(dx)):
                self.rect.x -= dx
                screen_scroll = -dx

        return screen_scroll, level_complete, chest

    def shoot(self):
        if self.shoot_cooldown == 0 and self.ammo > 0:
            self.shoot_cooldown = 20
            bullet = Bullet(self.rect.centerx + (0.75 * self.rect.size[0] * self.direction), self.rect.centery,
                            self.direction)
            bullet_group.add(bullet)
            # кол-во пуль(уменьшение)
            self.ammo -= 1
            shot_fx.play()

    def ai(self):
        if self.alive and player.alive:
            if self.idling == False and random.randint(1, 200) == 1:
                self.update_action(0)  # 0: idle
                self.idling = True
                self.idling_counter = 50
            # проверьте, находится ли ии рядом с игроком
            if self.vision.colliderect(player.rect):
                # поворт ии к игроку
                self.update_action(0)
                # выстрел
                self.shoot()
            else:
                if self.idling == False:
                    if self.direction == 1:
                        ai_move_right = True
                    else:
                        ai_move_right = False
                    ai_move_left = not ai_move_right
                    self.move(ai_move_left, ai_move_right)
                    self.update_action(1)  # 1: run
                    self.move_counter += 1
                    # обновление ИИ по мере продвижения врага
                    self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)

                    if self.move_counter > Platform_SIZE:
                        self.direction *= -1
                        self.move_counter *= -1
                else:
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling = False

        self.rect.x += screen_scroll

    def update_animation(self):  # обновление изображения
        ANIMATION_COOLDOWN = 100
        self.image = self.animation_list[self.action][self.frame_index]
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        if self.frame_index >= len(self.animation_list[self.action]):
            if self.action == 3:
                self.frame_index = len(self.animation_list[self.action]) - 1
            else:
                self.frame_index = 0

    def update_action(self, new_action):
        if new_action != self.action:
            self.action = new_action
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def check_alive(self):
        if self.health <= 0:
            self.health = 0
            self.speed = 0
            self.alive = False
            self.update_action(3)

    def draw(self):
        screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)


class World():
    def __init__(self):
        self.obstacle_list = []

    def process_data(self, data):
        self.level_length = len(data[0])
        for y, row in enumerate(data):
            for x, platform in enumerate(row):
                if platform >= 0:
                    img = img_list[platform]
                    img_rect = img.get_rect()
                    img_rect.x = x * Platform_SIZE
                    img_rect.y = y * Platform_SIZE
                    platform_data = (img, img_rect)
                    if platform >= 0 and platform <= 8:
                        self.obstacle_list.append(platform_data)
                    elif platform >= 9 and platform <= 10:
                        water = Water(img, x * Platform_SIZE, y * Platform_SIZE)
                        water_group.add(water)
                    elif platform >= 11 and platform <= 14:
                        decoration = Decoration(img, x * Platform_SIZE, y * Platform_SIZE)
                        decoration_group.add(decoration)
                    elif platform == 15:  # create player
                        player = Player('player', x * Platform_SIZE, y * Platform_SIZE, 3, 5, 20, 5)
                        health_bar = HealthBar(10, 10, player.health, player.health)
                    elif platform == 16:  # враги
                        enemy = Player('enemy', x * Platform_SIZE, y * Platform_SIZE, 3, 2, 20, 0)
                        Enemy_group.add(enemy)
                    elif platform == 21:  # враг slime
                        enemy_slime = Player('enemy_slime', x * Platform_SIZE, y * Platform_SIZE, 2, 1, 25, 0)
                        Enemy_group.add(enemy_slime)
                    elif platform == 17:  # коробка с боеприпасами
                        item_box = ItemBox('Ammo', x * Platform_SIZE, y * Platform_SIZE)
                        item_box_group.add(item_box)
                    elif platform == 18:  # create grenade box
                        item_box = ItemBox('Grenade', x * Platform_SIZE, y * Platform_SIZE)
                        item_box_group.add(item_box)
                    elif platform == 19:  # хилл
                        item_box = ItemBox('Health', x * Platform_SIZE, y * Platform_SIZE)
                        item_box_group.add(item_box)
                    elif platform == 20:  # выход
                        exit = Exit(img, x * Platform_SIZE, y * Platform_SIZE)
                        exit_group.add(exit)
                    elif platform == 23:  # сундук
                        chest = Chest(img, x * Platform_SIZE, y * Platform_SIZE)
                        chest_group.add(chest)

        return player, health_bar

    def draw(self):
        for platform in self.obstacle_list:
            platform[1][0] += screen_scroll
            screen.blit(platform[0], platform[1])


class Decoration(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + Platform_SIZE // 2, y + (Platform_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll


class Chest(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + Platform_SIZE // 2, y + (Platform_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll


class Water(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + Platform_SIZE // 2, y + (Platform_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll


class Exit(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + Platform_SIZE // 2, y + (Platform_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll


class ItemBox(pygame.sprite.Sprite):  # ящик с предметами
    def __init__(self, item_type, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.item_type = item_type
        self.image = item_boxes[self.item_type]
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + Platform_SIZE // 2, y + (Platform_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll
        # проверка на поднятие коробки
        if pygame.sprite.collide_rect(self, player):
            # какая коробка
            if self.item_type == 'Health':
                player.health += 25
                if player.health > player.max_health:
                    player.health = player.max_health
            elif self.item_type == 'Ammo':  # боеприпасы
                player.ammo += 15
            elif self.item_type == 'Grenade':
                player.grenades += 3
            # удаление коробки, после поднятия
            self.kill()


class HealthBar():
    def __init__(self, x, y, health, max_health):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = max_health

    def draw(self, health):
        self.health = health
        ratio = self.health / self.max_health
        pygame.draw.rect(screen, BLACK, (self.x - 2, self.y - 2, 155, 25))
        pygame.draw.rect(screen, RED, (self.x, self.y, 150, 20))
        pygame.draw.rect(screen, GREEN, (self.x, self.y, 150 * ratio, 20))


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 10
        self.image = bullet_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction

    def update(self):
        # движение пули
        self.rect.x += (self.direction * self.speed) + screen_scroll
        # проверка пули на экране
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()
        # столкновение пули с платформой
        for platform in world.obstacle_list:
            if platform[1].colliderect(self.rect):
                self.kill()

        if pygame.sprite.spritecollide(player, bullet_group, False):
            if player.alive:
                player.health -= 5
                self.kill()
        for enemy in Enemy_group:
            if pygame.sprite.spritecollide(enemy, bullet_group, False):
                if enemy.alive:
                    enemy.health -= 25  # 100
                    self.kill()


class Grenade(pygame.sprite.Sprite):   # граната
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.timer = 100
        self.vel_y = -11
        self.speed = 7
        self.image = grenade_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.direction = direction

    def update(self):
        self.vel_y += GRAVITY
        dx = self.direction * self.speed
        dy = self.vel_y

        for platform in world.obstacle_list:
            if platform[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                self.direction *= -1
                dx = self.direction * self.speed
            if platform[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                self.speed = 0
                if self.vel_y < 0:
                    self.vel_y = 0
                    dy = platform[1].bottom - self.rect.top
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    dy = platform[1].top - self.rect.bottom

        self.rect.x += dx + screen_scroll
        self.rect.y += dy

        # обратный отсчет
        self.timer -= 1
        if self.timer <= 0:
            self.kill()
            grenade_fx.play()
            burst = Burst(self.rect.x, self.rect.y, 0.5)
            burst_group.add(burst)
            # нанесение урона тем, кто находится рядом
            if abs(self.rect.centerx - player.rect.centerx) < Platform_SIZE * 2 and \
                    abs(self.rect.centery - player.rect.centery) < Platform_SIZE * 2:
                player.health -= 50
            for enemy in Enemy_group:
                if abs(self.rect.centerx - enemy.rect.centerx) < Platform_SIZE * 2 and \
                        abs(self.rect.centery - enemy.rect.centery) < Platform_SIZE * 2:
                    enemy.health -= 50


class Burst(pygame.sprite.Sprite):
    def __init__(self, x, y, scale):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        for num in range(1, 6):
            img = pygame.image.load(f'img/explosion/exp{num}.png').convert_alpha()
            img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
            self.images.append(img)
        self.frame_index = 0
        self.image = self.images[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.counter = 0

    def update(self):
        self.rect.x += screen_scroll

        burst_SPEED = 4
        self.counter += 1
        if self.counter >= burst_SPEED:
            self.counter = 0
            self.frame_index += 1
            if self.frame_index >= len(self.images):
                self.kill()
            else:
                self.image = self.images[self.frame_index]


class ScreenFade():
    def __init__(self, direction, colour, speed):
        self.direction = direction
        self.colour = colour
        self.speed = speed
        self.fade_counter = 0

    def fade(self):
        fade_complete = False
        self.fade_counter += self.speed
        if self.direction == 1:  # исчезновение экрана
            pygame.draw.rect(screen, self.colour, (0 - self.fade_counter, 0, SCREEN_WIDTH // 2, SCREEN_HEIGHT))
            pygame.draw.rect(screen, self.colour,
                             (SCREEN_WIDTH // 2 + self.fade_counter, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.draw.rect(screen, self.colour, (0, 0 - self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT // 2))
            pygame.draw.rect(screen, self.colour,
                             (0, SCREEN_HEIGHT // 2 + self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT))
        if self.direction == 2:  # вертикальный экран исчезает
            pygame.draw.rect(screen, self.colour, (0, 0, SCREEN_WIDTH, 0 + self.fade_counter))
        if self.fade_counter >= SCREEN_WIDTH:
            fade_complete = True

        return fade_complete


if __name__ == '__main__':
    mixer.init()
    pygame.init()

    font = pygame.font.SysFont('comicsansms', 17)

    SCREEN_WIDTH = 1500
    SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.7)

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('Shooter-Adventure')

    clock = pygame.time.Clock()
    FPS = 60

    GRAVITY = 0.35
    SCROLL_THRESH = 200
    ROWS = 16
    COLS = 150
    Platform_SIZE = SCREEN_HEIGHT // ROWS
    Platform_TYPES = 24
    MAX_LEVELS = 5
    screen_scroll = 0
    bg_scroll = 0
    level = 0
    start_game = False
    start_intro = False
    finish_intro = False

    img_list = []
    for x in range(Platform_TYPES):
        img = pygame.image.load(f'img/tile/{x}.png')
        img = pygame.transform.scale(img, (Platform_SIZE, Platform_SIZE))
        img_list.append(img)

    move_left = False
    move_right = False
    shoot = False
    grenade = False
    grenade_thrown = False

    start_img = pygame.image.load('img/start_btn.png').convert_alpha()
    exit_img = pygame.image.load('img/exit_btn.png').convert_alpha()
    restart_img = pygame.image.load('img/restart_btn.png').convert_alpha()
    mountain_img = pygame.image.load('img/Background/back3.png').convert_alpha()
    game_ov_img = pygame.image.load('img/Background/game_ov.png').convert_alpha()

    bullet_img = pygame.image.load('img/icons/bullet2.png').convert_alpha()
    grenade_img = pygame.image.load('img/icons/grenade.png').convert_alpha()
    health_box_img = pygame.image.load('img/icons/health_box.png').convert_alpha()
    ammo_box_img = pygame.image.load('img/icons/ammo_box.png').convert_alpha()
    grenade_box_img = pygame.image.load('img/icons/grenade_box.png').convert_alpha()
    item_boxes = {
        'Health': health_box_img,
        'Ammo': ammo_box_img,
        'Grenade': grenade_box_img
    }

    # Затухание экрана
    intro_fade = ScreenFade(1, BLACK, 5)
    death_fade = ScreenFade(2, PINK, 5)

    # Кнопки
    start_button = button.Button(SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 - 150, start_img, 1)
    exit_button = button.Button(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 50, exit_img, 1)
    restart_button = button.Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50, restart_img, 2)

    # Платформы
    world_map = []
    for row in range(ROWS):
        r = [-1] * COLS
        world_map.append(r)
    # Загрузить данные об уровне и создать мир
    with open(f'level{level}_data.csv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for x, row in enumerate(reader):
            for y, platform in enumerate(row):
                world_map[x][y] = int(platform)
    world = World()
    player, health_bar = world.process_data(world_map)

    run = True
    while run:
        clock.tick(FPS)
        if start_game == False:
            screen.fill(BG)
            if start_button.draw(screen):
                start_game = True
                start_intro = True
            if exit_button.draw(screen):
                finish_intro = True
                run = False
        else:
            draw_bg()
            world.draw()
            health_bar.draw(player.health)
            draw_text('AMMO: ', font, WHITE, 10, 35)
            for x in range(player.ammo):
                screen.blit(bullet_img, (90 + (x * 10), 40))
            draw_text('GRENADES: ', font, WHITE, 10, 60)
            for x in range(player.grenades):
                screen.blit(grenade_img, (135 + (x * 15), 60))

            player.update()
            player.draw()

            for enemy in Enemy_group:  # прорисовка врагов
                enemy.ai()
                enemy.update()
                enemy.draw()

            bullet_group.update()
            grenade_group.update()
            burst_group.update()
            item_box_group.update()
            decoration_group.update()
            water_group.update()
            exit_group.update()
            bullet_group.draw(screen)
            grenade_group.draw(screen)
            burst_group.draw(screen)
            item_box_group.draw(screen)
            decoration_group.draw(screen)
            water_group.draw(screen)
            exit_group.draw(screen)
            chest_group.draw(screen)
            chest_group.update()

            # показать вступление
            if start_intro == True:
                if intro_fade.fade():
                    start_intro = False
                    intro_fade.fade_counter = 0

            if player.alive:
                if shoot:
                    player.shoot()
                elif grenade and grenade_thrown == False and player.grenades > 0:
                    grenade = Grenade(player.rect.centerx + (0.5 * player.rect.size[0] * player.direction), \
                                      player.rect.top, player.direction)
                    grenade_group.add(grenade)
                    player.grenades -= 1
                    grenade_thrown = True
                if player.in_air:
                    player.update_action(2)
                elif move_left or move_right:
                    player.update_action(1)
                else:
                    player.update_action(0)
                screen_scroll, level_complete, chest = player.move(move_left, move_right)
                bg_scroll -= screen_scroll
                # завершение игры(сундук)
                if chest:
                    screen.fill(BG)
                    width = game_ov_img.get_width()
                    for x in range(5):
                        screen.blit(game_ov_img, ((x * width) - bg_scroll * 0.5, 0))
                        screen.blit(game_ov_img,
                                    ((x * width) - bg_scroll * 0.6, SCREEN_HEIGHT - game_ov_img.get_height() - 300))
                        screen.blit(game_ov_img,
                                    ((x * width) - bg_scroll * 0.7, SCREEN_HEIGHT - game_ov_img.get_height() - 150))
                        screen.blit(game_ov_img,
                                    ((x * width) - bg_scroll * 0.8, SCREEN_HEIGHT - game_ov_img.get_height()))
                    if exit_button.draw(screen):
                        finish_intro = True
                        run = False
                # прошел ли игрок уровень
                if level_complete:  # табличка
                    start_intro = True
                    level += 1
                    bg_scroll = 0
                    world_map = reset_level()
                    if level <= MAX_LEVELS:
                        # загрузка мира
                        with open(f'level{level}_data.csv', newline='') as csvfile:
                            reader = csv.reader(csvfile, delimiter=',')
                            for x, row in enumerate(reader):
                                for y, platform in enumerate(row):
                                    world_map[x][y] = int(platform)
                        world = World()
                        player, health_bar = world.process_data(world_map)
            else:
                screen_scroll = 0
                if death_fade.fade():
                    if restart_button.draw(screen):
                        death_fade.fade_counter = 0
                        start_intro = True
                        bg_scroll = 0
                        world_map = reset_level()
                        with open(f'level{level}_data.csv', newline='') as csvfile:
                            reader = csv.reader(csvfile, delimiter=',')
                            for x, row in enumerate(reader):
                                for y, platform in enumerate(row):
                                    world_map[x][y] = int(platform)
                        world = World()
                        player, health_bar = world.process_data(world_map)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:
                    move_left = True
                if event.key == pygame.K_d:
                    move_right = True
                if event.key == pygame.K_w:
                    shoot = True
                if event.key == pygame.K_q:
                    grenade = True
                if event.key == pygame.K_SPACE and player.alive:
                    player.jump = True
                    jump_fx.play()
                if event.key == pygame.K_ESCAPE:
                    run = False

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_a:
                    move_left = False
                if event.key == pygame.K_d:
                    move_right = False
                if event.key == pygame.K_w:
                    shoot = False
                if event.key == pygame.K_q:
                    grenade = False
                    grenade_thrown = False
        pygame.display.update()

    pygame.quit()