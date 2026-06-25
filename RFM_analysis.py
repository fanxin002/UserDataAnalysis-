# -*- coding: utf-8 -*-
"""
RFM用户分层分析
基于 UserBehavior 数据集，对购买用户进行 RFM 分层
- R (Recency): 最近一次购买距数据截止日的天数
- F (Frequency): 购买总次数
- M (Monetary): 由于无金额字段，使用购买的不同商品数替代（代表购买多样性/消费广度）
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os

# ==================== 全局配置 ====================
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

DB_PATH = r"C:\Users\22073\Desktop\UserDataAnalysis\UserBehavior_Clean.db"
SAVE_PATH = r"C:\Users\22073\Desktop\UserDataAnalysis\RFM用户分层分析.png"

# 项目统一配色
COLORS = {
    'blue': '#5470C6',
    'green': '#91CC75',
    'red': '#EE6666',
    'orange': '#FAC858',
    'purple': '#B07CC6',
    'cyan': '#73C0DE',
    'pink': '#FC8452',
    'light_blue': '#66B2FF',
}

# ==================== 数据获取 ====================
if not os.path.exists(DB_PATH):
    raise FileNotFoundError(f"数据库文件不存在，请检查路径：{DB_PATH}")

conn = sqlite3.connect(DB_PATH)

# 获取数据截止日期（最后一条购买记录的日期）
last_date_df = pd.read_sql_query("""
    SELECT MAX(DATE(datetime)) AS last_date
    FROM user_behavior
    WHERE behavior_type = 'buy'
""", conn)
DATA_END_DATE = last_date_df['last_date'].iloc[0]
print(f"数据截止日期: {DATA_END_DATE}")

# 获取每位购买用户的 RFM 原始指标
rfm_df = pd.read_sql_query("""
    SELECT 
        user_id,
        MAX(DATE(datetime)) AS last_buy_date,
        COUNT(*) AS frequency,
        COUNT(DISTINCT item_id) AS diversity,
        COUNT(DISTINCT category_id) AS category_cnt
    FROM user_behavior
    WHERE behavior_type = 'buy'
    GROUP BY user_id
