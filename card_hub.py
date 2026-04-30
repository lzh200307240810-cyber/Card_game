import random

from environment import RainEnvironment, LavaEnvironment
from skill import Skill


class Card:
    def __init__(self, card_id, name, card_type, description, skill):
        # --- 牌面信息 (UI与前端展示用到) ---
        self.card_id = card_id  # 卡牌编号 (方便以后配图或查Excel表)
        self.name = name  # 卡牌名称
        self.card_type = card_type  # 类型：比如 "Attack"(攻击牌), "Skill"(技能牌), "Power"(能力牌)
        self.description = description  # 卡牌描述文本

        # --- 后台逻辑 (绑定我们之前写的 Skill 类) ---
        self.skill = skill  # 这张卡牌绑定的具体效果

    def play(self, caster, target, arena):
        """
        打出卡牌的动作。
        在这里进行费用结算，然后再触发内部的技能。
        """

        # 2. 触发牌面上的实际效果文本
        print(f"   📜 卡牌效果: {self.description}")

        # 3. 调用底层的技能引擎来执行真实逻辑
        # 把施法者、目标、环境原封不动地传给内部的 skill
        self.skill.execute(caster=caster, target=target, arena=arena)

        return True  # 打牌成功

class DeckManager:
    @staticmethod
    def get_random_cards(count=5):
        """从大牌库中随机抽取 count 张不重复的卡牌副本"""
        # 获取所有卡牌的 ID 列表
        all_ids = list(ALL_CARDS.keys())

        # 随机抽取 ID
        selected_ids = random.sample(all_ids, count)

        # 根据 ID 返回卡牌对象列表
        return [ALL_CARDS[cid] for cid in selected_ids]

    @staticmethod
    def get_elemental_deck(element, count=5):
        """进阶：只抽取特定属性的卡牌 (例如开局选职业)"""
        filtered_ids = [cid for cid in ALL_CARDS.keys() if cid.startswith(element[0].upper())]
        # 如果该系牌不够，就从全库补齐
        selected_ids = random.sample(filtered_ids, min(len(filtered_ids), count))
        return [ALL_CARDS[cid] for cid in selected_ids]




s_atk_low = Skill("轻微打击", "attack", power=1.0)
s_atk_mid = Skill("标准打击", "attack", power=1.5)
s_atk_high = Skill("全力重击", "attack", power=2.5)

s_shield_1 = Skill("格挡", "shield", power=1)
s_shield_2 = Skill("多重结界", "shield", power=2)

s_buff_atk = Skill("战意激增", "buff", power=1, status_target="atk_boost")
s_dispel = Skill("净化之光", "dispel", status_target="atk_boost")

s_env_rain = Skill("降雨咒", "change_env", env_effect=RainEnvironment)
s_env_lava = Skill("火山召唤", "change_env", env_effect=LavaEnvironment)

# --- 定义全量卡牌大仓库 (以 ID 为 Key) ---
ALL_CARDS = {
    # 金系卡牌 (Metal)
    "M001": Card("M001", "金芒刺", "Attack", "金系初级攻击，造成1.0倍伤害", s_atk_low),
    "M002": Card("M002", "贯穿金枪",  "Attack", "金系高级攻击，造成2.5倍伤害", s_atk_high),
    "M003": Card("M003", "固若金汤",  "Shield", "获得1次永久护盾次数", s_shield_1),

    # 木系卡牌 (Wood)
    "W001": Card("W001", "枯木逢春", "Heal", "恢复40点HP", Skill("治疗", "heal", power=40)),
    "W002": Card("W002", "藤蔓束缚", "Buff", "强化自身攻击等级", s_buff_atk),

    # 水系卡牌 (Water)
    "T001": Card("T001", "水龙卷", "Attack", "水系中级攻击，造成1.5倍伤害", s_atk_mid),
    "T002": Card("T002", "祈雨仪式", "ChangeEnv", "将环境变为【倾盆大雨】", s_env_rain),

    # 火系卡牌 (Fire)
    "F001": Card("F001", "烈焰波", "Attack", "火系中级攻击，造成1.5倍伤害", s_atk_mid),
    "F002": Card("F002", "熔岩地裂",  "ChangeEnv", "将环境变为【滚滚熔岩】", s_env_lava),

    # 土系卡牌 (Earth)
    "E001": Card("E001", "大地护盾", "Shield", "获得2次永久护盾次数", s_shield_2),
    "E002": Card("E002", "重力压制", "Dispel", "清除目标的攻击强化状态", s_dispel),
}
