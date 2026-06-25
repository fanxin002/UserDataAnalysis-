import sqlite3
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from datetime import timedelta

db_path = r"C:\Users\22073\Desktop\UserDataAnalysis\UserBehavior_Clean.db"

conn = sqlite3.connect(db_path)
# 关键修正：UTC时间+8小时=北京时间，然后取小时
data = conn.execute("""
    SELECT 
        CASE 
            WHEN CAST(SUBSTR(datetime,12,2) AS INTEGER) + 8 >= 24 
            THEN CAST(CAST(SUBSTR(datetime,12,2) AS INTEGER) + 8 - 24 AS TEXT)
            ELSE CAST(CAST(SUBSTR(datetime,12,2) AS INTEGER) + 8 AS TEXT)
        END AS bj_hour,
        COUNT(*) as pv,
        COUNT(DISTINCT user_id) as uv
    FROM user_behavior 
    WHERE behavior_type='pv' 
    GROUP BY bj_hour 
    ORDER BY bj_hour
""").fetchall()
conn.close()

# 补全24小时数据（有些小时可能为0）
hours = [str(i).zfill(2) for i in range(24)]
pv_dict = {h:0 for h in hours}
uv_dict = {h:0 for h in hours}

for row in data:
    hour = row[0].zfill(2)
    pv_dict[hour] = row[1]
    uv_dict[hour] = row[2]

pv = [pv_dict[h] for h in hours]
uv = [uv_dict[h] for h in hours]

# 画图
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

fig, ax1 = plt.subplots(figsize=(14,7))

ax1.plot(hours, pv, color='#1f77b4', marker='o', linewidth=2, label='PV')
ax1.set_xlabel('北京时间（小时）')
ax1.set_ylabel('PV（万次）', color='#1f77b4')
ax1.tick_params(axis='y', labelcolor='#1f77b4')
ax1.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{x/10000:.1f}'))
ax1.set_xticks(range(24))

ax2 = ax1.twinx()
ax2.plot(hours, uv, color='#ff7f0e', marker='s', linewidth=2, label='UV')
ax2.set_ylabel('UV（万人）', color='#ff7f0e')
ax2.tick_params(axis='y', labelcolor='#ff7f0e')
ax2.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{x/10000:.1f}'))

plt.title('24小时PV/UV时段分布（北京时间）')
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
plt.grid(linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('24小时PV_UV_北京时间.png', dpi=150)
plt.show()

print("修正时区后的时段分布已保存")
print("预计晚8-10点（20-22时）会出现峰值")