import pandas as pd
import sqlite3
import os

csv_file = r"C:\Users\22073\Desktop\UserDataAnalysis\UserBehavior_Clean.csv"
db_file = r"C:\Users\22073\Desktop\UserDataAnalysis\UserBehavior_Clean.db"

conn = sqlite3.connect(db_file)

# 分块读
chunk_iter = pd.read_csv(
    csv_file,
    header=None,
    names=["user_id","item_id","category_id","behavior_type","datetime"],
    chunksize=100000
)

first = True
for chunk in chunk_iter:
    # 直接存时间字符串
    chunk["datetime"] = chunk["datetime"].astype(str)
    chunk.to_sql("user_behavior", conn, if_exists="replace" if first else "append", index=False)
    first = False

conn.close()

conn = sqlite3.connect(db_file)
count = conn.execute("select count(*) from user_behavior").fetchone()[0]
print(f"入库完成")
conn.close()

os.remove(csv_file)