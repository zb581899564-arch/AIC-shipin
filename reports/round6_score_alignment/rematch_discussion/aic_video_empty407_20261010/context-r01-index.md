# 完整分卷索引

JSON只移除格式空白，所有值均保留；按序拼接分卷与完整文件原字节完全一致。必须完整读取所有分卷，不得以索引或末标冒充完整读取。

```json
{
  "full_file": "context-r01.md",
  "bytes": 535643,
  "sha256": "4096ebc8f6dc91de3b60a9b1ceefb3496cc9fe4e1161531f795b75e13f57296a",
  "parts": [
    {
      "file": "context-r01-part01.md",
      "bytes": 104979,
      "sha256": "266818dcdea617fd23369fb96eac44d81c6f2ba64352710dbf13d0e073333a42"
    },
    {
      "file": "context-r01-part02.md",
      "bytes": 9727,
      "sha256": "d77f9ed9750e4a9404d2b1a5b579c31487e795efb9e341bfadaefec9a1fe67cf"
    },
    {
      "file": "context-r01-part03.md",
      "bytes": 123573,
      "sha256": "db8fe89605a96dd1981f1b5efb57bb7a5805ebcf0f227357d08b05aeca757e09"
    },
    {
      "file": "context-r01-part04.md",
      "bytes": 104833,
      "sha256": "c04dae1fd244964149ce673fd6fbc530d6723d131d560c4fc130ac711eaac63f"
    },
    {
      "file": "context-r01-part05.md",
      "bytes": 104892,
      "sha256": "e2099860e828c64ce8c4d798a5fc1895c0c27de5708dd661e34f4016b0ae0bd0"
    },
    {
      "file": "context-r01-part06.md",
      "bytes": 86048,
      "sha256": "7685f2cc5d70a8ea25bbf151b6804dce9646273df12f9c4e9aa95a722af12612"
    }
  ],
  "parts_concat_exact": true
}
```
