# Project Packaging Script
$ProjectRoot = Get-Location
$ProjectName = "Project_Package"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmm"
$ZipName = "$($ProjectName)_$($Timestamp).zip"
$ZipPath = Join-Path $ProjectRoot $ZipName

Write-Host "Starting project packaging..." -ForegroundColor Cyan

$ExcludePatterns = @(
    "backend\venv*",
    "backend\__pycache__*",
    "backend\logs*",
    "backend\uploads*",
    "frontend\node_modules*",
    "frontend\dist*",
    "deployment\data*",
    "temp_landppt*",
    ".agent*",
    "*.zip",
    "*.log"
)

$StagingDir = Join-Path $env:TEMP "pm_package_staging"
if (Test-Path $StagingDir) { Remove-Item -Recursive -Force $StagingDir }
New-Item -ItemType Directory -Path $StagingDir | Out-Null

$DirsToCopy = @("backend", "frontend", "deployment", "docs")

foreach ($dir in $DirsToCopy) {
    if (Test-Path $dir) {
        $SourcePath = Join-Path $ProjectRoot.Path $dir
        Write-Host "Processing $dir..." -ForegroundColor Gray
        
        Get-ChildItem -Path $SourcePath -Recurse | ForEach-Object {
            $RelativePath = $_.FullName.Substring($ProjectRoot.Path.Length + 1)
            $ShouldExclude = $false
            foreach ($pattern in $ExcludePatterns) {
                if ($RelativePath -like $pattern) { $ShouldExclude = $true; break }
            }
            
            if (-not $ShouldExclude) {
                $TargetFile = Join-Path $StagingDir $RelativePath
                $TargetDir = Split-Path $TargetFile
                if (-not (Test-Path $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir | Out-Null }
                if (-not $_.PSIsContainer) {
                    Copy-Item $_.FullName $TargetFile -ErrorAction SilentlyContinue
                }
            }
        }
    }
}

$FilesToCopy = @(".env.example", "README.md")
foreach ($file in $FilesToCopy) {
    if (Test-Path $file) {
        Copy-Item $file $StagingDir
    }
}

Write-Host "Compressing..." -ForegroundColor Cyan
if (Test-Path $ZipPath) { Remove-Item $ZipPath }
Compress-Archive -Path "$StagingDir\*" -DestinationPath $ZipPath

Remove-Item -Recursive -Force $StagingDir

Write-Host "========================================" -ForegroundColor Green
Write-Host "Project successfully packaged!" -ForegroundColor Green
Write-Host "File Name: $ZipName"
Write-Host "Path: $ZipPath"
Write-Host "========================================" -ForegroundColor Green
