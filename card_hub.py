import random
from tkinter.constants import NORMAL

from environment import RainEnvironment, LavaEnvironment
from skill import Skill


class Card:
    def __init__(self, card_id, name, card_type, description, skill, poker_value=None, level=0):
        # --- 牌面信息 (UI与前端展示用到) ---
        self.card_id = card_id  # 卡牌编号 (方便以后配图或查Excel表)
        self.name = name  # 卡牌名称
        self.card_type = card_type  # 类型：比如 "Attack"(攻击牌), "Skill"(技能牌), "Power"(能力牌)
        self.description = description  # 卡牌描述文本
        self.poker_value = poker_value  # 扑克牌数字 (A-K)，用于后续博弈效果
        self.level = level  # 卡牌等级 (0=基础, 1=Lv.1, ...)

        # --- 后台逻辑 (支持单个或多个 Skill) ---
        if isinstance(skill, list):
            self.skills = skill
        else:
            self.skills = [skill]

    @property
    def skill(self):
        """向后兼容：返回第一个技能"""
        return self.skills[0]

    def play(self, caster, target, arena):
        """
        打出卡牌的动作。
        依次执行所有绑定的技能。
        """
        print(f"   📜 卡牌效果: {self.description}")

        for s in self.skills:
            s.execute(caster=caster, target=target, arena=arena)

        return True  # 打牌成功

class DeckManager:
    # 扑克牌数字列表 (A 到 K)
    POKER_VALUES = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']

    @staticmethod
    def get_cards_from_deck(card_pool, count=5):
        """从指定牌库中随机抽取 count 张不重复的卡牌副本，并随机分配扑克牌数字"""
        all_ids = list(card_pool.keys())
        selected_ids = random.sample(all_ids, min(len(all_ids), count))

        cards = []
        for cid in selected_ids:
            base_card = card_pool[cid]
            poker_value = random.choice(DeckManager.POKER_VALUES)
            new_card = Card(
                base_card.card_id,
                base_card.name,
                base_card.card_type,
                base_card.description,
                base_card.skills,
                poker_value
            )
            cards.append(new_card)
        return cards

    @staticmethod
    def get_random_cards(count=5):
        """从大牌库中随机抽取 count 张不重复的卡牌副本，并随机分配扑克牌数字"""
        return DeckManager.get_cards_from_deck(ALL_CARDS, count)

    @staticmethod
    def draw_one_card(card_pool):
        """从指定牌库中随机抽取1张卡牌副本，随机分配扑克牌数字"""
        return DeckManager.get_cards_from_deck(card_pool, 1)[0]

    @staticmethod
    def get_elemental_deck(element, count=5):
        """进阶：只抽取特定属性的卡牌 (例如开局选职业)，并随机分配扑克牌数字"""
        filtered_ids = [cid for cid in ALL_CARDS.keys() if cid.startswith(element[0].upper())]
        # 如果该系牌不够，就从全库补齐
        selected_ids = random.sample(filtered_ids, min(len(filtered_ids), count))

        cards = []
        for cid in selected_ids:
            base_card = ALL_CARDS[cid]
            poker_value = random.choice(DeckManager.POKER_VALUES)
            new_card = Card(
                base_card.card_id,
                base_card.name,
                base_card.card_type,
                base_card.description,
                base_card.skills,
                poker_value
            )
            cards.append(new_card)
        return cards




s_atk_low = Skill("轻微打击", "attack", power=1.0)
s_atk_mid = Skill("标准打击", "attack", power=1.5)
s_atk_high = Skill("全力重击", "attack", power=2.5)
s_combo = Skill("连击", "attack", power=0.75, num=2)

s_shield_1 = Skill("护甲+1", "shield", power=1)
s_shield_2 = Skill("护甲+2", "shield", power=2)

s_buff_atk = Skill("攻击UP", "buff", power=1, status_target="atk_boost")
s_buff_def = Skill("防御UP", "buff", power=1, status_target="def_boost")
s_dispel = Skill("驱散", "dispel", status_target="atk_boost")

s_env_rain = Skill("降雨", "change_env", env_effect=RainEnvironment)
s_env_lava = Skill("火山", "change_env", env_effect=LavaEnvironment)


# --- 定义全量卡牌大仓库 (以 ID 为 Key) ---
NORMAL_CARDS = {
    # 进攻
    "C001": Card("C001", "进击", "Attack", "进攻，造成1.0倍攻击力伤害", s_atk_low),
    "C004": Card("C004", "用力打", "Attack", "进攻，造成1.5倍攻击力伤害", s_atk_mid),
    "C005": Card("C005", "别怕，我有云南白药", "Attack", "进攻，造成2.5倍攻击力伤害", s_atk_high),
    "C006": Card("C006","正反手","Attack","造成二连击",s_combo),

    # 防御
    "C003": Card("C003","天冷加衣","Shield","护甲等级+1",s_shield_1),

    # buff
    "C002": Card("C002", "抱头", "Buff", "防御等级上升一级", s_buff_def),
    "C007": Card("C007", "握拳", "Buff", "攻击等级上升一级", s_buff_atk),
}
LEVEL0_ENEMY_CARD = {
    "C001": Card("C001", "进击", "Attack", "进攻，造成1.0倍攻击力伤害", s_atk_low),
    "C002": Card("C002", "抱头", "Buff", "防御等级上升一级", s_buff_def),
    "C004": Card("C004", "用力打", "Attack", "进攻，造成1.5倍攻击力伤害", s_atk_mid),
}


