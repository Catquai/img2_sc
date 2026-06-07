param(
    [Parameter(Mandatory = $true)]
    [string]$Source,
    [Parameter(Mandatory = $true)]
    [string]$Output,
    [string]$FillColor = "#ffffff"
)

Add-Type -AssemblyName System.Drawing

function Convert-HexColor {
    param([string]$Value)
    if ($Value -notmatch '^#([0-9a-fA-F]{6})$') {
        throw "Use an opaque hex color like #ffffff."
    }
    return [System.Drawing.ColorTranslator]::FromHtml($Value)
}

$sourcePath = (Resolve-Path -LiteralPath $Source).Path
$sourceImage = [System.Drawing.Image]::FromFile($sourcePath)
$result = New-Object System.Drawing.Bitmap -ArgumentList @(
    $sourceImage.Width,
    $sourceImage.Height,
    [System.Drawing.Imaging.PixelFormat]::Format24bppRgb
)
$graphics = [System.Drawing.Graphics]::FromImage($result)

try {
    $graphics.Clear((Convert-HexColor -Value $FillColor))
    $graphics.DrawImage($sourceImage, 0, 0, $sourceImage.Width, $sourceImage.Height)
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

Write-Output "Filled transparent background and wrote opaque image: $Output"
