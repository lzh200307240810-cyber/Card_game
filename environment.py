import random

def generate_starting_environment():
    """
    使用 random.choices 进行加权随机。
    假设我们希望 70% 是白板环境，15% 是雨天，15% 是熔岩。
    """
    env_pool = [CleanEnvironment, RainEnvironment, LavaEnvironment]
    weights = [90, 5, 5]  # 权重设置

    # choices 返回的是一个列表，我们取第一个 [0]，然后加上 () 实例化它
    ChosenEnvClass = random.choices(env_pool, weights=weights)[0]
    return ChosenEnvClass()

class BaseEnvironment:
    # 新增 duration 参数，默认值为 4
    def __init__(self, name, duration=4):
        self.name = name
        self.duration = duration
        self.is_permanent = False # 如果你想做永久环境，可以加个这个开关

    def on_turn_start(self, entity, arena): pass
    def modify_damage(self, attacker, defender, current_damage, arena): return current_damage

class CleanEnvironment(BaseEnvironment):
    def __init__(self):
        super().__init__("风和日丽 ☀️", duration=999)
        self.is_permanent = True


class RainEnvironment(BaseEnvironment):
    def __init__(self):
        # 调用父类，明确设定寿命为 4
        super().__init__("倾盆大雨", duration=4)

    def modify_damage(self, attacker, defender, current_damage, arena):
        if attacker.element == "water": return current_damage * 1.5
        if attacker.element == "fire": return current_damage * 0.5
        return current_damage


class LavaEnvironment(BaseEnvironment):
    def __init__(self):
        super().__init__("滚滚熔岩 🌋",duration=4)

    def on_turn_start(self, entity, arena):
        if entity.element != "fire":
            arena.log(f"   [环境] {entity.name} 被熔岩烫伤，扣除 15 点生命！")
            entity.apply_damage(15)

class BattleEnvironment:
    def __init__(self, start_env=CleanEnvironment()):
        self.current_weather = start_env
        self.turn_count = 1
        self.combatants = []
        self.current_actor_index = 0
        self.see_all=False

    def log(self, message):
        print(message)

    def change_weather(self, new_weather):
        self.current_weather = new_weather
        self.log(f"\n🌪️ [系统] 战场环境变成了：【{self.current_weather.name}】(持续 {self.current_weather.duration} 回合)")

    def pass_turn(self):
        # 1. 当前角色回合结束 (省略之前的逻辑...)

        # 2. 推进索引
        self.current_actor_index += 1

        # 3. 所有人行动完毕，进入下一个【大回合】！
        if self.current_actor_index >= len(self.combatants):
            self.current_actor_index = 0
            self.turn_count += 1
            self.log(f"\n🌎 ===== 战场进入第 {self.turn_count} 大回合 =====")

            # 🌟【核心倒计时逻辑】🌟
            if not self.current_weather.is_permanent:
                self.current_weather.duration -= 1

                if self.current_weather.duration > 0:
                    self.log(f"   ☁️ 环境【{self.current_weather.name}】还剩 {self.current_weather.duration} 回合。")
                else:
                    # 寿命归零，强制切回白板环境！
                    self.log(f"   🌤️ 环境【{self.current_weather.name}】效果已消散！天气恢复正常。")
                    self.current_weather = CleanEnvironment()

        # 4. 下一个角色回合开始 (省略之前的逻辑...)
