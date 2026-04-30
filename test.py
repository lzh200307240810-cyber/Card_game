import random
from environment import BattleEnvironment, RainEnvironment, CleanEnvironment
from skill import Skill
from utils import Entity, WaterEntity, FireEntity


class GameEngine:
    def __init__(self, player, enemy, arena, player_deck, enemy_deck):
        self.player = player
        self.enemy = enemy
        self.arena = arena

        self.player_deck = player_deck
        self.enemy_deck = enemy_deck

        self.round = 1

    def display_status(self):
        """展示当前的战况面板"""
        print("\n" + "=" * 50)
        print(f"🌍 当前战场环境: 【{self.arena.current_weather.name}】")
        # 护盾现在是永久属性了，所以面板展示很重要
        print(
            f"🧑 【{self.player.name}】({self.player.element}) | HP: {self.player.hp}/{self.player.max_hp} | 🛡️ 护盾状态: {self.player.shield}")
        print(
            f"👹 【{self.enemy.name}】({self.enemy.element}) | HP: {self.enemy.hp}/{self.enemy.max_hp} | 🛡️ 护盾状态: {self.enemy.shield}")
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
        print("\n⚔️ 战斗正式开始！⚔️ (规则提示：护盾为永久状态，不随回合消散)")

        while self.player.hp > 0 and self.enemy.hp > 0:
            print(f"\n========== 🔔 第 {self.round} 大回合开始 ==========")
            self.display_status()

            # 1. 玩家选牌
            player_card = self.player_choose_card()

            # 2. 敌人选牌 (简单的 AI：随机抽一张)
            enemy_card = random.choice(self.enemy_deck)

            print("\n>>> 双方已锁定行动，开始结算！ <<<")

            # 3. 结算阶段
            player_card.execute(caster=self.player, target=self.enemy, arena=self.arena)
            if self.enemy.hp <= 0:
                print("\n🎉 胜利！你击败了敌人！")
                break

            enemy_card.execute(caster=self.enemy, target=self.player, arena=self.arena)
            if self.player.hp <= 0:
                print("\n💀 失败！你倒下了...")
                break

            # 4. 回合结束的清理工作
            # 【核心修改点】：删除了 self.player.shield = 0 的护盾清零逻辑
            # 现在护盾会一直保留，直到被你的“完全抵挡一次伤害”机制消耗掉！

            # 环境倒计时推进依然保留
            if not self.arena.current_weather.is_permanent:
                self.arena.current_weather.duration -= 1
                if self.arena.current_weather.duration <= 0:
                    print(f"\n🌤️ 环境【{self.arena.current_weather.name}】持续时间结束，天气恢复正常！")
                    self.arena.change_weather(CleanEnvironment())

            self.round += 1


if __name__ == "__main__":
    # 实例化战场与角色
    arena = BattleEnvironment()
    hero = Entity("水魔法师", element="water", max_hp=300, atk=50, defense=20)
    boss = Entity("熔岩恶魔", element="fire", max_hp=500, atk=60, defense=30)

    # 玩家卡组 (修改了护盾描述，适应新的机制)
    p_deck = [
        Skill("水流冲击", skill_type="attack", power=1.5),
        Skill("水之结界", skill_type="shield", power=1),
        Skill("祈雨舞", skill_type="change_env", env_effect=RainEnvironment)
    ]

    # 敌人卡组
    e_deck = [
        Skill("恶魔猛击", skill_type="attack", power=1.2),
        Skill("熔岩护甲", skill_type="shield", power=0.2)
    ]

    game = GameEngine(player=hero, enemy=boss, arena=arena, player_deck=p_deck, enemy_deck=e_deck)
    game.run_game()