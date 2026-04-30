from utils import calculate_damage


class Skill:
    # 稍微优化：给 power 设个默认值 0，因为改变环境的牌可能不需要 power 参数
    def __init__(self, name, skill_type, power=0, num=1,env_effect=None,status_target=None):
        self.status_target = status_target
        self.name = name
        self.skill_type = skill_type
        self.power = power
        self.env_effect = env_effect
        self.num = num
        #num 是连击次数
    # 🌟【修复 1】：把 arena 加入到参数列表中
    def execute(self, caster, target=None, arena=None):
        """
        技能的核心执行逻辑。
        caster: 施法者 (Entity对象)
        target: 目标 (Entity对象)
        arena: 战场环境 (BattleEnvironment对象)
        """
        print(f"\n✨ [{caster.name}] 施放了技能：【{self.name}】！")

        if self.skill_type == "change_env" and self.env_effect:
            if arena:
                arena.change_weather(self.env_effect())
            else:
                print("   [错误] 未传入战场环境，无法施放环境卡！")

        elif self.skill_type == "attack":
            print(f"   -> 凝聚力量！技能威力倍率: {self.power}x")

            # 🌟【修复 2】：补上实际的伤害计算和扣血执行
            if target and arena:
                # 调用独立的伤害计算器（注意把 arena 传进去，好让天气起作用）
                damage = calculate_damage(attacker=caster, defender=target, arena=arena, skill_multiplier=self.power, atk_num=self.num)
                target.apply_damage(damage)
            else:
                print("攻击失败：没有合法的目标或战场环境！")

        elif self.skill_type == "heal":
            if target:
                heal_amount = int(self.power)
                target.hp += heal_amount
                target.hp = min(target.hp, target.max_hp)
                print(f"   -> 💚 [{target.name}] 恢复了 {heal_amount} 点 HP！当前 HP: {target.hp}")

        elif self.skill_type == "shield":
            caster.gain_shield(self.power)

        elif self.skill_type == "buff":
            if self.status_target in caster.statuses:
                # power 代表提升的级数
                caster.statuses[self.status_target].add_level(self.power)

        elif self.skill_type == "dispel":
            if target and self.status_target in target.statuses:
                print(f"   -> 施展了驱散魔法！试图清除目标的 [{self.status_target}]")
                target.statuses[self.status_target].clear()


