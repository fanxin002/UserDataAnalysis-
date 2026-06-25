import pandas as pd

FILE = r"C:\Users\22073\Desktop\UserDataAnalysis\UserBehavior.csv"

start = pd.Timestamp("2017-11-25")
end   = pd.Timestamp("2017-12-03 23:59:59")

# 全局计数：总行数 / 脏数据行数
total = dirty = 0
chunks = []

for i, c in enumerate(pd.read_csv(
    FILE,
    header=None,
    names=["user_id","item_id","category_id","behavior_type","timestamp"],
    chunksize=500_000
)):
    total += len(c)

    c["datetime"] = pd.to_datetime(c["timestamp"], unit="s", errors="coerce")

    mask = c["datetime"].between(start, end)

    # 不在时间窗口内的全部算脏数据
    dirty += (~mask).sum()
    chunks.append(c[mask])

df = pd.concat(chunks, ignore_index=True)
df = df.drop(columns=["timestamp"])

print(f"\n总行数: {total:,}，脏数据: {dirty:,}，占比 {dirty/total:.2%}")
print(f"有效数据: {len(df):,}")
print(f"时间范围: {df['datetime'].min()} ~ {df['datetime'].max()}")
print("行为分布:")
print(df["behavior_type"].value_counts())

df.to_csv("UserBehavior_Clean.csv", index=False, header=False)
print("清洗完成")