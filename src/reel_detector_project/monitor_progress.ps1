# Monitor PCAP conversion progress every 30 minutes
# Run this script to check progress: .\monitor_progress.ps1

Write-Host "=== PCAP CONVERSION PROGRESS MONITOR ===" -ForegroundColor Magenta
Write-Host "Monitoring every 30 minutes..." -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop monitoring" -ForegroundColor Red
Write-Host ""

$startTime = Get-Date
$baselineLines = (Get-Content data/thursday_traffic.csv).Count
$baselineSize = (Get-ChildItem data/thursday_traffic.csv).Length

Write-Host "=== BASELINE STATUS ===" -ForegroundColor Green
Write-Host "Start time: $startTime" -ForegroundColor White
Write-Host "Baseline lines: $baselineLines" -ForegroundColor White
Write-Host "Baseline size: $([math]::Round($baselineSize/1KB, 2)) KB" -ForegroundColor White
Write-Host ""

$checkCount = 0

while ($true) {
    $checkCount++
    $currentTime = Get-Date
    $currentLines = (Get-Content data/thursday_traffic.csv).Count
    $currentSize = (Get-ChildItem data/thursday_traffic.csv).Length
    
    $linesAdded = $currentLines - $baselineLines
    $sizeAdded = $currentSize - $baselineSize
    $timeElapsed = $currentTime - $startTime
    
    Write-Host "=== CHECK #$checkCount - $currentTime ===" -ForegroundColor Cyan
    Write-Host "Current lines: $currentLines" -ForegroundColor White
    Write-Host "Current size: $([math]::Round($currentSize/1KB, 2)) KB" -ForegroundColor White
    Write-Host "Lines added: $linesAdded" -ForegroundColor Yellow
    Write-Host "Size added: $([math]::Round($sizeAdded/1KB, 2)) KB" -ForegroundColor Yellow
    Write-Host "Time elapsed: $($timeElapsed.Hours)h $($timeElapsed.Minutes)m $($timeElapsed.Seconds)s" -ForegroundColor Green
    
    if ($linesAdded -gt 0) {
        $rate = $linesAdded / $timeElapsed.TotalSeconds
        $estimatedTotal = if ($rate -gt 0) { [math]::Round(1000000 / $rate / 3600, 1) } else { "Unknown" }
        Write-Host "Processing rate: $([math]::Round($rate, 1)) lines/second" -ForegroundColor Cyan
        Write-Host "Estimated completion: $estimatedTotal hours" -ForegroundColor Cyan
    }
    
    Write-Host ""
    Write-Host "Next check in 30 minutes..." -ForegroundColor Gray
    Write-Host "----------------------------------------" -ForegroundColor Gray
    
    Start-Sleep -Seconds 1800  # 30 minutes = 1800 seconds
}
