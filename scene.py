import pygame
import sys
import random
import math

from card_hub import DeckManager, NORMAL_CARDS, LEVEL0_ENEMY_CARD, CardUpgradeManager
from environment import CleanEnvironment, BattleEnvironment
from utils import (
    WaterEntity, FireEntity, WoodEntity, EarthEntity, MetalEntity,
    StaticAbility, NourishAbility
)
SCREEN_W, SCREEN_H = 1280, 720
FPS = 60

# 卡牌尺寸（360:640 ≈ 9:16，放大一倍）
CARD_W, CARD_H = 180, 320
CARD_GAP = 15
ENEMY_CARD_W, ENEMY_CARD_H = 60, 107
ENEMY_CARD_GAP = 10

# 扑克牌图片尺寸（随卡牌放大一倍）
POKER_W, POKER_H = 44, 60

# 颜色
C_PANEL = (20, 40, 20)
C_WHITE = (240, 240, 240)
C_BLACK = (30, 30, 30)
C_GOLD = (220, 180, 50)
C_RED = (200, 50, 50)
C_GREEN = (50, 180, 80)
C_BLUE = (60, 120, 200)
C_GRAY = (120, 120, 120)

CARD_TYPE_COLORS = {
    "Attack": (220, 80, 60),
    "Shield": (80, 140, 200),
    "Buff": (200, 180, 60),
    "Heal": (60, 180, 100),
    "Poison": (140, 60, 180),
    "Dispel": (180, 120, 60),
    "ChangeEnv": (100, 180, 180),
}

POKER_ORDER = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']

# 游戏状态
STATE_CHAR_SELECT = "char_select"
STATE_CARD_CHOICE = "card_choice"
STATE_UPGRADE = "upgrade"
STATE_GAME_OVER = "game_over"
STATE_POKER_COMPARE = "poker_compare"
# 角色选项定义
CHAR_OPTIONS = [
    {"name": "金", "cls": MetalEntity, "hp": 300, "atk": 50, "def": 20,
     "desc": "高攻高防，锐利2层（无视30%防御）", "ability": "无专属技能",
     "color": (220, 200, 80)},
    {"name": "木", "cls": WoodEntity, "hp": 300, "atk": 50, "def": 20,
     "desc": "高防御，回合恢复", "ability": "静止：双方跳过出牌，恢复30%HP",
     "color": (80, 200, 100)},
    {"name": "水", "cls": WaterEntity, "hp": 300, "atk": 50, "def": 20,
     "desc": "攻防均衡，闪避10%", "ability": "塑形：每2回合复制对方状态",
     "color": (80, 160, 240)},
    {"name": "火", "cls": FireEntity, "hp": 300, "atk": 50, "def": 20,
     "desc": "高攻击，闪避20%", "ability": "光明：双方手牌互相可见",
     "color": (240, 80, 50)},
    {"name": "土", "cls": EarthEntity, "hp": 300, "atk": 50, "def": 20,
     "desc": "初始3层护盾", "ability": "滋养：每回合结束自动升级一张手牌",
     "color": (180, 140, 80)},
]


class DamageNumber:
    """飘字动画：数字从小变大再消失"""
    def __init__(self, text, x, y, color=(255, 60, 60)):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.duration = 1.0
        self.elapsed = 0.0

    @property
    def done(self):
        return self.elapsed >= self.duration

    @property
    def alpha(self):
        # 前 0.6 秒可见，后 0.4 秒淡出
        if self.elapsed < 0.6:
            return 255
        return int(255 * (1 - (self.elapsed - 0.6) / 0.4))

    @property
    def scale(self):
        # 0~0.15s 从小到大，0.15~0.6s 保持，0.6~1s 缩小消失
        t = self.elapsed
        if t < 0.15:
            return 0.3 + 0.7 * (t / 0.15)
        elif t < 0.6:
            return 1.0
        else:
            return 1.0 * (1 - (t - 0.6) / 0.4)

    @property
    def offset_y(self):
        # 向上飘动
        return -60 * (self.elapsed / self.duration)


class CardAnimation:
    """单张卡牌的位移+旋转动画"""
    def __init__(self, card, start_pos, end_pos, duration, on_complete=None,
                 start_rotation=0.0, end_rotation=0.0):
        self.card = card
        self.start_pos = start_pos  # (x, y) 左上角
        self.end_pos = end_pos      # (x, y) 左上角
        self.start_rotation = start_rotation  # 起始旋转角度
        self.end_rotation = end_rotation      # 结束旋转角度
        self.duration = duration    # 秒
        self.elapsed = 0.0
        self.on_complete = on_complete  # 回调函数

    @property
    def done(self):
        return self.elapsed >= self.duration

    @property
    def progress(self):
        return min(1.0, self.elapsed / self.duration) if self.duration > 0 else 1.0

    @property
    def pos(self):
        # ease-out 插值
        t = self.progress
        t = 1 - (1 - t) ** 2  # quadratic ease-out
        x = self.start_pos[0] + (self.end_pos[0] - self.start_pos[0]) * t
        y = self.start_pos[1] + (self.end_pos[1] - self.start_pos[1]) * t
        return (x, y)

    @property
    def rotation(self):
        t = self.progress
        t = 1 - (1 - t) ** 2
        return self.start_rotation + (self.end_rotation - self.start_rotation) * t


