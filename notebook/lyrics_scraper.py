import os
import json
import time
import random
import pandas as pd
import lyricsgenius
from tqdm import tqdm

# ========== 0. 基本配置 ==========
client_access_token = "3AhYPPIL5RQbybxGO0UvFk2OH_ZHkiN6w07CVwy9WNrLzxN0qhBDW2rIRkV8041e"  # ⚠️ 换成你自己的 token

genius = lyricsgenius.Genius(
    client_access_token,
    timeout=15,
    skip_non_songs=True,
    remove_section_headers=True,
)

input_json_path = "part-00000-c13c6767-e1f0-4adf-bab8-6e210485f360-c000.json"
output_csv_path = "csv/tracks_with_lyrics.csv"

# 每多少首歌保存一次中间结果
CHECKPOINT_EVERY = 100

# 如果你想测试用，先限制数量；想全部跑就设为 None
MAX_SONGS = None  # 比如只跑 500 首就写 500

# ========== 1. 读取 JSON（每行一首歌） ==========
tracks = []
with open(input_json_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        data = json.loads(line)
        tracks.append(data)

print(f"从 JSON 读取到 {len(tracks)} 首歌")

# ========== 2. 载入已有 CSV，做断点续爬 + 避免重复失败 ==========
results = []  # 用来保存“本轮 + 历史”的所有结果记录
processed_keys = set()        # 所有已经处理过的 (track_name, artist_name)
processed_success = set()     # 成功拿到歌词的 key
processed_error = set()       # 有 error 的 key

if os.path.exists(output_csv_path):
    print(f"检测到已有文件：{output_csv_path}，尝试断点续爬...")
    df_existing = pd.read_csv(output_csv_path)

    # 把已有的记录都放进 results 里，后面会继续往里 append
    results = df_existing.to_dict(orient="records")

    for _, row in df_existing.iterrows():
        track_name_old = str(row.get("track_name", ""))
        artist_name_old = str(row.get("artist_name", ""))
        key = (track_name_old, artist_name_old)

        processed_keys.add(key)

        lyrics_old = row.get("lyrics")
        error_old = row.get("error")

        # 有歌词算成功
        if isinstance(lyrics_old, str) and lyrics_old.strip() != "":
            processed_success.add(key)
        # 没歌词但有 error，算失败过
        elif isinstance(error_old, str) and error_old.strip() != "":
            processed_error.add(key)

    print(f"已存在记录数：{len(results)}")
    print(f"其中成功：{len(processed_success)}，失败：{len(processed_error)}")
else:
    print("未检测到已有 CSV，将从头开始爬取。")

# 当前已有的结果数量（用于计算 checkpoint）
current_count = len(results)

# ========== 3. 主循环：抓歌词 + 自动跳过 + 中间保存 ==========
new_fetched = 0  # 统计本次新抓取的数量

for i, item in enumerate(tqdm(tracks, desc="Fetching lyrics")):
    # 如果设置了 MAX_SONGS，就在这里限制总处理量（包括已经有的）
    if MAX_SONGS is not None and (new_fetched + len(processed_keys)) >= MAX_SONGS:
        break

    track_name = item.get("track_name")
    artist_name = item.get("artist_name")
    play_count = item.get("play_count")

    key = (str(track_name), str(artist_name))

    # 1) 自动跳过已经爬过的歌曲（无论之前成功还是失败）
    if key in processed_keys:
        # 如果你想将“失败过”的歌重新尝试，可以在这里改逻辑
        continue

    lyrics = None
    error_msg = None

    try:
        song = genius.search_song(track_name, artist_name)
        if song is not None and isinstance(song.lyrics, str) and song.lyrics.strip() != "":
            lyrics = song.lyrics
        else:
            error_msg = "Song not found or empty lyrics"
    except Exception as e:
        error_msg = str(e)

    results.append({
        "track_name": track_name,
        "artist_name": artist_name,
        "play_count": play_count,
        "lyrics": lyrics,
        "error": error_msg,
    })

    # 更新状态集合
    processed_keys.add(key)
    if lyrics is not None and lyrics.strip() != "":
        processed_success.add(key)
    else:
        processed_error.add(key)

    new_fetched += 1
    current_count += 1

    # 2) 每 100 首自动保存中间文件
    if current_count % CHECKPOINT_EVERY == 0:
        df_checkpoint = pd.DataFrame(results)
        df_checkpoint.to_csv(output_csv_path, index=False)
        print(f"\nCheckpoint 已保存：共 {current_count} 条记录（包括历史 + 本次）")

    # 3) 随机 sleep 5~15 秒，防止被限流
    time.sleep(random.uniform(3, 6))

# ========== 4. 最后一轮保存 ==========
df_final = pd.DataFrame(results)
df_final.to_csv(output_csv_path, index=False)
print(f"\n全部完成！最终共保存 {len(results)} 条记录（包括历史 + 本次）。")
print(f"文件路径：{output_csv_path}")
