import random
from card_hub import ALL_CARDS


class Card:
    def __init__(self, card_id, name, cost, card_type, description, skill):
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
