# 完整分卷索引

JSON只移除格式空白，所有值均保留；按序拼接分卷与完整文件原字节完全一致。必须完整读取所有分卷，不得以索引或末标冒充完整读取。

```json
{
  "full_file": "context-r00b.md",
  "bytes": 315643,
  "sha256": "e436c71211d70252d24c6b5b3b1a458e959e3b26284e61b1bbeb7c9cd2cca479",
  "parts": [
    {
      "file": "context-r00b-part01.md",
      "bytes": 104985,
      "sha256": "52bfeee890b91c58ed4b0fe6ce8868777247473f844a1256cae3249ad19157d6"
    },
    {
      "file": "context-r00b-part02.md",
      "bytes": 2487,
      "sha256": "2a4108d145659077a932b93e33afec3a706c630e9a3d62a3520ff72658a8bca5"
    },
    {
      "file": "context-r00b-part03.md",
      "bytes": 123573,
      "sha256": "db8fe89605a96dd1981f1b5efb57bb7a5805ebcf0f227357d08b05aeca757e09"
    },
    {
      "file": "context-r00b-part04.md",
      "bytes": 84598,
      "sha256": "1726fbce94983594b508d762bb7f84c6c296ab4536b9d2afff66e913604bd5e4"
    }
  ],
  "parts_concat_exact": true
}
```
