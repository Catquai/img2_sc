param(
    [Parameter(Mandatory = $true)]
    [string]$Source,
    [Parameter(Mandatory = $true)]
    [string]$Output,
    [int]$Width = 512,
    [int]$Height = 512,
    [ValidateSet("cover", "contain", "stretch")]
    [string]$Fit = "cover",
    [string]$Background = "#00000000"
)

Add-Type -AssemblyName System.Drawing

function Convert-HexColor {
    param([string]$Value)
    if ($Value -notmatch '^#([0-9a-fA-F]{6}|[0-9a-fA-F]{8})$') {
        throw "Use a hex color like #ffffff or #00000000."
    }
    $hex = $Value.Substring(1)
    $r = [Convert]::ToInt32($hex.Substring(0, 2), 16)
    $g = [Convert]::ToInt32($hex.Substring(2, 2), 16)
    $b = [Convert]::ToInt32($hex.Substring(4, 2), 16)
    $a = if ($hex.Length -eq 8) { [Convert]::ToInt32($hex.Substring(6, 2), 16) } else { 255 }
    return [System.Drawing.Color]::FromArgb($a, $r, $g, $b)
}

$sourcePath = (Resolve-Path -LiteralPath $Source).Path
$sourceImage = [System.Drawing.Image]::FromFile($sourcePath)
$result = New-Object System.Drawing.Bitmap -ArgumentList @(
    $Width,
    $Height,
    [System.Drawing.Imaging.PixelFormat]::Format32bppArgb
)
$graphics = [System.Drawing.Graphics]::FromImage($result)

try {
    $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
    $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $graphics.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
    $graphics.Clear((Convert-HexColor -Value $Background))

    if ($Fit -eq "stretch") {
        $destination = New-Object System.Drawing.Rectangle 0, 0, $Width, $Height
    }
    else {
        $scaleX = $Width / $sourceImage.Width
        $scaleY = $Height / $sourceImage.Height
        $scale = if ($Fit -eq "cover") { [Math]::Max($scaleX, $scaleY) } else { [Math]::Min($scaleX, $scaleY) }
        $drawWidth = [Math]::Round($sourceImage.Width * $scale)
        $drawHeight = [Math]::Round($sourceImage.Height * $scale)
        $x = [Math]::Round(($Width - $drawWidth) / 2)
        $y = [Math]::Round(($Height - $drawHeight) / 2)
        $destination = New-Object System.Drawing.Rectangle $x, $y, $drawWidth, $drawHeight
    }

    $graphics.DrawImage($sourceImage, $destination)
    $outputDir = Split-Path -Parent $Output
    if ($outputDir) {
        New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
    }
    $result.Save($Output, [System.Drawing.Imaging.ImageFormat]::Png)
}
finally {
    $graphics.Dispose()
    $result.Dispose()
    $sourceImage.Dispose()
}

Write-Output "Resized image to $($Width)x$($Height): $Output"