# ============================================================
# Level 1 升级卡牌系统
# ============================================================

# --- L1 技能实例（比基础更强，已去重） ---
s_atk_low_L1 = Skill("元素斩", "attack", power=1.2)
s_atk_mid_L1 = Skill("元素爆破", "attack", power=1.8)
s_atk_high_L1 = Skill("元素终结", "attack", power=3.0)
s_combo_L1 = Skill("元素连击", "attack", power=0.9, num=2)
s_shield_L1 = Skill("元素护甲", "shield", power=2)
s_heal_L1 = Skill("元素治愈", "heal", power=60)
s_poison_L1 = Skill("毒素蔓延", "poison", power=2)

# --- 金系 Lv.1 ---
L1_METAL = {
    "L1M001": Card("L1M001", "金罡斩", "Attack", "金系攻击，造成1.2倍伤害", s_atk_low_L1, level=1),
    "L1M002": Card("L1M002", "破阵金枪", "Attack", "金系重击，造成3.0倍伤害", s_atk_high_L1, level=1),
    "L1M003": Card("L1M003", "金刚壁", "Shield", "获得2次永久护盾", s_shield_L1, level=1),
    "L1M004": Card("L1M004", "金系元素强化", "Buff", "攻击和防御各提升一级", [s_buff_atk, s_buff_def], level=1),
}

# --- 木系 Lv.1 ---
L1_WOOD = {
    "L1W001": Card("L1W001", "灵木回春", "Heal", "恢复60点HP", s_heal_L1, level=1),
    "L1W002": Card("L1W002", "荆棘", "Attack", "木系连击，造成三连击", [s_combo_L1,s_atk_low], level=1),
    "L1W003": Card("L1W003", "腐毒之种", "Poison", "对目标施加2层中毒", s_poison_L1, level=1),
    "L1W004": Card("L1W004", "木系元素强化", "Buff", "攻击和防御各提升一级", [s_buff_atk, s_buff_def], level=1),
}

# --- 水系 Lv.1 ---
L1_WATER = {
    "L1T001": Card("L1T001", "怒涛冲击", "Attack", "水系攻击，造成1.8倍伤害", s_atk_mid_L1, level=1),
    "L1T002": Card("L1T002", "潮汐连击", "Attack", "水系连击，造成三连击", [s_combo_L1,s_atk_low], level=1),
    "L1T003": Card("L1T003", "深海庇护", "Shield", "获得2次永久护盾", s_shield_L1, level=1),
    "L1T004": Card("L1T004", "水系元素强化", "Buff", "攻击和防御各提升一级", [s_buff_atk, s_buff_def], level=1),
}

# --- 火系 Lv.1 ---
L1_FIRE = {
    "L1F001": Card("L1F001", "炎爆术", "Attack", "火系攻击，造成1.8倍伤害", s_atk_mid_L1, level=1),
    "L1F002": Card("L1F002", "烈焰风暴", "Attack", "火系重击，造成3.0倍伤害", s_atk_high_L1, level=1),
    "L1F003": Card("L1F003", "灼烧驱散", "Dispel", "清除目标攻击强化", s_dispel, level=1),
    "L1F004": Card("L1F004", "火系元素强化", "Buff", "攻击和防御各提升一级", [s_buff_atk, s_buff_def], level=1),
}

# --- 土系 Lv.1 ---
L1_EARTH = {
    "L1E001": Card("L1E001", "岩甲", "Shield", "获得2次永久护盾", s_shield_L1, level=1),
    "L1E002": Card("L1E002", "地脉强化", "Buff", "防御等级上升两级", [s_buff_def,s_buff_def], level=1),
    "L1E003": Card("L1E003", "落石冲击", "Attack", "土系攻击，造成1.8倍伤害", s_atk_mid_L1, level=1),
    "L1E004": Card("L1E004", "土系元素强化", "Buff", "攻击和防御各提升一级", [s_buff_atk, s_buff_def], level=1),
}

# 元素名 → Lv.1 牌库映射
L1_POOLS = {
    "metal": L1_METAL,
    "wood":  L1_WOOD,
    "water": L1_WATER,
    "fire":  L1_FIRE,
    "earth": L1_EARTH,
}


class CardUpgradeManager:
    @staticmethod
    def upgrade_card(card, entity):
        """
        将卡牌升级为角色自身元素的 Level 1 卡牌。
        - 只能从角色对应元素的牌库中选择
        - 卡牌类型必须相同（Attack→Attack，Shield→Shield 等）
        - poker_value 保持不变
        - 返回新的 Card 对象（不修改原卡）
        """
        element = entity.element
        pool = L1_POOLS.get(element)
        if not pool:
            print(f"   [错误] 未知元素: {element}")
            return card

        # 按卡牌类型过滤
        candidates = [c for c in pool.values() if c.card_type == card.card_type]
        if not candidates:
            print(f"   ⚠️ [{element}] 的 Lv.1 牌库中没有类型为 [{card.card_type}] 的卡牌，无法升级")
            return card

        base = random.choice(candidates)
        upgraded = Card(
            base.card_id,
            base.name,
            base.card_type,
            base.description,
            base.skills,
            poker_value=card.poker_value,  # 点数不变
            level=1
        )
        print(f"   ⬆️ [{card.name}][{card.poker_value}] → [{upgraded.name}][{upgraded.poker_value}] Lv.1 ({element})")
        return upgraded
