class StatusEffect:
    def __init__(self, name, max_level):
        self.name = name
        self.level = 0
        self.max_level = max_level

    def add_level(self, amount=1):
        """增加状态层数"""
        self.level = min(self.level + amount, self.max_level)
        print(f"   🔼 [状态] {self.name} 提升至 {self.level} 级！")

    def clear(self):
        """清空该状态"""
        if self.level > 0:
            self.level = 0
            print(f"   💨 [状态] {self.name} 的影响已被清空！")

class AttackBoost(StatusEffect):
    def __init__(self):
        super().__init__(name="攻击强化", max_level=2)
        # 离散的状态影响映射表：0级+0%，1级+50%，2级+120%
        self.level_bonuses = {
            0: 0.0,
            1: 0.50,
            2: 1.20
        }

    def get_multiplier(self):
        """返回当前的攻击倍率 (基础1.0 + 额外加成)"""
        return 1.0 + self.level_bonuses[self.level]

def calculate_damage(attacker, defender, arena, skill_multiplier=1.0, def_constant=100.0,atk_num=1):
    """
    终极版伤害计算器：包含基础攻防、五行克制、技能倍率、以及【环境干预】
    """
    # 1. 查表获取五行倍率 (假设 ELEMENTAL_TABLE 已经在该文件引入)
    atk_mult, def_mult = ELEMENTAL_TABLE.get((attacker.element, defender.element), (1.0, 1.0))
    actual_atk_num=atk_num
    # 2. 基础威力、五行加成的基础攻击力

    actual_atk = attacker.atk * skill_multiplier * atk_mult
    actual_def = defender.defense * def_mult
    damage_multiplier = def_constant / (def_constant + actual_def)
    base_damage = actual_atk * damage_multiplier
    if defender.shield>0:
        actual_atk_num = 0
        for _ in range(atk_num):
            defender.shield = defender.shield-1
            #other performance
            if defender.shield < 0:
                defender.shield = 0
                actual_atk_num =actual_atk_num+1
    if actual_atk_num>1:
        print("连击 ",base_damage,"*",actual_atk_num)
    base_damage = actual_atk_num * base_damage
    return int(base_damage)
    # 4. 环境干预 (重点在这里！调用天气的 modify_damage 来修改伤害)
    final_damage = arena.current_weather.modify_damage(attacker, defender, base_damage, arena)

    # 5. 返回最终整数伤害
    return int(final_damage)

ELEMENTAL_TABLE = {
    # === 金系 (Metal) ===
    ("metal", "wood"): (2.0, 0.5),   # 金克木
    ("metal", "water"): (1.0, 2.0),  # 金生水
    ("metal", "fire"): (0.5, 2.0),   # 火克金 (被克)
    ("metal", "earth"): (2.0, 1.0),  # 土生金 (被生)
    ("metal", "metal"): (1.0, 1.0),  # 同系

    # === 木系 (Wood) ===
    ("wood", "earth"): (2.0, 0.5),   # 木克土
    ("wood", "fire"): (1.0, 2.0),    # 木生火
    ("wood", "metal"): (0.5, 2.0),   # 金克木 (被克)
    ("wood", "water"): (2.0, 1.0),   # 水生木 (被生)
    ("wood", "wood"): (1.0, 1.0),    # 同系

    # === 水系 (Water) ===
    ("water", "fire"): (2.0, 0.5),   # 水克火
    ("water", "wood"): (1.0, 2.0),   # 水生木
    ("water", "earth"): (0.5, 2.0),  # 土克水 (被克)
    ("water", "metal"): (2.0, 1.0),  # 金生水 (被生)
    ("water", "water"): (1.0, 1.0),  # 同系

    # === 火系 (Fire) ===
    ("fire", "metal"): (2.0, 0.5),   # 火克金
    ("fire", "earth"): (1.0, 2.0),   # 火生土
    ("fire", "water"): (0.5, 2.0),   # 水克火 (被克)
    ("fire", "wood"): (2.0, 1.0),    # 木生火 (被生)
    ("fire", "fire"): (1.0, 1.0),    # 同系

    # === 土系 (Earth) ===
    ("earth", "water"): (2.0, 0.5),  # 土克水
    ("earth", "metal"): (1.0, 2.0),  # 土生金
    ("earth", "wood"): (0.5, 2.0),   # 木克土 (被克)
    ("earth", "fire"): (2.0, 1.0),   # 火生土 (被生)
    ("earth", "earth"): (1.0, 1.0)   # 同系
}
# def get_side(element1, element2):
#     """
#     通过传入两个元素，组成二元组进行查表。
#     """
#     return ELEMENTAL_TABLE.get((element1, element2),(1.0, 1.0))

