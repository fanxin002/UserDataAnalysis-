import sqlite3
import matplotlib.pyplot as plt

db = r"C:\Users\22073\Desktop\UserDataAnalysis\UserBehavior_Clean.db"
conn = sqlite3.connect(db)
data = conn.execute("""
    SELECT SUBSTR(datetime,1,10) as day, COUNT(*) as pv, COUNT(DISTINCT user_id) as uv
    FROM user_behavior WHERE behavior_type='pv' GROUP BY day ORDER BY day
""").fetchall()
conn.close()

plt.rcParams['font.sans-serif'] = ['SimHei']  # 中文不乱码
plt.figure(figsize=(12,6))
plt.plot([x[0] for x in data], [x[1] for x in data], label='PV', marker='o')
plt.plot([x[0] for x in data], [x[2] for x in data], label='UV', marker='s')
plt.xticks(rotation=45)
plt.xlabel('日期')
plt.ylabel('数量')
plt.title('每日PV/UV趋势')
plt.legend()
plt.grid(linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('PV_UV趋势.png', dpi=150)
plt.show()
print('图已保存为 PV_UV趋势.png')