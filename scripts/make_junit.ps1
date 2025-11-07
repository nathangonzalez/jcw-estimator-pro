param(
  [string]$Suite = "suite",
  [string]$Case = "case",
  [bool]$Success = $true,
  [string]$Out = "output/JUNIT.xml"
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path (Split-Path $Out) | Out-Null

$failNode = if ($Success) { "" } else { "<failure message=`"failed`"></failure>" }

$xml = @"
<testsuite name="$Suite" tests="1" failures="${([int](-not $Success))}">
  <testcase classname="$Suite" name="$Case">
    $failNode
  </testcase>
</testsuite>
"@

$xml | Out-File -Encoding utf8 $Out
