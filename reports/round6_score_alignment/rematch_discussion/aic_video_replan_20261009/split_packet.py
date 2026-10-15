"""Split a complete immutable packet into line-aligned full UTF-8 volumes."""
from pathlib import Path
import argparse
import hashlib
import json

HERE = Path(__file__).resolve().parent

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('packet')
    parser.add_argument('--max-bytes', type=int, default=140000)
    args = parser.parse_args()
    source = HERE / args.packet
    original = source.read_bytes()
    chunks, chunk = [], bytearray()
    for line in original.splitlines(keepends=True):
        if chunk and len(chunk) + len(line) > args.max_bytes:
            chunks.append(bytes(chunk))
            chunk.clear()
        chunk.extend(line)
    if chunk:
        chunks.append(bytes(chunk))
    assert b''.join(chunks) == original
    rows, offset, start_line = [], 0, 1
    for index, data in enumerate(chunks, 1):
        data.decode('utf-8')
        filename = source.stem + f'-part{index:02}.md'
        path = HERE / filename
        if path.exists():
            raise FileExistsError(path)
        path.write_bytes(data)
        count = len(data.splitlines())
        rows.append(dict(file=filename, bytes=len(data), sha256=sha(data),
                         byte_start=offset, byte_end_exclusive=offset+len(data),
                         first_line=start_line, last_line=start_line+count-1))
        offset += len(data)
        start_line += count
    index_file = HERE / (source.stem + '-index.md')
    if index_file.exists():
        raise FileExistsError(index_file)
    info = dict(packet=source.name, bytes=len(original), sha256=sha(original),
                parts=rows, exact_concatenation=True, no_content_omitted=True)
    index_file.write_text('# 完整连续分卷索引\n\n任务 AIC-VIDEO-REMATCH-NEXT-20261005。'
        '必须按序完整读取以下所有分卷，不能只读最后一卷。分卷原字节顺序拼接即完整原包，'
        '无删减、无摘要替代；代码围栏可能跨卷，请按连续文本读取。继承旧轮次的阶段/额度只为历史，'
        '当前事实和主控新问题位于最后卷。请明确每卷实际读取范围与截断，缺卷不得宣称全读。\n\n'
        '```json\n' + json.dumps(info, ensure_ascii=False, indent=2) + '\n```\n', encoding='utf-8')
    print(json.dumps(info, ensure_ascii=False))

if __name__ == '__main__':
    main()
