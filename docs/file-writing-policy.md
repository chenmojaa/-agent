# 文件写入规范（防 BOM / 防乱码）

## 根因
Windows PowerShell + .NET 默认 `WriteAllText` 会写 UTF-8 BOM（`EF BB BF`）：
- Python 解释器 → `SyntaxError: invalid non-printable character U+FEFF`
- Vue / Vite SFC parser → 模板首位错位、报 `Element is missing end tag`
- TypeScript 编译器 → 严格模式下也会抱怨

## 规则
1. **绝不允许** UTF-8 BOM 出现在 `.py` / `.vue` / `.ts` / `.css` / `.html` / `.md` / `.json` 文件首字节
2. 写文件统一用 `[System.Text.UTF8Encoding]::new($false)`（即 `UTF8Encoding(false)`）
3. 写之前检测源文本首字符 `\uFEFF`，出现就 `TrimStart([char]0xFEFF)`
4. 读文件时统一用 `[System.IO.File]::ReadAllBytes(path)` 然后显式判 BOM / 选解码

## 推荐写文件命令（PowerShell）
```powershell
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($path, $content, $utf8NoBom)
```

## 推荐读文件命令（PowerShell）
```powershell
$bytes = [System.IO.File]::ReadAllBytes($path)
if ($bytes.Length -gt 2 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
  $body = $bytes[3..($bytes.Length-1)]
} else { $body = $bytes }
$text = [System.Text.Encoding]::UTF8.GetString($body)
```

## 体检脚本
```powershell
$files = Get-ChildItem <dir> -Recurse -File -Include <ext> | Select-Object -ExpandProperty FullName
foreach ($f in $files) {
  $bytes = [System.IO.File]::ReadAllBytes($f)
  $bom = $bytes.Length -gt 2 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF
  $text = [System.Text.Encoding]::UTF8.GetString($bytes)
  $pua = 0
  foreach ($c in $text.ToCharArray()) {
    if ([int]$c -ge 0xE000 -and [int]$c -le 0xF8FF) { $pua++ }
  }
  if ($bom -or $pua -gt 0) {
    Write-Host "$f BOM=$bom PUA=$pua"
  }
}
```

## 误区
- **PowerShell `Get-Content` 显示乱码 ≠ 文件乱码**。控制台默认 GBK 解码 UTF-8 文件导致视觉乱码。判定真实状态用上面的体检脚本（按字节判断）。
- **VSCode 右下角显示编码**：UTF-8 with BOM 标记说明文件确实有 BOM，需要按规则 1 处理。