""", conn)
conn.close()

print(f"购买用户总数: {len(rfm_df):,}")

# ==================== RFM 指标计算 ====================
# R: 最近一次购买距今的天数（越小越好）
rfm_df['recency'] = (pd.to_datetime(DATA_END_DATE) - pd.to_datetime(rfm_df['last_buy_date'])).dt.days

# F: 购买频次（越大越好）
rfm_df['frequency'] = rfm_df['frequency']

# M: 购买多样性——购买的不同商品数（越大越好，替代金额）
rfm_df['monetary'] = rfm_df['diversity']

# 输出基本统计
print(f"\n========== RFM 指标统计 ==========")
print(f"R (Recency) - 距最后购买天数:")
print(f"  均值: {rfm_df['recency'].mean():.1f}天 | 中位数: {rfm_df['recency'].median():.0f}天")
print(f"  最小: {rfm_df['recency'].min()}天 | 最大: {rfm_df['recency'].max()}天")
print(f"\nF (Frequency) - 购买频次:")
print(f"  均值: {rfm_df['frequency'].mean():.1f}次 | 中位数: {rfm_df['frequency'].median():.0f}次")
print(f"  最小: {rfm_df['frequency'].min()}次 | 最大: {rfm_df['frequency'].max()}次")
print(f"\nM (Monetary替代) - 购买商品多样性:")
print(f"  均值: {rfm_df['monetary'].mean():.1f}个 | 中位数: {rfm_df['monetary'].median():.0f}个")
print(f"  最小: {rfm_df['monetary'].min()}个 | 最大: {rfm_df['monetary'].max()}个")

# ==================== RFM 打分（五分位法） ====================
# R: 越小越好 → 打分时反向，1=最近购买（最好），5=最久未购买（最差）
# F: 越大越好 → 1=最少购买（最差），5=最多购买（最好）
# M: 越大越好 → 1=最少多样性（最差），5=最多多样性（最好）

try:
    rfm_df['R_score'] = pd.qcut(rfm_df['recency'], q=5, labels=[5, 4, 3, 2, 1]).astype(int)
except ValueError:
    # 如果recency分布太集中，用rank分桶
    rfm_df['R_score'] = pd.cut(rfm_df['recency'].rank(method='first'), bins=5, labels=[5, 4, 3, 2, 1]).astype(int)

try:
    rfm_df['F_score'] = pd.qcut(rfm_df['frequency'], q=5, labels=[1, 2, 3, 4, 5]).astype(int)
except ValueError:
    rfm_df['F_score'] = pd.cut(rfm_df['frequency'].rank(method='first'), bins=5, labels=[1, 2, 3, 4, 5]).astype(int)

try:
    rfm_df['M_score'] = pd.qcut(rfm_df['monetary'], q=5, labels=[1, 2, 3, 4, 5]).astype(int)
except ValueError:
    rfm_df['M_score'] = pd.cut(rfm_df['monetary'].rank(method='first'), bins=5, labels=[1, 2, 3, 4, 5]).astype(int)

# RFM 综合得分
rfm_df['RFM_score'] = rfm_df['R_score'] * 100 + rfm_df['F_score'] * 10 + rfm_df['M_score']

# ==================== 用户分层 ====================
def classify_user(r, f, m):
    """
    用户分层规则（基于R/F/M 1-5打分）：
    - 重要价值用户：R≥4, F≥4, M≥4 → 最近活跃、高频、高多样性
    - 重要发展用户：R≥4, F<4, M≥4 → 最近活跃、低频但高多样性
    - 重要保持用户：R<4, F≥4, M≥4 → 久未购买、但高频高多样性
    - 重要挽留用户：R<4, F<4, M≥4 → 久未购买、低频但高多样性
    - 一般价值用户：R≥4, F≥4, M<4 → 最近活跃、高频但低多样性
    - 一般发展用户：R≥4, F<4, M<4 → 最近活跃、低频低多样性
    - 一般保持用户：R<4, F≥4, M<4 → 久未购买、高频但低多样性
    - 一般挽留用户：R<4, F<4, M<4 → 久未购买、低频低多样性（流失风险最大）
    """
    if r >= 4 and f >= 4 and m >= 4:
        return '重要价值用户'
    elif r >= 4 and f < 4 and m >= 4:
        return '重要发展用户'
    elif r < 4 and f >= 4 and m >= 4:
        return '重要保持用户'
    elif r < 4 and f < 4 and m >= 4:
        return '重要挽留用户'
    elif r >= 4 and f >= 4 and m < 4:
        return '一般价值用户'
    elif r >= 4 and f < 4 and m < 4:
        return '一般发展用户'
    elif r < 4 and f >= 4 and m < 4:
        return '一般保持用户'
    else:
        return '一般挽留用户'

rfm_df['user_segment'] = rfm_df.apply(
    lambda row: classify_user(row['R_score'], row['F_score'], row['M_score']), axis=1
)

# ==================== 分层统计 ====================
segment_order = ['重要价值用户', '重要发展用户', '重要保持用户', '重要挽留用户',
                 '一般价值用户', '一般发展用户', '一般保持用户', '一般挽留用户']
segment_colors_map = {
    '重要价值用户': COLORS['blue'],
    '重要发展用户': COLORS['green'],
    '重要保持用户': COLORS['orange'],
    '重要挽留用户': COLORS['red'],
    '一般价值用户': COLORS['cyan'],
    '一般发展用户': COLORS['purple'],
    '一般保持用户': COLORS['pink'],
    '一般挽留用户': '#AAAAAA',
}

segment_stats = rfm_df['user_segment'].value_counts().reindex(segment_order).fillna(0).astype(int)
segment_pct = (segment_stats / segment_stats.sum() * 100).round(1)

print(f"\n========== 用户分层结果 ==========")
for seg in segment_order:
    cnt = segment_stats[seg]
    pct = segment_pct[seg]
    print(f"  {seg}: {cnt:,}人 ({pct}%)")

# ==================== 可视化（双图组合，和复购率分析风格统一）====================
important_count = sum(segment_stats[s] for s in segment_order if '重要' in s)
general_count = sum(segment_stats[s] for s in segment_order if '一般' in s)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# ---------- 左图: RFM用户分层饼图 ----------
pie_labels = ['重要价值用户', '重要保持用户', '一般发展用户', '一般挽留用户', '其他']
pie_sizes = [
    segment_stats.get('重要价值用户', 0),
    segment_stats.get('重要保持用户', 0),
    segment_stats.get('一般发展用户', 0),
    segment_stats.get('一般挽留用户', 0),
    segment_stats.sum() - segment_stats.get('重要价值用户', 0) - segment_stats.get('重要保持用户', 0) - segment_stats.get('一般发展用户', 0) - segment_stats.get('一般挽留用户', 0),
]
pie_colors = [COLORS['blue'], COLORS['orange'], COLORS['purple'], '#AAAAAA', COLORS['cyan']]
# 过滤掉为0的分类
filtered = [(l, s, c) for l, s, c in zip(pie_labels, pie_sizes, pie_colors) if s > 0]
pie_labels, pie_sizes, pie_colors = zip(*filtered) if filtered else ([], [], [])

ax1.pie(
    pie_sizes,
    labels=pie_labels,
    colors=pie_colors,
    autopct='%1.2f%%',
    startangle=90,
    textprops={'fontsize': 11, 'fontweight': 'bold'}
)
ax1.set_title('RFM用户价值分层分布', fontsize=14, fontweight='bold', pad=20)

# ---------- 右图: 各分层用户数柱状图 ----------
# 按用户数排序取Top分层展示
sorted_segments = segment_stats.sort_values(ascending=True)
bar_colors = [segment_colors_map.get(s, '#AAAAAA') for s in sorted_segments.index]

bars = ax2.barh(range(len(sorted_segments)), sorted_segments.values,
                color=bar_colors, edgecolor='black', linewidth=1.2, height=0.7)
ax2.set_yticks(range(len(sorted_segments)))
ax2.set_yticklabels(sorted_segments.index, fontsize=11)
ax2.set_xlabel('用户数', fontsize=11)
ax2.set_title('各分层用户数量', fontsize=14, fontweight='bold', pad=20)
ax2.invert_yaxis()
for bar in bars:
    width = bar.get_width()
    ax2.text(width + max(sorted_segments.values) * 0.01, bar.get_y() + bar.get_height() / 2,
             f'{int(width):,}', va='center', fontsize=10, fontweight='bold')
ax2.grid(axis='x', alpha=0.3)

# ==================== 保存输出 ====================
os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
plt.tight_layout()
plt.savefig(SAVE_PATH, dpi=150, bbox_inches='tight')
plt.show()

print(f"\n[OK] RFM用户分层分析图表已保存至：{SAVE_PATH}")

# ==================== 输出CSV用于后续运营 ====================
csv_path = r"C:\Users\22073\Desktop\UserDataAnalysis\RFM_User_Segments.csv"
rfm_df[['user_id', 'recency', 'frequency', 'monetary', 'R_score', 'F_score', 'M_score', 'RFM_score', 'user_segment']].to_csv(
    csv_path, index=False, encoding='utf-8-sig'
)
print(f"[OK] 用户分层明细数据已保存至：{csv_path}")

# ==================== 运营建议输出 ====================
print(f"""
================================================================
              >>> 基于RFM的运营建议 <<<
