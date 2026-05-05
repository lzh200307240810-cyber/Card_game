import random

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
        return 1.0 + self.level_bonuses[self.level]

class DefenseBoost(StatusEffect):
    def __init__(self):
        super().__init__(name="防御强化", max_level=2)
        # 离散的状态影响映射表：0级+0%，1级+50%，2级+120%
        self.level_bonuses = {
            0: 0.0,
            1: 0.50,
            2: 1.00
        }
    def get_multiplier(self):
        return 1.0 + self.level_bonuses[self.level]

class PoisonStatus(StatusEffect):
    """中毒状态：每层每回合流失8%最大生命，无视护甲，最多5层"""
    def __init__(self):
        super().__init__(name="中毒", max_level=5)
        self.percent_per_stack = 0.08

    def add_stack(self, amount=1):
        """叠加中毒层数"""
        self.level = min(self.level + amount, self.max_level)
        print(f"   ☠️ [中毒] 叠加至 {self.level} 层！")

    def tick(self, owner):
        """回合开始时触发中毒伤害，返回总伤害"""
        if self.level <= 0:
            return 0
        damage = int(owner.max_hp * self.percent_per_stack * self.level)
        print(f"   ☠️ [中毒] {owner.name} 受到 {self.level} 层中毒，流失 {damage} 点生命！（无视护甲）")
        owner.hp -= damage
        owner.hp = max(0, owner.hp)
        # 每回合自然消退1层
        self.level -= 1
        if self.level > 0:
            print(f"   ☠️ [中毒] 剩余 {self.level} 层")
        else:
            print(f"   ☠️ [中毒] 毒素已消散！")
        return damage

class Ability:
    """角色专属技能基类"""
    def __init__(self, name, description):
        self.name = name
        self.description = description

    def on_turn_start(self, owner, opponent, arena):
        pass

    def on_turn_end(self, owner, deck=None):
        pass

class ShapableAbility(Ability):
    """水系专属：每2回合复制对方的状态等级"""
    def __init__(self):
        super().__init__("塑形", "每2回合复制对方的状态等级")
        self.cooldown = 2
        self.counter = 2

    def on_turn_start(self, owner, opponent, arena):
        self.counter -= 1
        if self.counter <= 0:
            for key in owner.statuses:
                if key in opponent.statuses:
                    src = opponent.statuses[key]
                    dst = owner.statuses[key]
                    if src.level != dst.level:
                        dst.level = src.level
                        print(f"   🌊 [塑形] {owner.name} 复制了 {opponent.name} 的【{dst.name}】等级 → {dst.level}")
            self.counter = self.cooldown

class LightAbility(Ability):
    """火系专属：双方手牌互相可见"""
    def __init__(self):
        super().__init__("光明", "双方手牌互相可见")

    def on_turn_start(self, owner, opponent, arena):
        if not arena.see_all:
            arena.see_all = True
            print(f"   💡 [光明] {owner.name} 点亮了战场，双方手牌互相可见！")

class StaticAbility(Ability):
    """木系专属：主动技能，双方本回合不能出牌，回合结束恢复30%生命，2回合冷却"""
    def __init__(self):
        super().__init__("静止", "双方本回合不能出牌，回合结束恢复30%生命")
        self.cooldown = 2
        self.current_cd = 0  # 0 表示可用
        self.pending_heal = False  # 标记回合结束时是否需要回血

    def can_activate(self):
        return self.current_cd == 0

    def on_activate(self, owner, opponent, arena):
        """主动发动：双方本回合跳过出牌"""
        arena.skip_turn = True
        self.pending_heal = True
        self.current_cd = self.cooldown + 1  # +1 因为本回合结束就会 tick 一次
        print(f"   🌿 [静止] {owner.name} 发动了【静止】！双方本回合无法出牌！")

    def on_turn_end(self, owner, deck=None):
        """回合结束时：恢复30%生命，冷却递减"""
        if self.pending_heal:
            heal_amount = int(owner.max_hp * 0.30)
            owner.hp = min(owner.hp + heal_amount, owner.max_hp)
            print(f"   🌿 [静止] {owner.name} 恢复了 {heal_amount} 点 HP！当前 HP: {owner.hp}/{owner.max_hp}")
            self.pending_heal = False
        if self.current_cd > 0:
            self.current_cd -= 1
            if self.current_cd > 0:
                print(f"   🌿 [静止] 冷却中... 还需 {self.current_cd} 回合")

