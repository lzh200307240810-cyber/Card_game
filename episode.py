import random

from cards import DeckManager
from environment import CleanEnvironment, BattleEnvironment, RainEnvironment
from skill import Skill
from utils import WaterEntity, FireEntity


class GameEngine:
    def __init__(self, player, enemy, arena, player_deck, enemy_deck):
        self.player = player
        self.enemy = enemy
        self.arena = arena

        # 双方的“牌库”或“技能列表”
        self.player_deck = player_deck
        self.enemy_deck = enemy_deck

        self.round = 1

    def display_status(self):
        """展示当前的战况面板"""
        print("\n" + "=" * 50)
        print(f"🌍 当前战场环境: 【{self.arena.current_weather.name}】")
        print(
            f"🧑 【{self.player.name}】({self.player.element}) | HP: {self.player.hp}/{self.player.max_hp} | 🛡️ 护盾: {self.player.shield}")
        print(
            f"👹 【{self.enemy.name}】({self.enemy.element}) | HP: {self.enemy.hp}/{self.enemy.max_hp} | 🛡️ 护盾: {self.enemy.shield}")
        print("=" * 50)

    def player_choose_card(self):
        """处理玩家的交互输入"""
        print("\n👇 你的手牌：")
        for i, card in enumerate(self.player_deck):
            print(f"  [{i + 1}] {card.name} (类型: {card.skill_type})")

        while True:
            choice = input(f"请输入你要打出的卡牌编号 (1-{len(self.player_deck)}): ")
            if choice.isdigit() and 1 <= int(choice) <= len(self.player_deck):
                return self.player_deck[int(choice) - 1]
            print("⚠️ 输入无效，请重新输入正确的数字！")

    def run_game(self):
        """启动游戏的主循环"""
        print("\n⚔️ 战斗正式开始！⚔️")

        # 只要双方都活着，循环就一直进行
        while self.player.hp > 0 and self.enemy.hp > 0:
            print(f"\n========== 🔔 第 {self.round} 大回合开始 ==========")
            self.display_status()

            # 1. 玩家选牌 (等待终端输入)
            player_card = self.player_choose_card()

            # 2. 敌人选牌 (这里写一个简单的 AI：从它的牌库里随机抽一张)
            enemy_card = random.choice(self.enemy_deck)

            print("\n>>> 双方已锁定行动，开始结算！ <<<")

            # 3. 结算阶段
            # (在目前的简化版里，我们默认玩家永远先出手。如果敌人被玩家秒杀了，敌人就不出手了)

            # 玩家执行卡牌
            player_card.execute(caster=self.player, target=self.enemy, arena=self.arena)
            if self.enemy.hp <= 0:
                print("\n🎉 胜利！你击败了敌人！")
                break

            # 敌人执行卡牌
            enemy_card.execute(caster=self.enemy, target=self.player, arena=self.arena)
            if self.player.hp <= 0:
                print("\n💀 失败！你倒下了...")
                break

            # 4. 回合结束的清理工作
            # 临时护盾在回合结束时清零
            if self.player.shield > 0:
                print(f"   💨 {self.player.name} 的 {self.player.shield} 点临时护盾消散了。")
                self.player.shield = 0
            if self.enemy.shield > 0:
                print(f"   💨 {self.enemy.name} 的 {self.enemy.shield} 点临时护盾消散了。")
                self.enemy.shield = 0

            # 环境倒计时推进
            if not self.arena.current_weather.is_permanent:
                self.arena.current_weather.duration -= 1
                if self.arena.current_weather.duration <= 0:
                    print(f"\n🌤️ 环境【{self.arena.current_weather.name}】持续时间结束，天气恢复正常！")
                    # 这里假设你有 CleanEnvironment 类
                    self.arena.change_weather(CleanEnvironment())

            self.round += 1


# ==========================================
# 🎮 启动游戏引擎！
# ==========================================
if __name__ == "__main__":
    # 实例化战场、角色 (确保你已经引入了之前写的 Entity, Skill, BattleEnvironment 等类)
    arena = BattleEnvironment()
    hero = WaterEntity("水", max_hp=300, atk=50, defense=20)
    boss = FireEntity("火",  max_hp=500, atk=60, defense=30)

    player_starting_hand = DeckManager.get_random_cards(5)

    # 敌人也可以随机分发一些卡牌
    enemy_starting_hand = DeckManager.get_random_cards(3)

    game = GameEngine(
        player=hero,
        enemy=boss,
        arena=arena,
        player_deck=player_starting_hand,
        enemy_deck=enemy_starting_hand
    )
