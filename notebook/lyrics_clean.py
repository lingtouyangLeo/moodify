# 如果你在 Colab 上，先确保有 pandas
# !pip install pandas

import pandas as pd
import re

# ============ 1. 配置区（按需修改） ============


import os
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

INPUT_CSV_PATH = os.path.join(PROJECT_ROOT, "data", "tracks_with_lyrics.csv")
OUTPUT_CSV_PATH = os.path.join(PROJECT_ROOT, "data", "tracks_with_lyrics_cleaned.csv")


# 是否把歌词统一转成小写（推荐：True，方便做情绪分类和向量化）
TO_LOWER = True

# 是否移除括号里的“舞台说明类文字”（但保留情绪喊话）
# 例如：(Chorus)、(Verse 2)、(Bridge)、(Background Vocals) 会被去掉
#      (yeah)、(oh no) 这类情绪喊话会尽量保留
REMOVE_STAGE_COMMENTS = True


# ============ 2. 一些模式和关键词 ============

# 非歌词/站内提示/制作信息等垃圾行（统一小写后匹配）
BAD_KEYWORDS = [
    "you might also like",
    "embed",
    "track info",
    "more on genius",
    "lyrics powered by",
    "produced by",
    "written by",
    "composed by",
    "recorded at",
    "mastered by",
    "engineered by",
]

# [Chorus] / [Verse 1] / [Bridge] 等段落标签
SECTION_HEADER_PATTERN = re.compile(r"^\s*\[.*?\]\s*$")

# 典型“舞台说明类”括号内容关键字
STAGE_COMMENT_KEYWORDS = [
    "chorus", "verse", "bridge", "hook", "intro", "outro",
    "pre-chorus", "post-chorus",
    "background", "vocals", "beat", "instrumental",
    "guitar", "solo", "spoken", "talking", "whisper",
    "laughs", "applause", "crowd",
]


def is_stage_comment(text: str) -> bool:
    """
    判断括号中的内容是不是舞台说明（而不是情绪喊话）
    例如：Chorus、Background Vocals -> True
         yeah, oh no -> False
    """
    t = text.strip().lower()
    # 太长的大段说明，一般也当舞台说明（比如：background talking…）
    if len(t.split()) > 6:
        return True
    return any(k in t for k in STAGE_COMMENT_KEYWORDS)


def clean_lyrics_one_song(text: str) -> str:
    """对单首歌的歌词做清洗，返回清洗后的字符串"""
    if pd.isna(text):
        return text

    # -------- 2.1 按行拆开，逐行处理 --------
    lines = text.splitlines()
    cleaned_lines = []

    for line in lines:
        original_line = line
        line = line.strip()

        # 空行直接跳过（后面再统一格式）
        if line == "":
            continue

        lower_line = line.lower()

        # ① 删除明显不是歌词的垃圾行（站内提示 / credits）
        if any(k in lower_line for k in BAD_KEYWORDS):
            continue

        # ② 删除 [Chorus] / [Verse 1] 这类结构标签
        if SECTION_HEADER_PATTERN.match(line):
            continue

        # ③ 可选：删除纯舞台说明类的括号行
        #    示例：(Chorus), (Bridge), (Background Vocals)
        if REMOVE_STAGE_COMMENTS and line.startswith("(") and line.endswith(")"):
            inner = line[1:-1]
            if is_stage_comment(inner):
                # 这是类似 (Chorus) 的内容，直接整行丢掉
                continue

        # ④ 行中间的括号内容：只删除“舞台说明”，保留情绪喊话
        #    例如：I said (yeah!) I love you -> 保留 (yeah!)
        #          (Background Vocals: la la la) -> 删除
        if REMOVE_STAGE_COMMENTS:
            def _handle_paren(m):
                inner = m.group(1)
                if is_stage_comment(inner):
                    # 删除舞台说明括号
                    return ""
                else:
                    # 保留情绪相关括号（例如 (yeah), (oh no)）
                    return m.group(0)

            line = re.sub(r"\((.*?)\)", _handle_paren, line).strip()
            if line == "":
                continue

        cleaned_lines.append(line)

    # 所有行都被删掉的话，就返回空字符串
    if not cleaned_lines:
        return ""

    # -------- 2.2 合并被拆开的标点行（简单版本） --------
    merged_lines = []
    i = 0
    while i < len(cleaned_lines):
        line = cleaned_lines[i]

        # 如果当前行只有一个标点（, . ! ? ; :），且前后都有内容，就与两侧合并
        if (
            len(line) == 1
            and line in {",", ".", "!", "?", ";", ":"}
            and i > 0
            and i < len(cleaned_lines) - 1
        ):
            prev_line = merged_lines.pop()
            next_line = cleaned_lines[i + 1]
            merged = prev_line.rstrip() + line + " " + next_line.lstrip()
            merged_lines.append(merged)
            i += 2  # 跳过下一行
        else:
            merged_lines.append(line)
            i += 1

    text = "\n".join(merged_lines)

    # -------- 2.3 统一符号、空白、大小写 --------
    # 统一各种引号
    text = (
        text.replace("’", "'")
            .replace("‘", "'")
            .replace("“", '"')
            .replace("”", '"')
    )

    # 去掉多余空格（不影响换行）
    text = re.sub(r"[ \t]+", " ", text)

    # 可选：全部转小写（方便做情绪分类 & 推荐 embedding）
    if TO_LOWER:
        text = text.lower()

    return text.strip()


# ============ 3. 读取 CSV，批量清洗并保存 ============

print(f"读取 CSV: {INPUT_CSV_PATH}")
df = pd.read_csv(INPUT_CSV_PATH)

if "lyrics" not in df.columns:
    raise ValueError("当前 CSV 中没有 'lyrics' 这一列，请检查文件列名。")

# 生成新列：clean_lyrics
df["clean_lyrics"] = df["lyrics"].apply(clean_lyrics_one_song)

# 你也可以只保留需要的列，方便后续处理：
df = df[["track_name", "artist_name", "play_count", "clean_lyrics"]]

df.to_csv(OUTPUT_CSV_PATH, index=False)
print(f"已保存清洗后的 CSV 到: {OUTPUT_CSV_PATH}")
print(df[["track_name", "artist_name", "clean_lyrics"]].head())
