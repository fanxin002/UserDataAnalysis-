import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False
DB_PATH = r"C:\Users\22073\Desktop\UserDataAnalysis\UserBehavior_Clean.db"
SAVE_PATH = r"C:\Users\22073\Desktop\UserDataAnalysis\复购率分析.png"



if not os.path.exists(DB_PATH):
    raise FileNotFoundError(f"数据库文件不存在，请检查路径：{DB_PATH}")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_behavior'")
if not cursor.fetchone():
    conn.close()
    raise ValueError("数据库中不存在user_behavior表，请确认数据已导入")


user_buy_cnt_df = pd.read_sql_query("""
    SELECT 
        user_id,
        COUNT(*) AS buy_cnt  -- 每个用户的购买总次数
    FROM user_behavior
    WHERE behavior_type = 'buy'
    GROUP BY user_id
""", conn)
conn.close()

# ==================== 指标计算（逻辑透明，无黑盒）====================
total_buyers = len(user_buy_cnt_df)  # 总购买用户数
repeat_buyers = user_buy_cnt_df[user_buy_cnt_df['buy_cnt'] >= 2].shape[0]  # 复购用户数
repurchase_rate = repeat_buyers / total_buyers if total_buyers > 0 else 0

freq_dist = user_buy_cnt_df['buy_cnt'].value_counts().sort_index()
freq_1 = freq_dist.get(1, 0)  # 购买1次用户数
freq_2 = freq_dist.get(2, 0)  # 购买2次用户数
freq_3plus = freq_dist[freq_dist.index >= 3].sum()  # 购买3次及以上用户数

# ==================== 可视化（双图组合，专业度拉满，配色和之前项目统一）====================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

ax1.pie(
    [total_buyers - repeat_buyers, repeat_buyers],
    labels=['首次购买用户', '复购用户'],
    colors=['#5470C6', '#91CC75'],  # 沿用项目统一配色
    autopct='%1.2f%%',
    startangle=90,
    textprops={'fontsize': 12, 'fontweight': 'bold'}
)
ax1.set_title('用户复购率分布', fontsize=14, fontweight='bold', pad=20)

bar_width = 0.6
x_pos = [0, 1, 2]
bar_values = [freq_1, freq_2, freq_3plus]
bar_labels = ['1次购买', '2次购买', '≥3次购买']

bars = ax2.bar(x_pos, bar_values, width=bar_width, color='#66B2FF', edgecolor='black', linewidth=1.2)
ax2.set_xticks(x_pos)
ax2.set_xticklabels(bar_labels, fontsize=11)
ax2.set_ylabel('用户数', fontsize=11)
ax2.set_title('复购频次分布', fontsize=14, fontweight='bold', pad=20)
# 柱顶加数值标签
for bar in bars:
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height + 0.005*max(bar_values),
             f'{int(height):,}', ha='center', va='bottom', fontsize=10, fontweight='bold')
ax2.grid(axis='y', alpha=0.3)

# 保存输出
os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
plt.tight_layout()
plt.savefig(SAVE_PATH, dpi=150, bbox_inches='tight')
plt.show()

print(f"📊 复购率分析结果：")
print(f"1. 总购买用户数：{total_buyers:,}")
print(f"2. 复购用户数：{repeat_buyers:,}")
print(f"3. 用户复购率：{repurchase_rate:.2%}")
print(f"4. 复购频次分布：1次购买占比{freq_1/total_buyers:.2%}，2次购买占比{freq_2/total_buyers:.2%}，≥3次购买占比{freq_3plus/total_buyers:.2%}")
print(f"📁 图表保存路径：{SAVE_PATH}")