================================================================

  [1] 重要价值用户 ({segment_stats.get('重要价值用户',0):,}人, {segment_pct.get('重要价值用户',0)}%)
      -> 核心VIP，优先维护，提供专属权益和个性化推荐

  [2] 重要发展用户 ({segment_stats.get('重要发展用户',0):,}人, {segment_pct.get('重要发展用户',0)}%)
      -> 高消费潜力但购买频次低，推送限时优惠刺激复购

  [3] 重要保持用户 ({segment_stats.get('重要保持用户',0):,}人, {segment_pct.get('重要保持用户',0)}%)
      -> 曾经高频高消费但近期沉默，需要召回策略（优惠券/大促提醒）

  [4] 重要挽留用户 ({segment_stats.get('重要挽留用户',0):,}人, {segment_pct.get('重要挽留用户',0)}%)
      -> 高消费价值但活跃度和频次双低，需紧急干预（大力度优惠）

  [5] 一般价值用户 ({segment_stats.get('一般价值用户',0):,}人, {segment_pct.get('一般价值用户',0)}%)
      -> 活跃且高频但消费广度低，尝试品类交叉推荐提升客单价

  [6] 一般发展用户 ({segment_stats.get('一般发展用户',0):,}人, {segment_pct.get('一般发展用户',0)}%)
      -> 近期活跃但低频低消费，新用户引导和教育

  [7] 一般保持用户 ({segment_stats.get('一般保持用户',0):,}人, {segment_pct.get('一般保持用户',0)}%)
      -> 曾经活跃但近期沉默，常规营销唤醒

  [8] 一般挽留用户 ({segment_stats.get('一般挽留用户',0):,}人, {segment_pct.get('一般挽留用户',0)}%)
      -> 流失边缘用户，低成本触达尝试挽回，评估是否值得继续投入

================================================================""")