class Scene:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("卡牌对战")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("microsoftyahei", 18)
        self.font_sm = pygame.font.SysFont("microsoftyahei", 14)
        self.font_lg = pygame.font.SysFont("microsoftyahei", 24, bold=True)
        self.font_xl = pygame.font.SysFont("microsoftyahei", 32, bold=True)

        # ---------- 加载素材 ----------
        self.bg_image = pygame.image.load("assessment/field.png").convert()
        self.bg_image = pygame.transform.scale(self.bg_image, (SCREEN_W, SCREEN_H))

        # 卡面图片（360x640 原图，按 9:16 缩放到 CARD_W x CARD_H）
        self.card_faces = {}
        face_map = {
            "attack_low":  "assessment/attack_low.jpg",
            "attack_mid":  "assessment/attack_mid.jpg",
            "attack_high": "assessment/attack_high.jpg",
            "attack_double": "assessment/attack_double.png",
            "shield_1":    "assessment/shield_1.jpg",
            "attack_up_1": "assessment/attack_up_1.png",
            "defense_up_1":"assessment/defense_up_1.png",
        }
        for key, path in face_map.items():
            img = pygame.image.load(path).convert_alpha()
            self.card_faces[key] = pygame.transform.scale(img, (CARD_W, CARD_H))

        # 扑克牌数字图片 (A-K)
        self.poker_imgs = {}
        for val in POKER_ORDER:
            path = f"assessment/Poker_Value/{val}.png"
            img = pygame.image.load(path).convert_alpha()
            self.poker_imgs[val] = pygame.transform.scale(img, (POKER_W, POKER_H))

        # 默认卡面（无匹配时用）
        self.default_face = pygame.Surface((CARD_W, CARD_H))
        self.default_face.fill((180, 180, 180))

        # 元素升级叠加素材
        self.element_overlays = {}
        element_overlay_map = {
            "metal": "assessment/element_card_plus/element_metal.png",
            "wood":  "assessment/element_card_plus/element_wood.png",
            "water": "assessment/element_card_plus/element_water.png",
            "fire":  "assessment/element_card_plus/element_fire.png",
            "earth": "assessment/element_card_plus/element_earth.png",
        }
        for elem, path in element_overlay_map.items():
            img = pygame.image.load(path).convert_alpha()
            self.element_overlays[elem] = pygame.transform.scale(img, (CARD_W, CARD_H))

        # ---------- 初始化游戏（角色选择界面） ----------
        self.arena = None
        self.player = None
        self.enemy = None
        self.player_deck = []
        self.enemy_deck = []

        self.round = 1
        self.state = STATE_CHAR_SELECT
        self.log_lines = []
        self.selected_card_idx = -1
        self.hovered_card_idx = -1
        self.game_over_msg = ""
        self.char_hovered = -1
        self.animations = []  # 动画队列
        self.animating_cards = set()  # 正在动画中的卡牌，不参与手牌渲染
        self.damage_numbers = []  # 飘字动画

        # 扑克对比状态
        self._compare_player_card = None
        self._compare_enemy_card = None
        self._compare_result = None  # "player" / "enemy" / "tie"
        self._compare_timer = 0.0

    # ----------------------------------------------------------
    # 角色选择
    # ----------------------------------------------------------
    def start_game(self, player_idx):
        """根据选择的角色初始化对局"""
        p_opt = CHAR_OPTIONS[player_idx]
        self.player = p_opt["cls"](p_opt["name"], max_hp=p_opt["hp"], atk=p_opt["atk"], defense=p_opt["def"])

        # 敌人随机选一个不同属性
        enemy_options = [i for i in range(len(CHAR_OPTIONS)) if i != player_idx]
        e_idx = random.choice(enemy_options)
        e_opt = CHAR_OPTIONS[e_idx]
        self.enemy = e_opt["cls"](e_opt["name"], max_hp=e_opt["hp"], atk=e_opt["atk"], defense=e_opt["def"])

        self.arena = BattleEnvironment()
        self.player_deck = DeckManager.get_cards_from_deck(NORMAL_CARDS, 5)
        self.enemy_deck = DeckManager.get_cards_from_deck(LEVEL0_ENEMY_CARD, 3)
        self.round = 1
        self.log_lines = []
        self.selected_card_idx = -1
        self.game_over_msg = ""
        self.log(f"⚔️ 你选择了【{p_opt['name']}】，对手是【{e_opt['name']}】！")
        self.start_turn()

    def draw_text_wrapped(self, text, x, y, max_width, font=None, color=C_WHITE, line_height=24):
        """自动换行绘制中文文本，返回总行数"""
        font = font or self.font_sm
        lines = []
        current = ""
        for ch in text:
            test = current + ch
            if font.size(test)[0] > max_width:
                lines.append(current)
                current = ch
            else:
                current = test
        if current:
            lines.append(current)
        for i, line in enumerate(lines):
            self.draw_text(line, x, y + i * line_height, font, color)
        return len(lines)

    def draw_char_select(self):
        """绘制角色选择界面"""
        # 标题
        self.draw_text("选择你的角色", SCREEN_W // 2, 40, self.font_xl, C_GOLD, center=True)
        self.draw_text("点击卡片或按数字键 1-5 选择", SCREEN_W // 2, 80, self.font, C_GRAY, center=True)

        # 5 个角色卡片
        card_w, card_h = 210, 560
        gap = 16
        total_w = card_w * 5 + gap * 4
        start_x = (SCREEN_W - total_w) // 2
        start_y = 110

        for i, opt in enumerate(CHAR_OPTIONS):
            cx = start_x + i * (card_w + gap)
            cy = start_y

            is_hovered = i == self.char_hovered
            if is_hovered:
                cy -= 8

            # 卡片背景
            panel_color = (opt["color"][0] // 4, opt["color"][1] // 4, opt["color"][2] // 4)
            self.draw_panel(cx, cy, card_w, card_h, panel_color)

            # 边框
            border_color = C_GOLD if is_hovered else opt["color"]
            border_w = 3 if is_hovered else 2
            pygame.draw.rect(self.screen, border_color, (cx, cy, card_w, card_h), border_w, border_radius=8)

            # 编号
            self.draw_text(f"[{i + 1}]", cx + 10, cy + 10, self.font, C_GRAY)

            # 元素名称（大字）
            self.draw_text(opt["name"], cx + card_w // 2, cy + 50, self.font_xl, opt["color"], center=True)

            # 横线分隔
            pygame.draw.line(self.screen, opt["color"], (cx + 15, cy + 80), (cx + card_w - 15, cy + 80), 1)

            # 属性
            y = cy + 95
            self.draw_text(f"HP:  {opt['hp']}", cx + 20, y, self.font, C_GREEN)
            self.draw_text(f"ATK: {opt['atk']}", cx + 20, y + 28, self.font, C_RED)
            self.draw_text(f"DEF: {opt['def']}", cx + 20, y + 56, self.font, C_BLUE)

            # 横线分隔
            y2 = y + 95
            pygame.draw.line(self.screen, opt["color"], (cx + 15, y2), (cx + card_w - 15, y2), 1)

            # 特性描述
            y3 = y2 + 12
            self.draw_text("特性", cx + 20, y3, self.font, C_GOLD)
            n = self.draw_text_wrapped(opt["desc"], cx + 20, y3 + 26, card_w - 40, self.font, C_WHITE, 24)

            # 横线分隔
            y4 = y3 + 26 + n * 24 + 10
            pygame.draw.line(self.screen, opt["color"], (cx + 15, y4), (cx + card_w - 15, y4), 1)

            # 专属技能
            y5 = y4 + 12
            self.draw_text("专属技能", cx + 20, y5, self.font, C_GOLD)
            self.draw_text_wrapped(opt["ability"], cx + 20, y5 + 26, card_w - 40, self.font, C_WHITE, 24)

    # ----------------------------------------------------------
    # 卡面映射：根据卡牌 skill 选择对应图片
    # ----------------------------------------------------------
    def get_card_face(self, card):
        """根据卡牌的主要技能返回对应的卡面图片"""
        # 取第一个 skill 判断类型
        primary = card.skills[0]

        if primary.skill_type == "attack":
            # 连击牌
            if primary.num >= 2:
                return self.card_faces.get("attack_double", self.default_face)
            # 按威力分级
            if primary.power >= 2.0:
                return self.card_faces.get("attack_high", self.default_face)
            elif primary.power >= 1.2:
                return self.card_faces.get("attack_mid", self.default_face)
            else:
                return self.card_faces.get("attack_low", self.default_face)

        elif primary.skill_type == "shield":
            return self.card_faces.get("shield_1", self.default_face)

        elif primary.skill_type == "buff":
            if primary.status_target == "atk_boost":
                return self.card_faces.get("attack_up_1", self.default_face)
            elif primary.status_target == "def_boost":
                return self.card_faces.get("defense_up_1", self.default_face)

        # 多技能卡：按第一个 skill 匹配，fallback 到默认
        return self.card_faces.get("attack_low", self.default_face)

    # ----------------------------------------------------------
    # 日志
    # ----------------------------------------------------------
    def log(self, msg):
        self.log_lines.append(msg)
        if len(self.log_lines) > 8:
            self.log_lines.pop(0)

    # ----------------------------------------------------------
    # 绘制工具
    # ----------------------------------------------------------
    def draw_text(self, text, x, y, font=None, color=C_WHITE, center=False):
        font = font or self.font
        surf = font.render(str(text), True, color)
        rect = surf.get_rect()
        if center:
            rect.center = (x, y)
        else:
            rect.topleft = (x, y)
        self.screen.blit(surf, rect)
        return rect

    def draw_bar(self, x, y, w, h, ratio, fg=C_GREEN, bg=C_RED):
        ratio = max(0, min(1, ratio))
        pygame.draw.rect(self.screen, bg, (x, y, w, h))
        pygame.draw.rect(self.screen, fg, (x, y, int(w * ratio), h))
        pygame.draw.rect(self.screen, C_WHITE, (x, y, w, h), 1)

    def draw_panel(self, x, y, w, h, color=C_PANEL):
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.fill((*color, 180))
        self.screen.blit(surf, (x, y))
        pygame.draw.rect(self.screen, C_WHITE, (x, y, w, h), 1, border_radius=8)

    # ----------------------------------------------------------
    # 绘制扑克牌数字（左上 + 右下中心对称）
    # ----------------------------------------------------------
    def draw_poker_value(self, cx, cy, poker_value):
        """在卡牌左上角和右下角绘制扑克数字，右下旋转180度"""
        if not poker_value or poker_value not in self.poker_imgs:
            return

        img = self.poker_imgs[poker_value]
        # 左上角
        self.screen.blit(img, (cx + 3, cy + 3))
        # 右下角（旋转180度）
        img_rot = pygame.transform.rotate(img, 180)
        self.screen.blit(img_rot, (cx + CARD_W - POKER_W - 3, cy + CARD_H - POKER_H - 3))

    # ----------------------------------------------------------
    # 绘制实体信息
    # ----------------------------------------------------------
    def draw_entity(self, entity, x, y, is_player=False):
        name_color = C_GOLD if is_player else C_RED
        self.draw_text(f"{'🧑' if is_player else '👹'} {entity.name} ({entity.element})", x, y, self.font_lg, name_color)

        hp_ratio = entity.hp / entity.max_hp
        self.draw_bar(x, y + 32, 200, 18, hp_ratio)
        self.draw_text(f"HP: {entity.hp}/{entity.max_hp}", x + 5, y + 33, self.font_sm, C_BLACK)

        self.draw_text(f"🛡️ 护盾: {entity.shield}", x + 210, y + 33, self.font_sm, C_WHITE)

        statuses = []
        for key, status in entity.statuses.items():
            if hasattr(status, 'level') and status.level > 0:
                statuses.append(f"{status.name}:{status.level}")
        status_text = " | ".join(statuses) if statuses else "无状态"
        self.draw_text(f"状态: {status_text}", x, y + 56, self.font_sm, C_GRAY)

        ability = entity.ability
        cd_text = ""
        if isinstance(ability, StaticAbility) and ability.current_cd > 0:
            cd_text = f" (CD:{ability.current_cd})"
        self.draw_text(f"专属: {ability.name}{cd_text}", x, y + 76, self.font_sm, C_GOLD)

    # ----------------------------------------------------------
    # 绘制卡牌（通用：支持旋转 + 缩放，以底边中心为锚点）
    # ----------------------------------------------------------
    def draw_card_at(self, card, anchor_x, anchor_y, scale=1.0, rotation=0.0, highlight=None, force=False):
        """以 (anchor_x, anchor_y) 为卡牌底边中心绘制，所有元素整体旋转"""
        if not force and card in self.animating_cards:
            return
        w = int(CARD_W * scale)
        h = int(CARD_H * scale)
        s = scale

        # 在卡牌表面上合成所有元素
        face = self.get_card_face(card)
        surface = pygame.transform.scale(face, (w, h))

        # 元素叠加素材
        if card.level > 0 and self.player and self.player.element in self.element_overlays:
            ov = pygame.transform.scale(self.element_overlays[self.player.element], (w, h))
            surface.blit(ov, (0, 0))

        # 等级标记
        if card.level > 0:
            lv_size = max(10, int(14 * s))
            lv_font = pygame.font.SysFont("microsoftyahei", lv_size)
            lv_surf = lv_font.render(f"Lv.{card.level}", True, C_GOLD)
            surface.blit(lv_surf, (w - lv_surf.get_width() - int(4 * s), int(2 * s)))

        # 扑克数字（左上 + 右下中心对称）
        pv_w = int(POKER_W * s)
        pv_h = int(POKER_H * s)
        if card.poker_value and card.poker_value in self.poker_imgs:
            pv_img = pygame.transform.scale(self.poker_imgs[card.poker_value], (pv_w, pv_h))
            # 左上角
            surface.blit(pv_img, (int(3 * s), int(3 * s)))
            # 右下角（180度旋转）
            pv_rot = pygame.transform.rotate(pv_img, 180)
            surface.blit(pv_rot, (w - pv_rot.get_width() - int(3 * s),
                                   h - pv_rot.get_height() - int(3 * s)))

        # 卡牌名称（底部居中）
        name_size = max(10, int(14 * s))
        name_font = pygame.font.SysFont("microsoftyahei", name_size)
        name_surf = name_font.render(card.name, True, C_WHITE)
        name_rect = name_surf.get_rect(centerx=w // 2, bottom=h - int(5 * s))
        bg = pygame.Surface((name_rect.width + int(8 * s), name_rect.height + int(2 * s)), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 140))
        surface.blit(bg, (name_rect.x - int(4 * s), name_rect.y - 1))
        surface.blit(name_surf, name_rect)

        # 金色选中边框
        if highlight == "gold":
            pygame.draw.rect(surface, C_GOLD, (0, 0, w, h), 3)

        # 整体旋转
        if rotation != 0:
            surface = pygame.transform.rotate(surface, rotation)

        # 以底边中心为锚点定位
        rw, rh = surface.get_size()
        draw_x = anchor_x - rw // 2
        draw_y = anchor_y - rh
        self.screen.blit(surface, (draw_x, draw_y))

    # ----------------------------------------------------------
    # 绘制玩家手牌（双圆弧扇形握持）
    # ----------------------------------------------------------
    def draw_fan_hand(self, cards, fan_cx, fan_cy, fan_radius, fan_scale, total_angle):
        """底边沿小圆弧（fan_radius）聚拢，卡牌向外倾斜形成扇形"""
        n = len(cards)
        if n == 0:
            return
        hovered = self.hovered_card_idx

        for i, card in enumerate(cards):
            if card in self.animating_cards:
                continue
            if n == 1:
                angle = 0
            else:
                angle = total_angle / 2 - i * (total_angle / (n - 1))

            is_hovered = i == hovered
            sc = 1.0 if is_hovered else fan_scale
            lift = -40 if is_hovered else 0

            # 底边锚点沿小圆弧分布
            anchor_x = int(fan_cx + fan_radius * math.sin(math.radians(-angle)))
            anchor_y = int(fan_cy - fan_radius * math.cos(math.radians(-angle)) + lift)

            highlight = "gold" if i == self.selected_card_idx else None
            self.draw_card_at(card, anchor_x, anchor_y, scale=sc, rotation=angle, highlight=highlight)

    def get_fanchard_at_pos(self, mx, my, cards, fan_cx, fan_cy, fan_radius, fan_scale, total_angle):
        """扇形手牌碰撞检测（鼠标到卡牌中心距离，优先选上层卡）"""
        n = len(cards)
        if n == 0:
            return -1

        best_idx = -1
        best_dist = float('inf')

        for i in range(n - 1, -1, -1):
            if n == 1:
                angle = 0
            else:
                angle = total_angle / 2 - i * (total_angle / (n - 1))
            # 锚点（底边中心）
            ax = fan_cx + fan_radius * math.sin(math.radians(-angle))
            ay = fan_cy - fan_radius * math.cos(math.radians(-angle))
            # 卡牌中心 = 锚点上移半张卡高度
            ch = CARD_H * fan_scale
            ccx = ax
            ccy = ay - ch / 2
            # 鼠标到卡牌中心距离
            dx = mx - ccx
            dy = my - ccy
            dist = math.sqrt(dx * dx + dy * dy)
            # 在卡牌尺寸范围内才算命中
            hit_radius = max(CARD_W, CARD_H) * fan_scale / 2
            if dist < hit_radius and dist < best_dist:
                best_dist = dist
                best_idx = i

        return best_idx

    # ----------------------------------------------------------
    # 绘制玩家手牌（网格布局，用于升级等状态）
    # ----------------------------------------------------------
    def draw_hand(self, cards, x, y):
        for i, card in enumerate(cards):
            if card in self.animating_cards:
                continue
            cx = x + i * (CARD_W + CARD_GAP) + CARD_W // 2
            cy = y + CARD_H
            highlight = "gold" if i == self.selected_card_idx else None
            self.draw_card_at(card, cx, cy, scale=1.0, rotation=0.0, highlight=highlight)

    # ----------------------------------------------------------
    # 绘制敌人手牌（背面，see_all 时正面）
    # ----------------------------------------------------------
    def draw_enemy_hand(self, cards, x, y):
        for i, card in enumerate(cards):
            cx = x + i * (ENEMY_CARD_W + ENEMY_CARD_GAP)

            if self.arena.see_all:
                # 正面：缩放卡面
                face = self.get_card_face(card)
                face_small = pygame.transform.scale(face, (ENEMY_CARD_W, ENEMY_CARD_H))
                self.screen.blit(face_small, (cx, y))
            else:
                # 背面
                pygame.draw.rect(self.screen, (80, 40, 40), (cx, y, ENEMY_CARD_W, ENEMY_CARD_H), border_radius=4)
                pygame.draw.rect(self.screen, C_RED, (cx, y, ENEMY_CARD_W, ENEMY_CARD_H), 2, border_radius=4)
                self.draw_text("?", cx + ENEMY_CARD_W // 2, y + ENEMY_CARD_H // 2, self.font_lg, C_RED, center=True)

    # ----------------------------------------------------------
    # 绘制环境信息
    # ----------------------------------------------------------
    def draw_environment(self, x, y):
        weather = self.arena.current_weather
        self.draw_panel(x, y, 250, 60)
        self.draw_text(f"🌍 环境: {weather.name}", x + 10, y + 8, self.font, C_GOLD)
        if not weather.is_permanent:
            self.draw_text(f"剩余 {weather.duration} 回合", x + 10, y + 32, self.font_sm, C_GRAY)
        else:
            self.draw_text("永久", x + 10, y + 32, self.font_sm, C_GRAY)

    # ----------------------------------------------------------
    # 绘制战斗日志
    # ----------------------------------------------------------
    def draw_log(self, x, y, w, h):
        self.draw_panel(x, y, w, h)
        self.draw_text("战斗日志", x + 10, y + 5, self.font_sm, C_GOLD)
        for i, line in enumerate(self.log_lines):
            if y + 25 + i * 18 < y + h - 5:
                self.draw_text(line, x + 10, y + 25 + i * 18, self.font_sm, C_WHITE)

    # ----------------------------------------------------------
    # 绘制操作提示
    # ----------------------------------------------------------
    def draw_hints(self, x, y):
        if self.state == STATE_CARD_CHOICE:
            self.draw_text("点击卡牌出牌 | 数字键1-5快速选牌 | A发动专属技能", x, y, self.font_sm, C_GOLD)
        elif self.state == STATE_UPGRADE:
            self.draw_text("点击卡牌进行升级 | 数字键1-5选择", x, y, self.font_sm, C_GOLD)
        elif self.state == STATE_GAME_OVER:
            self.draw_text("R: 重新开始 | ESC: 退出", x, y, self.font_sm, C_GOLD)

    # ----------------------------------------------------------
    # 卡牌碰撞检测
    # ----------------------------------------------------------
    def get_card_at_pos(self, mx, my, cards, x, y, cw=CARD_W, ch=CARD_H, gap=CARD_GAP):
        for i in range(len(cards)):
            cx = x + i * (cw + gap)
            if cx <= mx <= cx + cw and y <= my <= y + ch:
                return i
        return -1

    # ----------------------------------------------------------
    # 动画系统
    # ----------------------------------------------------------
    def get_card_screen_pos(self, card_idx, hand_x, hand_y):
        """获取手牌中第 idx 张卡的屏幕坐标"""
        return (hand_x + card_idx * (CARD_W + CARD_GAP), hand_y)

    def get_deck_pos(self, is_player=True):
        """牌库/摸牌起始位置（屏幕右侧外）"""
        if is_player:
            return (SCREEN_W + 10, 450)
        return (SCREEN_W + 10, 50)

    def queue_play_anim(self, card_idx, card, on_complete=None):
        """出牌动画：从扇形手牌位置飞到屏幕中央（带旋转），动画期间从手牌渲染中隐藏"""
        self.animating_cards.add(card)

        # 计算卡牌在扇形中的位置和角度
        n = len(self.player_deck)
        if n <= 1:
            angle = 0
        else:
            angle = self._fan_total_angle / 2 - card_idx * (self._fan_total_angle / (n - 1))

        # 锚点（底边中心）
        anchor_x = int(self._fan_cx + self._fan_radius * math.sin(math.radians(-angle)))
        anchor_y = int(self._fan_cy - self._fan_radius * math.cos(math.radians(-angle)))

        # 转为左上角坐标（用于动画插值）
        start_x = anchor_x - CARD_W // 2
        start_y = anchor_y - CARD_H

        # 飞到屏幕中央
        end_x = SCREEN_W // 2 - CARD_W // 2
        end_y = SCREEN_H // 2 - CARD_H // 2

        anim = CardAnimation(card, (start_x, start_y), (end_x, end_y), 0.35,
                             on_complete=on_complete,
                             start_rotation=angle, end_rotation=0.0)
        self.animations.append(anim)

    def queue_draw_anim(self, card, target_idx, hand_x, hand_y, on_complete=None):
        """摸牌动画：从屏幕右侧飞入扇形手牌末尾（带旋转），动画期间不加入手牌"""
        self.animating_cards.add(card)
        start = self.get_deck_pos(is_player=True)

        # 计算新牌在扇形中的目标位置（加入后的索引）
        n = target_idx + 1  # 加入后手牌总数
        if n <= 1:
            angle = 0
        else:
            angle = self._fan_total_angle / 2 - target_idx * (self._fan_total_angle / (n - 1))

        anchor_x = int(self._fan_cx + self._fan_radius * math.sin(math.radians(-angle)))
        anchor_y = int(self._fan_cy - self._fan_radius * math.cos(math.radians(-angle)))

        # 转为左上角
        end_x = anchor_x - CARD_W // 2
        end_y = anchor_y - CARD_H

        anim = CardAnimation(card, start, (end_x, end_y), 0.4,
                             on_complete=on_complete,
                             start_rotation=0.0, end_rotation=angle)
        self.animations.append(anim)

    def update_animations(self, dt):
        """推进所有动画，完成时触发回调"""
        done_list = []
        for anim in self.animations:
            anim.elapsed += dt
            if anim.done:
                if anim.on_complete:
                    anim.on_complete()
                done_list.append(anim)
        for anim in done_list:
            self.animations.remove(anim)

    def draw_animations(self):
        """绘制正在飞行中的卡牌（支持旋转）"""
        for anim in self.animations:
            x, y = anim.pos
            # 转为底边中心锚点（draw_card_at 使用锚点定位）
            anchor_x = x + CARD_W // 2
            anchor_y = y + CARD_H
            self.draw_card_at(anim.card, anchor_x, anchor_y, scale=1.0, rotation=anim.rotation, force=True)

    @property
    def is_animating(self):
        return len(self.animations) > 0

    # ----------------------------------------------------------
    # 飘字动画
    # ----------------------------------------------------------
    def spawn_damage_number(self, entity, amount, is_heal=False):
        """在实体位置生成飘字"""
        if amount == 0:
            return
        if entity == self.player:
            x, y = 180, 420
        else:
            x, y = 180, 120
        text = f"+{amount}" if is_heal else f"-{amount}"
        color = (80, 255, 80) if is_heal else (255, 60, 60)
        self.damage_numbers.append(DamageNumber(text, x, y, color))

    def update_damage_numbers(self, dt):
        for dn in self.damage_numbers:
            dn.elapsed += dt
        self.damage_numbers = [dn for dn in self.damage_numbers if not dn.done]

    def draw_damage_numbers(self):
        for dn in self.damage_numbers:
            if dn.alpha <= 0 or dn.scale <= 0:
                continue
            font_size = max(12, int(28 * dn.scale))
            font = pygame.font.SysFont("microsoftyahei", font_size, bold=True)
            surf = font.render(dn.text, True, dn.color)
            surf.set_alpha(dn.alpha)
            rect = surf.get_rect(center=(dn.x, dn.y + dn.offset_y))
            self.screen.blit(surf, rect)

    # ----------------------------------------------------------
    # 游戏逻辑
    # ----------------------------------------------------------
    def start_turn(self):
        self.log(f"\n===== 第 {self.round} 回合 =====")
        self.arena.current_weather.on_turn_start(self.player, self.arena)
        self.arena.current_weather.on_turn_start(self.enemy, self.arena)

        # 中毒伤害飘字
        p_hp = self.player.hp
        e_hp = self.enemy.hp
        self.player.statuses["poison"].tick(self.player)
        self.enemy.statuses["poison"].tick(self.enemy)
        if self.player.hp < p_hp:
            self.spawn_damage_number(self.player, p_hp - self.player.hp)
        if self.enemy.hp < e_hp:
            self.spawn_damage_number(self.enemy, e_hp - self.enemy.hp)
        self.player.ability.on_turn_start(self.player, self.enemy, self.arena)
        self.enemy.ability.on_turn_start(self.enemy, self.player, self.arena)

        if self.player.hp <= 0:
            self.game_over("💀 你倒在了环境伤害下...")
            return
        if self.enemy.hp <= 0:
            self.game_over("🎉 敌人倒在了环境伤害下！")
            return

        self.selected_card_idx = -1
        self.state = STATE_CARD_CHOICE

    def determine_first(self, p_card, e_card):
        p_rank = POKER_ORDER.index(p_card.poker_value)
        e_rank = POKER_ORDER.index(e_card.poker_value)
        self.log(f"🃏 点数对决: {p_card.name}[{p_card.poker_value}] vs {e_card.name}[{e_card.poker_value}]")

        if p_rank > e_rank:
            self.log("  → 你先行动！")
            return "player"
        elif e_rank > p_rank:
            self.log("  → 敌人先行动！")
            return "enemy"
        else:
            winner = random.choice(["player", "enemy"])
            self.log(f"  → 平局！{'你' if winner == 'player' else '敌人'}先行动！")
            return winner

    def execute_card(self, actor, target, card, actor_deck, card_pool, defer_draw=False):
        """执行卡牌效果并抽新牌。defer_draw=True 时新卡不加入牌组（由动画控制）"""
        # 记录双方血量前值
        actor_hp_before = actor.hp
        target_hp_before = target.hp
        actor_shield_before = actor.shield

        card.play(caster=actor, target=target, arena=self.arena)

        # 检测掉血/回血并生成飘字
        actor_hp_delta = actor.hp - actor_hp_before
        target_hp_delta = target.hp - target_hp_before
        shield_delta = actor.shield - actor_shield_before

        if target_hp_delta < 0:
            self.spawn_damage_number(target, abs(target_hp_delta))
        if actor_hp_delta < 0:
            self.spawn_damage_number(actor, abs(actor_hp_delta))
        if actor_hp_delta > 0:
            self.spawn_damage_number(actor, actor_hp_delta, is_heal=True)
        if shield_delta > 0:
            self.spawn_damage_number(actor, shield_delta, is_heal=True)

        actor_deck.remove(card)
        new_card = DeckManager.draw_one_card(card_pool)
        if defer_draw:
            self.log(f"  📥 [{actor.name}] 抽取了新牌: {new_card.name}[{new_card.poker_value}]")
        else:
            actor_deck.append(new_card)
            self.log(f"  📥 [{actor.name}] 抽取了新牌: {new_card.name}[{new_card.poker_value}]")
        return new_card

    def play_selected_card(self):
        if self.is_animating:
            return
        if self.selected_card_idx < 0 or self.selected_card_idx >= len(self.player_deck):
            return

        player_card = self.player_deck[self.selected_card_idx]
        player_idx = self.selected_card_idx
        enemy_card = random.choice(self.enemy_deck)
        first = self.determine_first(player_card, enemy_card)

        def on_play_anim_done():
            """出牌动画结束 → 进入扑克对比画面"""
            self.animating_cards.discard(player_card)
            self.start_poker_compare(player_card, self._compare_enemy_card, first)

        self._compare_enemy_card = enemy_card
        self.queue_play_anim(player_idx, player_card, on_complete=on_play_anim_done)

    def start_poker_compare(self, player_card, enemy_card, first):
        """进入扑克对比状态：显示双方卡牌对比，1.5秒后自动结算"""
        print(f"[DEBUG] start_poker_compare called: player_card={player_card}, enemy_card={enemy_card}, first={first}")
        if not player_card or not enemy_card:
            # 数据异常，跳过对比直接结算
            print("[DEBUG] start_poker_compare: card is None, skipping compare")
            self.state = STATE_CARD_CHOICE
            return
        self._compare_player_card = player_card
        self._compare_enemy_card = enemy_card
        self._compare_result = first  # "player" / "enemy" / "tie"
        self._compare_timer = 0.0
        self.state = STATE_POKER_COMPARE
        print(f"[DEBUG] start_poker_compare: state set to {self.state}, player_card={self._compare_player_card.name}")

    def draw_poker_compare(self):
        """绘制扑克对比画面：双方卡牌放大并排，中间显示点数比较结果"""
        if not self._compare_player_card or not self._compare_enemy_card:
            return
        # 半透明遮罩
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # 标题
        self.draw_text("点数对决", SCREEN_W // 2, 40, self.font_xl, C_GOLD, center=True)

        # 两张卡牌并排放大显示
        scale = 0.8
        cw = int(CARD_W * scale)
        ch = int(CARD_H * scale)
        gap = 120
        left_x = SCREEN_W // 2 - gap // 2 - cw
        right_x = SCREEN_W // 2 + gap // 2
        card_y = SCREEN_H // 2 - ch // 2 + 20

        def draw_compare_card(card, x, y, is_player):
            face = self.get_card_face(card)
            surface = pygame.transform.scale(face, (cw, ch))

            # 元素叠加
            if card.level > 0:
                entity = self.player if is_player else self.enemy
                elem = entity.element
                if elem in self.element_overlays:
                    ov = pygame.transform.scale(self.element_overlays[elem], (cw, ch))
                    surface.blit(ov, (0, 0))

            # 等级标记
            if card.level > 0:
                lv_size = max(10, int(14 * scale))
                lv_font = pygame.font.SysFont("microsoftyahei", lv_size)
                lv_surf = lv_font.render(f"Lv.{card.level}", True, C_GOLD)
                surface.blit(lv_surf, (cw - lv_surf.get_width() - int(4 * scale), int(2 * scale)))

            # 扑克数字（左上 + 右下中心对称）
            pv_w = int(POKER_W * scale)
            pv_h = int(POKER_H * scale)
            if card.poker_value and card.poker_value in self.poker_imgs:
                pv_img = pygame.transform.scale(self.poker_imgs[card.poker_value], (pv_w, pv_h))
                surface.blit(pv_img, (int(3 * scale), int(3 * scale)))
                pv_rot = pygame.transform.rotate(pv_img, 180)
                surface.blit(pv_rot, (cw - pv_rot.get_width() - int(3 * scale),
                                      ch - pv_rot.get_height() - int(3 * scale)))

            # 卡牌名称
            name_size = max(10, int(14 * scale))
            name_font = pygame.font.SysFont("microsoftyahei", name_size)
            name_surf = name_font.render(card.name, True, C_WHITE)
            name_rect = name_surf.get_rect(centerx=cw // 2, bottom=ch - int(5 * scale))
            bg = pygame.Surface((name_rect.width + int(8 * scale), name_rect.height + int(2 * scale)), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 140))
            surface.blit(bg, (name_rect.x - int(4 * scale), name_rect.y - 1))
            surface.blit(name_surf, name_rect)

            # 标签
            label = "你的牌" if is_player else "敌人的牌"
            label_color = C_BLUE if is_player else C_RED
            lw = left_x + cw // 2 if is_player else right_x + cw // 2
            self.draw_text(label, lw, card_y - 25, self.font, label_color, center=True)

            self.screen.blit(surface, (x, y))

        draw_compare_card(self._compare_player_card, left_x, card_y, True)
        draw_compare_card(self._compare_enemy_card, right_x, card_y, False)

        # 中间：VS 和点数比较
        cx = SCREEN_W // 2
        mid_y = SCREEN_H // 2

        self.draw_text("VS", cx, mid_y - 10, self.font_xl, C_GOLD, center=True)

        # 显示双方点数
        p_val = self._compare_player_card.poker_value
        e_val = self._compare_enemy_card.poker_value
        p_rank = POKER_ORDER.index(p_val) if p_val in POKER_ORDER else 0
        e_rank = POKER_ORDER.index(e_val) if e_val in POKER_ORDER else 0

        # 点数显示（大的）
        pv_font = pygame.font.SysFont("microsoftyahei", 48, bold=True)
        p_surf = pv_font.render(p_val, True, C_BLUE)
        e_surf = pv_font.render(e_val, True, C_RED)
        self.screen.blit(p_surf, p_surf.get_rect(center=(cx, mid_y + 35)))
        self.screen.blit(e_surf, e_surf.get_rect(center=(cx, mid_y + 80)))

        # 胜负结果文字
        if self._compare_result == "player":
            result_text = "你先行动！"
            result_color = C_GREEN
        elif self._compare_result == "enemy":
            result_text = "敌人先行动！"
            result_color = C_RED
        else:
            result_text = "平局！随机决定"
            result_color = C_GOLD
        self.draw_text(result_text, cx, mid_y + 125, self.font_lg, result_color, center=True)


    def on_compare_done(self):
        """对比画面计时结束：结算卡牌效果"""
        print(f"[DEBUG] on_compare_done called: player_card={self._compare_player_card}, enemy_card={self._compare_enemy_card}, result={self._compare_result}")
        player_card = self._compare_player_card
        enemy_card = self._compare_enemy_card
        first = self._compare_result
        if not player_card or not enemy_card:
            print("[DEBUG] on_compare_done: card is None, falling back to STATE_CARD_CHOICE")
            self.state = STATE_CARD_CHOICE
            return

        # 清理对比状态
        self._compare_player_card = None
        self._compare_enemy_card = None
        self._compare_result = None

        def after_draw_and_enemy():
            """玩家先手：摸牌动画结束 → 敌人出牌 → 结束"""
            self.animating_cards.discard(new_card)
            self.player_deck.append(new_card)
            self.execute_card(self.enemy, self.player, enemy_card, self.enemy_deck, LEVEL0_ENEMY_CARD)
            self._finish_turn_after_anim()

        def after_draw():
            """敌人先手：摸牌动画结束 → 结束"""
            self.animating_cards.discard(new_card)
            self.player_deck.append(new_card)
            self._finish_turn_after_anim()

        if first == "player":
            # 玩家先手：执行玩家 → 摸牌动画 → 敌人出牌
            new_card = self.execute_card(self.player, self.enemy, player_card, self.player_deck, NORMAL_CARDS, defer_draw=True)
            if self.check_death():
                return
            new_idx = len(self.player_deck)
            self.queue_draw_anim(new_card, new_idx, self._hand_x, self._hand_y, on_complete=after_draw_and_enemy)
        else:
            # 敌人先手：执行敌人 → 执行玩家 → 摸牌动画
            self.execute_card(self.enemy, self.player, enemy_card, self.enemy_deck, LEVEL0_ENEMY_CARD)
            if self.check_death():
                return
            new_card = self.execute_card(self.player, self.enemy, player_card, self.player_deck, NORMAL_CARDS, defer_draw=True)
            if self.check_death():
                return
            new_idx = len(self.player_deck)
            self.queue_draw_anim(new_card, new_idx, self._hand_x, self._hand_y, on_complete=after_draw)

    def _finish_turn_after_anim(self):
        """动画全部结束后收尾"""
        if self.check_death():
            return
        self.end_turn()

    def check_death(self):
        if self.enemy.hp <= 0:
            self.game_over("🎉 胜利！你击败了敌人！")
            return True
        if self.player.hp <= 0:
            self.game_over("💀 失败！你倒下了...")
            return True
        return False

    def end_turn(self):
        self.player.ability.on_turn_end(self.player, self.player_deck)
        self.enemy.ability.on_turn_end(self.enemy, self.enemy_deck)
        self.arena.skip_turn = False

        if not self.arena.current_weather.is_permanent:
            self.arena.current_weather.duration -= 1
            if self.arena.current_weather.duration <= 0:
                self.log(f"🌤️ 环境【{self.arena.current_weather.name}】消散！")
                self.arena.change_weather(CleanEnvironment())

        if self.round == 3:
            self.log("⬆️ 卡牌升级时间！点击一张手牌升级")
            self.state = STATE_UPGRADE
            self.selected_card_idx = -1
            self.round += 1
            return

        self.round += 1
        self.start_turn()

    def activate_ability(self):
        ability = self.player.ability
        if isinstance(ability, StaticAbility) and ability.can_activate():
            ability.on_activate(self.player, self.enemy, self.arena)
            self.log(f"🌿 你发动了【{ability.name}】！双方本回合无法出牌！")
            new_p = DeckManager.draw_one_card(NORMAL_CARDS)
            self.player_deck.append(new_p)
            self.log(f"📥 抽取了新牌: {new_p.name}[{new_p.poker_value}]")
            new_e = DeckManager.draw_one_card(LEVEL0_ENEMY_CARD)
            self.enemy_deck.append(new_e)
            self.log(f"📥 敌人抽取了新牌: {new_e.name}[{new_e.poker_value}]")
            self.end_turn()
        else:
            self.log("⚠️ 专属技能冷却中或不可用")

    def upgrade_selected_card(self):
        if self.selected_card_idx < 0 or self.selected_card_idx >= len(self.player_deck):
            return
        old = self.player_deck[self.selected_card_idx]
        new = CardUpgradeManager.upgrade_card(old, self.player)
        self.player_deck[self.selected_card_idx] = new
        self.log(f"⬆️ {old.name} → {new.name} Lv.1")

        candidates = [i for i, c in enumerate(self.enemy_deck) if c.level == 0]
        if candidates:
            idx = random.choice(candidates)
            old_e = self.enemy_deck[idx]
            new_e = CardUpgradeManager.upgrade_card(old_e, self.enemy)
            self.enemy_deck[idx] = new_e
            self.log(f"⬆️ 敌人: {old_e.name} → {new_e.name} Lv.1")

        self.selected_card_idx = -1
        self.start_turn()

    def game_over(self, msg):
        self.game_over_msg = msg
        self.state = STATE_GAME_OVER
        self.log(msg)

    def reset_game(self):
        self.arena = BattleEnvironment()
        self.player = WoodEntity("木", max_hp=300, atk=50, defense=20)
        self.enemy = FireEntity("火", max_hp=500, atk=60, defense=30)
        self.player_deck = DeckManager.get_cards_from_deck(NORMAL_CARDS, 5)
        self.enemy_deck = DeckManager.get_cards_from_deck(LEVEL0_ENEMY_CARD, 3)
        self.round = 1
        self.state = STATE_CARD_CHOICE
        self.log_lines = []
        self.selected_card_idx = -1
        self.game_over_msg = ""
        self.log("⚔️ 新战斗开始！")

    # ----------------------------------------------------------
    # 主循环
    # ----------------------------------------------------------
    def run(self):
        # 手牌区域坐标（居中偏下）
        self._hand_x = (SCREEN_W - (CARD_W * 5 + CARD_GAP * 4)) // 2
        self._hand_y = 380
        hand_x = self._hand_x
        hand_y = self._hand_y

        # 扇形手牌布局参数（扑克手持样式）
        self._fan_cx = SCREEN_W // 2       # 水平居中
        self._fan_cy = SCREEN_H + 260      # 圆心在屏幕下方
        self._fan_radius = 400             # 底边锚点小圆弧半径
        self._fan_scale = 0.5              # 缩小到 50%
        self._fan_total_angle = 40         # 总张角（每张牌的旋转角度）
        fan_cx = self._fan_cx
        fan_cy = self._fan_cy
        fan_radius = self._fan_radius
        fan_scale = self._fan_scale
        fan_total_angle = self._fan_total_angle
        enemy_hand_x = (SCREEN_W - (ENEMY_CARD_W * 3 + ENEMY_CARD_GAP * 2)) // 2
        enemy_hand_y = 48

        # 角色选择卡片布局参数（与 draw_char_select 一致）
        char_card_w, char_card_h = 210, 560
        char_gap = 16
        char_total_w = char_card_w * 5 + char_gap * 4
        char_start_x = (SCREEN_W - char_total_w) // 2
        char_start_y = 110

        dt = 0
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0  # 秒
            self.update_animations(dt)
            self.update_damage_numbers(dt)

            # 扑克对比计时器
            if self.state == STATE_POKER_COMPARE:
                self._compare_timer += dt
                if self._compare_timer >= 1.0:
                    print(f"[DEBUG] timer expired, calling on_compare_done. state={self.state}, timer={self._compare_timer:.3f}")
                    self.on_compare_done()

            mx, my = pygame.mouse.get_pos()

            # 悬停检测（动画中禁用）
            if self.is_animating:
                self.hovered_card_idx = -1
            elif self.state == STATE_CHAR_SELECT:
                self.char_hovered = -1
                for i in range(5):
                    cx = char_start_x + i * (char_card_w + char_gap)
                    if cx <= mx <= cx + char_card_w and char_start_y <= my <= char_start_y + char_card_h:
                        self.char_hovered = i
            elif self.state == STATE_CARD_CHOICE:
                self.hovered_card_idx = self.get_fanchard_at_pos(
                    mx, my, self.player_deck, fan_cx, fan_cy, fan_radius, fan_scale, fan_total_angle)
            elif self.state == STATE_UPGRADE:
                self.hovered_card_idx = self.get_card_at_pos(mx, my, self.player_deck, hand_x, hand_y)
            elif self.state == STATE_POKER_COMPARE:
                self.hovered_card_idx = -1
            else:
                self.hovered_card_idx = -1

            # 动画中跳过游戏输入
            if not self.is_animating:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False

                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            running = False

                        if self.state == STATE_CHAR_SELECT:
                            if pygame.K_1 <= event.key <= pygame.K_5:
                                self.start_game(event.key - pygame.K_1)

                        elif self.state == STATE_CARD_CHOICE:
                            if pygame.K_1 <= event.key <= pygame.K_5:
                                idx = event.key - pygame.K_1
                                if idx < len(self.player_deck):
                                    self.selected_card_idx = idx
                                    self.play_selected_card()
                            elif event.key == pygame.K_a:
                                self.activate_ability()

                        elif self.state == STATE_UPGRADE:
                            if pygame.K_1 <= event.key <= pygame.K_5:
                                idx = event.key - pygame.K_1
                                if idx < len(self.player_deck):
                                    self.selected_card_idx = idx
                                    self.upgrade_selected_card()

                        elif self.state == STATE_GAME_OVER:
                            if event.key == pygame.K_r:
                                self.state = STATE_CHAR_SELECT

                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if self.state == STATE_CHAR_SELECT:
                            if self.char_hovered >= 0:
                                self.start_game(self.char_hovered)
                        elif self.state == STATE_CARD_CHOICE:
                            if self.hovered_card_idx >= 0:
                                self.selected_card_idx = self.hovered_card_idx
                                self.play_selected_card()
                        elif self.state == STATE_UPGRADE:
                            idx = self.get_card_at_pos(mx, my, self.player_deck, hand_x, hand_y)
                            if idx >= 0:
                                self.selected_card_idx = idx
                                self.upgrade_selected_card()

            # ---------- 绘制 ----------
            self.screen.blit(self.bg_image, (0, 0))

            if self.state == STATE_CHAR_SELECT:
                self.draw_char_select()

            else:
                # 回合信息（屏幕最上方）
                self.draw_text(f"第 {self.round} 回合", SCREEN_W // 2, 15, self.font_lg, C_GOLD, center=True)

                # 环境
                self.draw_environment(SCREEN_W // 2 - 125, 200)

                # 敌人信息
                self.draw_panel(60, 90, 750, 95)
                self.draw_entity(self.enemy, 80, 100, is_player=False)

                # 敌人手牌
                self.draw_enemy_hand(self.enemy_deck, enemy_hand_x, enemy_hand_y)

                # 玩家信息（卡牌上方）
                self.draw_panel(60, 280, 750, 95)
                self.draw_entity(self.player, 80, 290, is_player=True)

                # 飘字动画
                self.draw_damage_numbers()

                # 玩家手牌
                if self.state == STATE_CARD_CHOICE:
                    # 扇形握持
                    self.draw_fan_hand(self.player_deck, fan_cx, fan_cy, fan_radius, fan_scale, fan_total_angle)
                elif self.state not in (STATE_POKER_COMPARE, STATE_GAME_OVER):
                    # 升级等状态用网格布局（对比和结束时不绘制）
                    panel_x = hand_x - 20
                    self.draw_panel(panel_x, hand_y - 10, CARD_W * 5 + CARD_GAP * 4 + 40, CARD_H + 30)
                    self.draw_hand(self.player_deck, hand_x, hand_y)

                # 战斗日志
                self.draw_log(850, 30, 400, 350)

                # 操作提示
                self.draw_hints(80, SCREEN_H - 30)

                # 扑克对比覆盖层
                if self.state == STATE_POKER_COMPARE:
                    self.draw_poker_compare()

                # 游戏结束覆盖层
                if self.state == STATE_GAME_OVER:
                    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 150))
                    self.screen.blit(overlay, (0, 0))
                    self.draw_text(self.game_over_msg, SCREEN_W // 2, SCREEN_H // 2 - 20, self.font_xl, C_GOLD, center=True)
                    self.draw_text("按 R 重新开始 | ESC 退出", SCREEN_W // 2, SCREEN_H // 2 + 30, self.font, C_WHITE, center=True)

            # 动画层（最顶层）
            self.draw_animations()

            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    scene = Scene()
    scene.run()
