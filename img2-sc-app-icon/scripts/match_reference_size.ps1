param(
    [string]$Reference,
    [string]$Generated,
    [string]$Output,
    [ValidateSet("cover", "contain", "stretch")]
    [string]$Fit = "cover",
    [string]$Background = "#ffffff",
    [switch]$Info,
    [string[]]$Paths
)

Add-Type -AssemblyName System.Drawing

function Get-ImageSize {
    param([string]$Path)
    $resolved = Resolve-Path -LiteralPath $Path
    $image = [System.Drawing.Image]::FromFile($resolved)
    try {
        return [PSCustomObject]@{
            Path = $resolved.Path
            Width = $image.Width
            Height = $image.Height
        }
    }
    finally {
        $image.Dispose()
    }
}

function Convert-HexColor {
    param([string]$Value)
    if ($Value -notmatch '^#([0-9a-fA-F]{6}|[0-9a-fA-F]{8})$') {
        throw "Use a hex color like #ffffff or #ffffffff."
    }
    $hex = $Value.Substring(1)
    $r = [Convert]::ToInt32($hex.Substring(0, 2), 16)
    $g = [Convert]::ToInt32($hex.Substring(2, 2), 16)
    $b = [Convert]::ToInt32($hex.Substring(4, 2), 16)
    $a = 255
    if ($hex.Length -eq 8) {
        $a = [Convert]::ToInt32($hex.Substring(6, 2), 16)
    }
    return [System.Drawing.Color]::FromArgb($a, $r, $g, $b)
}

function Get-ImageFormat {
    param([string]$Path)
    $extension = [System.IO.Path]::GetExtension($Path).ToLowerInvariant()
    switch ($extension) {
        ".jpg" { return [System.Drawing.Imaging.ImageFormat]::Jpeg }
        ".jpeg" { return [System.Drawing.Imaging.ImageFormat]::Jpeg }
        ".bmp" { return [System.Drawing.Imaging.ImageFormat]::Bmp }
        ".gif" { return [System.Drawing.Imaging.ImageFormat]::Gif }
        default { return [System.Drawing.Imaging.ImageFormat]::Png }
    }
}

if ($Info) {
    if (-not $Paths -or $Paths.Count -eq 0) {
        throw "-Info requires at least one image path."
    }
    $infoPaths = foreach ($rawPath in $Paths) {
        $rawPath -split "," | Where-Object { $_.Trim().Length -gt 0 } | ForEach-Object { $_.Trim() }
    }
    foreach ($path in $infoPaths) {
        $size = Get-ImageSize -Path $path
        Write-Output "$($size.Path): $($size.Width)x$($size.Height)"
    }
    exit 0
}

if (-not $Reference -or -not $Generated -or -not $Output) {
    throw "Reference, Generated, and Output are required unless -Info is used."
}

$referenceSize = Get-ImageSize -Path $Reference
$generatedPath = (Resolve-Path -LiteralPath $Generated).Path
$source = [System.Drawing.Image]::FromFile($generatedPath)
$canvas = New-Object System.Drawing.Bitmap $referenceSize.Width, $referenceSize.Height
$graphics = [System.Drawing.Graphics]::FromImage($canvas)

try {
    $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
    $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $graphics.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
    $graphics.Clear((Convert-HexColor -Value $Background))

    if ($Fit -eq "stretch") {
        $dest = New-Object System.Drawing.Rectangle 0, 0, $referenceSize.Width, $referenceSize.Height
    }
    else {
        $scaleX = $referenceSize.Width / $source.Width
        $scaleY = $referenceSize.Height / $source.Height
        $scale = if ($Fit -eq "cover") { [Math]::Max($scaleX, $scaleY) } else { [Math]::Min($scaleX, $scaleY) }
        $width = [Math]::Round($source.Width * $scale)
        $height = [Math]::Round($source.Height * $scale)
        $x = [Math]::Round(($referenceSize.Width - $width) / 2)
        $y = [Math]::Round(($referenceSize.Height - $height) / 2)
        $dest = New-Object System.Drawing.Rectangle $x, $y, $width, $height
    }

    $graphics.DrawImage($source, $dest)
    $outputDir = Split-Path -Parent $Output
    if ($outputDir) {
        New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
    }
    $canvas.Save($Output, (Get-ImageFormat -Path $Output))
}
finally {
    $graphics.Dispose()
    $canvas.Dispose()
    $source.Dispose()
}

$finalSize = Get-ImageSize -Path $Output
Write-Output "Wrote $Output`: $($finalSize.Width)x$($finalSize.Height)"
