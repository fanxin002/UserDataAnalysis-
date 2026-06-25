import sqlite3
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ==================== 全局固定配置（100%写死，不受数据影响，保证左右尺寸完全一致）====================
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# 绘图尺寸参数全部固定，和数据无关
FIG_SIZE = (14, 9)           # 总画布固定大小
NODE_WIDTH = 2.2             # 所有节点宽度固定（左右完全一致）
NODE_HEIGHT = 0.9            # 所有节点高度固定
VERTICAL_GAP = 1.2           # 节点之间垂直间距固定
ARROW_COLOR = '#666666'      # 箭头颜色固定
TEXT_COLOR = 'white'         # 节点文字颜色固定
BOX_COLOR = ['#5470C6', '#91CC75', '#EE6666']  # 固定配色（和之前风格统一）
SAVE_PATH = r"C:\Users\22073\Desktop\UserDataAnalysis\竖版双路径流程图.png"

# ==================== SQL取数（严格复刻你验证过的逻辑，只返回数据不影响绘图）====================
db_path = r"C:\Users\22073\Desktop\UserDataAnalysis\UserBehavior_Clean.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_behavior'")
if not cur.fetchone():
    raise ValueError("user_behavior表不存在")

# 1. PV独立用户数（两个路径共用基准）
cur.execute("SELECT COUNT(DISTINCT user_id) FROM user_behavior WHERE behavior_type='pv'")
pv_uv = cur.fetchone()[0]

# 2. 加购路径数据
cur.execute("""
    SELECT COUNT(DISTINCT t1.user_id) 
    FROM (SELECT DISTINCT user_id, item_id, category_id, datetime FROM user_behavior WHERE behavior_type='cart') t1
""")
cart_uv = cur.fetchone()[0]

cur.execute("""
    SELECT COUNT(DISTINCT t2.user_id) 
    FROM (SELECT DISTINCT user_id, item_id, category_id, datetime FROM user_behavior WHERE behavior_type='cart') t1
    LEFT JOIN (SELECT DISTINCT user_id, item_id, category_id, datetime FROM user_behavior WHERE behavior_type='buy') t2
    ON t1.user_id = t2.user_id AND t1.item_id = t2.item_id AND t1.category_id = t2.category_id
    WHERE t1.datetime < t2.datetime
""")
cart_buy_uv = cur.fetchone()[0]

# 3. 收藏路径数据
cur.execute("""
    SELECT COUNT(DISTINCT t1.user_id) 
    FROM (SELECT DISTINCT user_id, item_id, category_id, datetime FROM user_behavior WHERE behavior_type='fav') t1
""")
fav_uv = cur.fetchone()[0]

cur.execute("""
    SELECT COUNT(DISTINCT t2.user_id) 
    FROM (SELECT DISTINCT user_id, item_id, category_id, datetime FROM user_behavior WHERE behavior_type='fav') t1
    LEFT JOIN (SELECT DISTINCT user_id, item_id, category_id, datetime FROM user_behavior WHERE behavior_type='buy') t2
    ON t1.user_id = t2.user_id AND t1.item_id = t2.item_id AND t1.category_id = t2.category_id
    WHERE t1.datetime < t2.datetime
""")
fav_buy_uv = cur.fetchone()[0]

conn.close()

# 转化率计算（仅内容，不影响绘图尺寸）
cart_step1 = cart_uv / pv_uv if pv_uv else 0
cart_step2 = cart_buy_uv / cart_uv if cart_uv else 0
cart_final = cart_buy_uv / pv_uv if pv_uv else 0

fav_step1 = fav_uv / pv_uv if pv_uv else 0
fav_step2 = fav_buy_uv / fav_uv if fav_uv else 0
fav_final = fav_buy_uv / pv_uv if pv_uv else 0

