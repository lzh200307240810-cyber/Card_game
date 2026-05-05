import random

from card_hub import DeckManager, NORMAL_CARDS, LEVEL0_ENEMY_CARD, CardUpgradeManager
from environment import CleanEnvironment, BattleEnvironment, RainEnvironment
from utils import WaterEntity, FireEntity, StaticAbility, WoodEntity

POKER_ORDER = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']


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
        print(
            f"🧑 【{self.player.name}】({self.player.element}) | HP: {self.player.hp}/{self.player.max_hp} | 🛡️ 护盾: {self.player.shield}")
        print(
            f"👹 【{self.enemy.name}】({self.enemy.element}) | HP: {self.enemy.hp}/{self.enemy.max_hp} | 🛡️ 护盾: {self.enemy.shield}")

        if self.arena.see_all:
            print("   👹 敌方手牌：")
            for i, card in enumerate(self.enemy_deck):
                poker_display = f"[{card.poker_value}]" if card.poker_value else ""
                print(f"      [{i + 1}] 【{card.name}】({card.card_type}) /{poker_display}/")

        print("=" * 50)

    def player_choose_ability(self):
        """询问玩家是否发动主动技能"""
        ability = self.player.ability
        if isinstance(ability, StaticAbility) and ability.can_activate():
            print(f"\n🌿 你可以发动专属技能【{ability.name}】：{ability.description}")
            while True:
                choice = input("是否发动？(y/n): ").strip().lower()
                if choice == 'y':
                    return True
                elif choice == 'n':
                    return False
                print("⚠️ 请输入 y 或 n！")
        return False

    def enemy_choose_ability(self):
        """敌人AI决定是否发动主动技能"""
        ability = self.enemy.ability
        if isinstance(ability, StaticAbility) and ability.can_activate():
            # HP 低于 40% 时发动
            if self.enemy.hp < self.enemy.max_hp * 0.4:
                return True
        return False

    def player_choose_upgrade(self):
        """玩家选择一张手牌进行升级"""
        print("\n⬆️ 卡牌升级时间！选择一张手牌升级为 Lv.1 属性卡牌：")
        for i, card in enumerate(self.player_deck):
            poker_display = f"[{card.poker_value}]" if card.poker_value else ""
            print(f"  [{i + 1}]  【{card.name}】 (类型: {card.card_type} | Lv.{card.level}) /{poker_display}/")

        while True:
            choice = input(f"请选择要升级的卡牌 (1-{len(self.player_deck)}): ")
            if choice.isdigit() and 1 <= int(choice) <= len(self.player_deck):
                idx = int(choice) - 1
                old_card = self.player_deck[idx]
                new_card = CardUpgradeManager.upgrade_card(old_card, self.player)
                self.player_deck[idx] = new_card
                return
            print("⚠️ 输入无效，请重新输入！")

    def enemy_choose_upgrade(self):
        """敌人AI选择一张手牌进行升级（优先升级非Lv.1的牌）"""
        candidates = [i for i, c in enumerate(self.enemy_deck) if c.level == 0]
        if not candidates:
            return
        idx = random.choice(candidates)
        old_card = self.enemy_deck[idx]
        new_card = CardUpgradeManager.upgrade_card(old_card, self.enemy)
        self.enemy_deck[idx] = new_card

    def player_choose_card(self):
        """处理玩家的交互输入"""
        print("\n👇 你的手牌：")
        for i, card in enumerate(self.player_deck):
            poker_display = f"[{card.poker_value}]" if card.poker_value else ""
            print(f"  [{i + 1}]  【{card.name}】 (类型: {card.card_type} | 描述: {card.description}) /{poker_display}/")

        while True:
            choice = input(f"请输入你要打出的卡牌编号 (1-{len(self.player_deck)}): ")
            if choice.isdigit() and 1 <= int(choice) <= len(self.player_deck):
                return self.player_deck[int(choice) - 1]
            print("⚠️ 输入无效，请重新输入正确的数字！")

    def determine_first_mover(self, player_card, enemy_card):
        """根据双方打出的卡牌点数决定先手，返回 "player" 或 "enemy" """
        p_rank = POKER_ORDER.index(player_card.poker_value)
        e_rank = POKER_ORDER.index(enemy_card.poker_value)

        print(f"\n🃏 点数对决！")
        print(f"   🧑 你打出 【{player_card.name}】[{player_card.poker_value}]")
        print(f"   👹 敌人打出 【{enemy_card.name}】[{enemy_card.poker_value}]")

        if p_rank > e_rank:
            print(f"   → 🧑 [{player_card.poker_value}] > 👹 [{enemy_card.poker_value}]，你先行动！")
            return "player"
        elif e_rank > p_rank:
            print(f"   → 👹 [{enemy_card.poker_value}] > 🧑 [{player_card.poker_value}]，敌人先行动！")
            return "enemy"
        else:
            winner = random.choice(["player", "enemy"])
            name = "你" if winner == "player" else "敌人"
            print(f"   → 平局！随机决定 → {name}先行动！")
            return winner

    def execute_turn(self, actor, target, card, actor_deck, card_pool):
        """执行一次出牌：打出卡牌 → 移除手牌 → 抽新牌"""
        card.play(caster=actor, target=target, arena=self.arena)

        # 移除已打出的牌，从对应牌库抽1张补充
        actor_deck.remove(card)
        new_card = DeckManager.draw_one_card(card_pool)
        actor_deck.append(new_card)
        print(f"   📥 [{actor.name}] 抽取了新牌：【{new_card.name}】[{new_card.poker_value}]")

    def run_game(self):
        """启动游戏的主循环"""
        print("\n⚔️ 战斗正式开始！⚔️")

        while self.player.hp > 0 and self.enemy.hp > 0:
            print(f"\n========== 🔔 第 {self.round} 大回合开始 ==========")

            # 环境回合开始效果
            self.arena.current_weather.on_turn_start(self.player, self.arena)
            self.arena.current_weather.on_turn_start(self.enemy, self.arena)

            # 中毒伤害
            self.player.statuses["poison"].tick(self.player)
            self.enemy.statuses["poison"].tick(self.enemy)

            # 专属技能触发
            self.player.ability.on_turn_start(self.player, self.enemy, self.arena)
            self.enemy.ability.on_turn_start(self.enemy, self.player, self.arena)

            if self.player.hp <= 0 or self.enemy.hp <= 0:
                print("\n💀 战斗结束！有人倒在了残酷的战场环境下...")
                break

            self.display_status()

            # 1. 检查主动技能发动
            player_activate = self.player_choose_ability()
            enemy_activate = self.enemy_choose_ability()

            if player_activate:
                self.player.ability.on_activate(self.player, self.enemy, self.arena)
            if enemy_activate:
                self.enemy.ability.on_activate(self.enemy, self.player, self.arena)

            if self.arena.skip_turn:
                # 静止发动：双方本回合不能出牌，但正常抽卡
                print("\n⏸️ 本回合被【静止】封锁，双方无法出牌！")
                new_p = DeckManager.draw_one_card(NORMAL_CARDS)
                self.player_deck.append(new_p)
                print(f"   📥 [{self.player.name}] 抽取了新牌：【{new_p.name}】[{new_p.poker_value}]")
                new_e = DeckManager.draw_one_card(LEVEL0_ENEMY_CARD)
                self.enemy_deck.append(new_e)
                print(f"   📥 [{self.enemy.name}] 抽取了新牌：【{new_e.name}】[{new_e.poker_value}]")
            else:
                # 2. 正常选牌
                player_card = self.player_choose_card()
                enemy_card = random.choice(self.enemy_deck)

                # 3. 根据打出的卡牌点数决定先手
                first = self.determine_first_mover(player_card, enemy_card)

                print("\n>>> 双方已锁定行动，开始结算！ <<<")

                # 4. 按先手顺序结算
                if first == "player":
                    self.execute_turn(self.player, self.enemy, player_card, self.player_deck, NORMAL_CARDS)
                    if self.enemy.hp <= 0:
                        print("\n🎉 胜利！你击败了敌人！")
                        break
                    self.execute_turn(self.enemy, self.player, enemy_card, self.enemy_deck, LEVEL0_ENEMY_CARD)
                    if self.player.hp <= 0:
                        print("\n💀 失败！你倒下了...")
                        break
                else:
                    self.execute_turn(self.enemy, self.player, enemy_card, self.enemy_deck, LEVEL0_ENEMY_CARD)
                    if self.player.hp <= 0:
                        print("\n💀 失败！你倒下了...")
                        break
                    self.execute_turn(self.player, self.enemy, player_card, self.player_deck, NORMAL_CARDS)
                    if self.enemy.hp <= 0:
                        print("\n🎉 胜利！你击败了敌人！")
                        break

            # 5. 专属技能回合结束处理（回血、冷却递减）
            if isinstance(self.player.ability, StaticAbility):
                self.player.ability.on_turn_end(self.player)
            if isinstance(self.enemy.ability, StaticAbility):
                self.enemy.ability.on_turn_end(self.enemy)
            self.arena.skip_turn = False

            # 6. 第3回合结束时，双方各升级一张手牌
            if self.round == 3:
                self.player_choose_upgrade()
                self.enemy_choose_upgrade()

            # 7. 环境倒计时推进
            if not self.arena.current_weather.is_permanent:
                self.arena.current_weather.duration -= 1
                if self.arena.current_weather.duration <= 0:
                    print(f"\n🌤️ 环境【{self.arena.current_weather.name}】持续时间结束，天气恢复正常！")
                    self.arena.change_weather(CleanEnvironment())

            self.round += 1


# ==========================================
# 🎮 启动游戏引擎！
# ==========================================
if __name__ == "__main__":
    arena = BattleEnvironment()
    hero = WoodEntity("木", max_hp=300, atk=50, defense=20)
    boss = FireEntity("火", max_hp=500, atk=60, defense=30)

    # 玩家从 NORMAL_CARDS 抽5张
    player_starting_hand = DeckManager.get_cards_from_deck(NORMAL_CARDS, 5)

    # 敌人从 LEVEL0_ENEMY_CARD 抽3张
    enemy_starting_hand = DeckManager.get_cards_from_deck(LEVEL0_ENEMY_CARD, 3)

    game = GameEngine(
        player=hero,
        enemy=boss,
        arena=arena,
        player_deck=player_starting_hand,
        enemy_deck=enemy_starting_hand
    )
    game.run_game()
