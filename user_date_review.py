import pandas as pd

FILE = r"C:\Users\22073\Desktop\UserDataAnalysis\UserBehavior.csv"

df = pd.read_csv(
    FILE,
    header=None,
    names=["user_id", "item_id", "category_id", "behavior_type", "timestamp"]
)

print("原始数据量:", len(df))

# 时间戳转时间
df["datetime"] = pd.to_datetime(df["timestamp"], unit="s", errors="coerce")

# .随机抽样1000行做抽查
sample_df = df.sample(n=1000, random_state=42)  

print("===== 抽查1000行数据预览 =====")
print(sample_df[["user_id", "item_id", "behavior_type", "timestamp", "datetime"]].head(10))

print("\n时间范围：")
print(df["datetime"].min(), "~", df["datetime"].max())

print("\n行为类型分布：")
print(df["behavior_type"].value_counts(dropna=False))

print("\n缺失值统计：")
print(df.isnull().sum())