# ==================== 竖版流程图绘制函数（所有尺寸固定，仅内容动态）====================
def draw_vertical_flowchart(ax, stages, values, conv_rates, title):
    """
    所有绘图参数100%固定，仅接收内容参数，保证左右两个图长得完全一样
    """
    # 固定起始Y坐标（让整个流程图垂直居中）
    start_y = 4
    
    # 1. 绘制3个垂直排列的节点
    for i in range(3):
        x = -NODE_WIDTH/2  # 节点水平居中（固定位置）
        y = start_y - i * (NODE_HEIGHT + VERTICAL_GAP)  # 垂直向下排列
        
        # 绘制固定尺寸的矩形节点
        rect = mpatches.FancyBboxPatch(
            (x, y), NODE_WIDTH, NODE_HEIGHT,
            boxstyle="round,pad=0.05",
            facecolor=BOX_COLOR[i],
            edgecolor='black',
            linewidth=1.2
        )
        ax.add_patch(rect)
        
        # 节点内文字（仅内容动态，位置/字号固定）
        ax.text(0, y + NODE_HEIGHT/2, 
                f"{stages[i]}\n{values[i]:,}",
                ha='center', va='center', color=TEXT_COLOR, 
                fontweight='bold', fontsize=11)
        
        # 2. 绘制向下的箭头（最后一个节点不需要箭头）
        if i < 2:
            arrow_start_y = y  # 当前节点底部
            arrow_end_y = y - VERTICAL_GAP  # 下一个节点顶部
            ax.annotate('', 
                        xy=(0, arrow_end_y),
                        xytext=(0, arrow_start_y),
                        arrowprops=dict(arrowstyle="->", color=ARROW_COLOR, lw=1.5, mutation_scale=20))
            
            # 箭头旁标注步骤转化率（仅内容动态，位置固定）
            ax.text(NODE_WIDTH/2 + 0.1, (arrow_start_y + arrow_end_y)/2,
                    f"{conv_rates[i]:.2%}",
                    ha='left', va='center', color='red',
                    fontweight='bold', fontsize=10)
    
    # 3. 底部标注最终转化率（位置/样式固定，仅内容动态）
    final_y = start_y - 3 * (NODE_HEIGHT + VERTICAL_GAP) + NODE_HEIGHT/2
    ax.text(0, final_y - 0.5,
            f"最终转化率：{conv_rates[2]:.2%}",
            ha='center', color='red', fontweight='bold', fontsize=12,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.9))
    
    # 4. 固定坐标轴范围（完全写死，不受数据影响）
    ax.set_xlim(-2, 2)
    ax.set_ylim(-2, 6)
    ax.axis('off')
    ax.set_title(title, fontsize=14, pad=20)

# ==================== 生成左右完全一致的竖版流程图 ====================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=FIG_SIZE)

# 左：加购路径竖版流程图（内容1，尺寸和右侧完全一致）
draw_vertical_flowchart(
    ax1,
    stages=['PV用户', '加购用户', '加购后购买'],
    values=[pv_uv, cart_uv, cart_buy_uv],
    conv_rates=[cart_step1, cart_step2, cart_final],
    title='加购路径流程图'
)

# 右：收藏路径竖版流程图（内容2，尺寸和左侧完全一致）
draw_vertical_flowchart(
    ax2,
    stages=['PV用户', '收藏用户', '收藏后购买'],
    values=[pv_uv, fav_uv, fav_buy_uv],
    conv_rates=[fav_step1, fav_step2, fav_final],
    title='收藏路径流程图'
)

plt.tight_layout()
plt.savefig(SAVE_PATH, dpi=150, bbox_inches='tight')
plt.show()

# 核心数据输出（仅内容，不影响绘图）
print(f"PV独立用户数：{pv_uv:,}")
print(f"加购路径：{cart_uv:,} → {cart_buy_uv:,} | 步骤转化率：{cart_step1:.2%}→{cart_step2:.2%} | 最终转化率：{cart_final:.2%}")
print(f"收藏路径：{fav_uv:,} → {fav_buy_uv:,} | 步骤转化率：{fav_step1:.2%}→{fav_step2:.2%} | 最终转化率：{fav_final:.2%}")
print(f"竖版流程图已保存至：{SAVE_PATH}")