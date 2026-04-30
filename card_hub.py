from cards import Card
from environment import RainEnvironment, LavaEnvironment
from skill import Skill

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
    "M001": Card("M001", "金芒刺", 1, "Attack", "金系初级攻击，造成1.0倍伤害", s_atk_low),
    "M002": Card("M002", "贯穿金枪", 3, "Attack", "金系高级攻击，造成2.5倍伤害", s_atk_high),
    "M003": Card("M003", "固若金汤", 2, "Shield", "获得1次永久护盾次数", s_shield_1),

    # 木系卡牌 (Wood)
    "W001": Card("W001", "枯木逢春", 2, "Heal", "恢复40点HP", Skill("治疗", "heal", power=40)),
    "W002": Card("W002", "藤蔓束缚", 1, "Buff", "强化自身攻击等级", s_buff_atk),

    # 水系卡牌 (Water)
    "T001": Card("T001", "水龙卷", 2, "Attack", "水系中级攻击，造成1.5倍伤害", s_atk_mid),
    "T002": Card("T002", "祈雨仪式", 2, "ChangeEnv", "将环境变为【倾盆大雨】", s_env_rain),

    # 火系卡牌 (Fire)
    "F001": Card("F001", "烈焰波", 2, "Attack", "火系中级攻击，造成1.5倍伤害", s_atk_mid),
    "F002": Card("F002", "熔岩地裂", 3, "ChangeEnv", "将环境变为【滚滚熔岩】", s_env_lava),

    # 土系卡牌 (Earth)
    "E001": Card("E001", "大地护盾", 2, "Shield", "获得2次永久护盾次数", s_shield_2),
    "E002": Card("E002", "重力压制", 2, "Dispel", "清除目标的攻击强化状态", s_dispel),
}