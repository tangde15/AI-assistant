#!/usr/bin/env python3
"""
脚本：向 Milvus 知识库插入示例历史/文化常识条目，用于测试检索功能。

用法：在项目根目录激活 venv 后运行：
    & "E:/python project/Custom-built AI assistant/venv/Scripts/python.exe" scripts/insert_knowledge_samples.py

注意：确保 Milvus 已启动且后端依赖（embedding_model 等）已正确配置。
"""
import time
import os
import sys

# Ensure project root is on sys.path so imports like `knowledgebase` work
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from knowledgebase import create_knowledgebase, insert_knowledge


SAMPLES = [
    {
        "content": "长城是中国古代为防御北方民族入侵而修建的防御工程，始建于春秋战国，秦始皇统一后大规模连接与修缮，绵延数千公里，是世界文化遗产。",
        "source": "维基百科"
    },
    {
        "content": "秦始皇于公元前221年完成中国第一次大一统，统一了度量衡、文字和货币，并开始修筑万里长城和阿房宫。",
        "source": "中国历史教材"
    },
    {
        "content": "丝绸之路是古代横贯欧亚的贸易通道，不仅运输丝绸和香料，还促进了东西方文明、宗教和技术的交流。",
        "source": "历史文献"
    },
    {
        "content": "唐代（618–907）是中国古代诗歌的黄金时代，涌现出李白、杜甫等著名诗人，他们的诗作对后世影响深远。",
        "source": "文学史资料"
    },
    {
        "content": "春节，又称农历新年，是中国和其他东亚地区的重要传统节日，人们在此期间团聚、祭祖、放鞭炮、贴春联以辞旧迎新。",
        "source": "民俗学"
    },
    {
        "content": "日本茶道是一种以茶会为中心的传统文化实践，强调礼仪、审美与待客之道，形式与器具体现了侘寂美学。",
        "source": "日本文化研究"
    },
    {
        "content": "印度的排灯节（Diwali）是象征胜利与光明的节日，人们点灯、放烟花、互赠礼物，祈愿繁荣与幸福。",
        "source": "印度节庆资料"
    },
    {
        "content": "埃及金字塔是古埃及文明的标志性建筑，主要用于法老的陵墓，其中最著名的是吉萨的胡夫金字塔。",
        "source": "考古学"
    },
    {
        "content": "法国的巴士底日（7月14日）纪念1789年巴士底狱被攻占，常被视为法国大革命的象征，今日为法国的国庆日。",
        "source": "世界史资料"
    },
    {
        "content": "俄罗斯套娃（Matryoshka）是一种套叠式木制民俗工艺品，源于19世纪末，象征家庭与子孙繁衍。",
        "source": "民俗文化"
    }
]


def main():
    print("确保 Milvus 已启动并且后端依赖配置正确（embedding_model 等）...")
    # 创建集合（如已存在会跳过）
    create_knowledgebase()

    inserted = []
    for idx, item in enumerate(SAMPLES, start=1):
        try:
            print(f"插入样本 {idx}: {item['content'][:60]}...")
            id_ = insert_knowledge(item)
            inserted.append((id_, item))
            # 稍作间隔，避免并发导致的问题
            time.sleep(0.2)
        except Exception as e:
            print(f"插入失败 ({idx}): {e}")

    print(f"完成，成功插入 {len(inserted)} 条样本。")
    for id_, item in inserted:
        print(f"  id={id_}  source={item['source']}  preview={item['content'][:50]}")


if __name__ == '__main__':
    main()