def calculate_damage(attacker, defender, arena, skill_multiplier=1.0, def_constant=100.0,atk_num=1):
    """
    终极版伤害计算器：包含基础攻防、五行克制、技能倍率、以及【环境干预】
    """
    atk_mult=1
    def_mult=1
    actual_atk_num=atk_num
    # 2. 基础威力、五行加成的基础攻击力

    actual_atk = attacker.atk * skill_multiplier * atk_mult
    actual_def = defender.defense * def_mult
    # 穿透：每点 sharp 无视 15% 防御
    sharp = getattr(attacker, 'sharp', 0)
    if sharp > 0:
        ignore_rate = min(sharp * 0.15, 1.0)
        actual_def = int(actual_def * (1 - ignore_rate))
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
    # 4. 环境干预 (重点在这里！调用天气的 modify_damage 来修改伤害)
    temp_damage = int(arena.current_weather.modify_damage(attacker, defender, base_damage, arena))
    final_damage = actual_atk_num * temp_damage
    if actual_atk_num>1:
        print("连击 ",temp_damage,"*",actual_atk_num)

    # 5. 返回最终整数伤害
    return final_damage


# def get_side(element1, element2):
#     """
#     通过传入两个元素，组成二元组进行查表。
#     """
#     return ELEMENTAL_TABLE.get((element1, element2),(1.0, 1.0))

class Entity:
    def __init__(self, name, element, max_hp, atk, defense, damage_reduction=0.0):
        self.name = name
        self.element = element
        self.max_hp = max_hp
        self.hp = max_hp
        self.shield = 0
        self.miss=0
        self.sharp=0
        self.heal=0
        self.base_atk = atk
        self.base_defense = defense
        self.damage_reduction = damage_reduction

        self.statuses = {
            "atk_boost": AttackBoost(),
            "def_boost": DefenseBoost(),
            "poison": PoisonStatus(),
        }
        self.ability = Ability("无", "无专属技能")

    @property
    def atk(self):
        """
        动态属性计算：每次读取 attacker.atk 时，都会执行这段代码。
        最终攻击力 = 基础攻击力 * 攻击强化状态的倍率
        """
        multiplier = self.statuses["atk_boost"].get_multiplier()
        return int(self.base_atk * multiplier)

    @property
    def defense(self):
        """
        每次读取 attacker.defense 或 defender.defense 时触发。
        最终防御力 = 基础防御力 * 防御强化状态的倍率
        """
        multiplier = self.statuses["def_boost"].get_multiplier()
        return int(self.base_defense * multiplier)

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
        self.base_atk = int(self.atk * 1.20)
        self.miss=0.2
        self.ability = LightAbility()

class WaterEntity(Entity):
    def __init__(self, name, max_hp, atk, defense, damage_reduction=0.0):
        super().__init__(name, "water", max_hp, atk, defense, damage_reduction)
        self.base_atk = int(self.atk * 1.10)
        self.base_defense = int(self.defense * 1.10)
        self.miss = 0.1
        self.ability = ShapableAbility()

class NourishAbility(Ability):
    """土系专属：每回合结束时，随机升级手中一张 Lv.0 卡牌"""
    def __init__(self):
        super().__init__("滋养", "每回合结束时，随机升级一张手牌")

    def on_turn_end(self, owner, deck=None):
        if not deck:
            return
        from card_hub import CardUpgradeManager
        candidates = [i for i, c in enumerate(deck) if c.level == 0]
        if not candidates:
            return
        idx = random.choice(candidates)
        old_card = deck[idx]
        new_card = CardUpgradeManager.upgrade_card(old_card, owner)
        deck[idx] = new_card
        print(f"   🌍 [滋养] {owner.name} 的手牌 [{old_card.name}] 自动升级为 [{new_card.name}] Lv.1")

class EarthEntity(Entity):
    def __init__(self, name, max_hp, atk, defense, damage_reduction=0.0):
        super().__init__(name, "earth", max_hp, atk, defense, damage_reduction)
        self.shield = 3
        self.ability = NourishAbility()

class MetalEntity(Entity):
    def __init__(self, name, max_hp, atk, defense, damage_reduction=0.0):
        super().__init__(name, "metal", max_hp, atk, defense, damage_reduction)
        self.base_defense = int(self.defense * 1.20)
        self.base_atk = int(self.atk * 1.20)
        self.sharp = 2

class WoodEntity(Entity):
    def __init__(self, name, max_hp, atk, defense, damage_reduction=0.0):
        super().__init__(name, "wood", max_hp, atk, defense, damage_reduction)
        self.heal=2
        self.base_defense = int(self.defense * 1.20)
        self.ability = StaticAbility()
