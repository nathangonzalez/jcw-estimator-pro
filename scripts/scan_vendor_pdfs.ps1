$ErrorActionPreference = 'Stop'

$root = 'data/lynn/raw/vendor'
$outDir = 'output'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$out = Join-Path $outDir 'F4B_PDF_LIST.txt'

if (Test-Path $root) {
  $pdfs = Get-ChildItem -Path $root -Recurse -Include *.pdf -File -ErrorAction SilentlyContinue
  $count = if ($pdfs) { $pdfs.Count } else { 0 }
  if ($count -gt 0) {
    $pdfs | Select-Object FullName, Length, LastWriteTime |
      Format-Table -AutoSize | Out-String -Width 4096 |
      Set-Content -Path $out -Encoding UTF8
  } else {
    "No PDFs found under $root (expected *.pdf files)." | Set-Content -Path $out -Encoding UTF8
  }
  Write-Host ("FOUND_PDFS {0}" -f $count)
  Write-Host ("WROTE {0}" -f $out)
} else {
  ("Missing path: " + $root) | Set-Content -Path $out -Encoding UTF8
  Write-Host ("MISSING_ROOT {0}" -f $root)
  Write-Host ("WROTE {0}" -f $out)
}