class Entity:
    def __init__(self, name,element, max_hp, atk, defense, damage_reduction=0.0):
        self.name = name
        self.element = element
        self.max_hp = max_hp
        self.hp = max_hp
        self.shield = 0
        self.miss=0
        self.sharp=0
        self.heal=0
        self.base_atk = atk
        self.defense = defense
        self.damage_reduction = damage_reduction

        self.statuses = {
            "atk_boost": AttackBoost()
        }

    @property
    def atk(self):
        """
        动态属性计算：每次读取 attacker.atk 时，都会执行这段代码。
        最终攻击力 = 基础攻击力 * 攻击强化状态的倍率
        """
        multiplier = self.statuses["atk_boost"].get_multiplier()
        return int(self.base_atk * multiplier)

    def gain_shield(self, amount):
        self.shield += amount
        print(f"🛡️ [{self.name}] 获得了 {amount} 点护盾！")

    def apply_damage(self, final_damage):
        print(f"⚔️ [{self.name}] 即将承受 {final_damage} 点最终伤害！")

        self.hp -= final_damage
        self.hp = max(0, self.hp)
        print(f"   -> 受到 {final_damage} 点真实伤害！剩余 HP: {self.hp}")
        if self.hp == 0:
            print(f"💀 [{self.name}] 阵亡了！")


class FireEntity(Entity):
    # 初始化时，不需要再传入 element，我们强制将其定为 "fire"
    def __init__(self, name, max_hp, atk, defense, damage_reduction=0.0):
        # 调用父类的初始化方法，强制传入 element="fire"
        super().__init__(name, "fire", max_hp, atk, defense, damage_reduction)

        # 直接在子类里修改属性 (比如火系天生攻击力高 20%)
        self.atk = int(self.atk * 1.20)
        self.miss=0.2
        print(f"🔥 [被动触发] {self.name} 是火系角色，基础攻击力提升 20%，当前面板攻击力为 {self.atk}！")

class WaterEntity(Entity):
    def __init__(self, name, max_hp, atk, defense, damage_reduction=0.0):
        super().__init__(name, "water", max_hp, atk, defense, damage_reduction)
        self.atk = int(self.atk * 1.10)
        self.defense = int(self.defense * 1.10)
        self.miss = 0.1
        self.ability="shapable"

class EarthEntity(Entity):
    def __init__(self, name, max_hp, atk, defense, damage_reduction=0.0):
        super().__init__(name, "earth", max_hp, atk, defense, damage_reduction)
        self.shield = 3
        self.ability = "nourish"

class MetalEntity(Entity):
    def __init__(self, name, max_hp, atk, defense, damage_reduction=0.0):
        super().__init__(name, "metal", max_hp, atk, defense, damage_reduction)
        self.defense = int(self.defense * 1.20)
        self.atk = int(self.atk * 1.20)
        self.sharp = 2

class WoodEntity(Entity):
    def __init__(self, name, max_hp, atk, defense, damage_reduction=0.0):
        super().__init__(name, "wood", max_hp, atk, defense, damage_reduction)
        self.heal=2
        self.defense = int(self.defense * 1.20)
        self.ability="static"
