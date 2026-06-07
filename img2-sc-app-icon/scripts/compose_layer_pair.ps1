param(
    [Parameter(Mandatory = $true)]
    [string]$Foreground,
    [Parameter(Mandatory = $true)]
    [string]$Background,
    [Parameter(Mandatory = $true)]
    [string]$Output
)

Add-Type -AssemblyName System.Drawing

$foregroundPath = (Resolve-Path -LiteralPath $Foreground).Path
$backgroundPath = (Resolve-Path -LiteralPath $Background).Path
$foregroundImage = [System.Drawing.Bitmap]::FromFile($foregroundPath)
$backgroundImage = [System.Drawing.Bitmap]::FromFile($backgroundPath)

try {
    if ($foregroundImage.Width -ne $backgroundImage.Width -or $foregroundImage.Height -ne $backgroundImage.Height) {
        throw "Foreground and background dimensions must match exactly."
    }

    $foregroundHasTransparency = $false
    $backgroundHasTransparency = $false

    for ($y = 0; $y -lt $foregroundImage.Height; $y++) {
        for ($x = 0; $x -lt $foregroundImage.Width; $x++) {
            if ($foregroundImage.GetPixel($x, $y).A -lt 255) {
                $foregroundHasTransparency = $true
            }
            if ($backgroundImage.GetPixel($x, $y).A -lt 255) {
                $backgroundHasTransparency = $true
            }
        }
    }

    if (-not $foregroundHasTransparency) {
        throw "Foreground must contain transparent pixels."
    }
    if ($backgroundHasTransparency) {
        throw "Background must be fully opaque."
    }

    $result = New-Object System.Drawing.Bitmap -ArgumentList @(
        $backgroundImage.Width,
        $backgroundImage.Height,
        [System.Drawing.Imaging.PixelFormat]::Format32bppArgb
    )
    $graphics = [System.Drawing.Graphics]::FromImage($result)

    try {
        $graphics.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceOver
        $graphics.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
        $graphics.DrawImage($backgroundImage, 0, 0, $backgroundImage.Width, $backgroundImage.Height)
        $graphics.DrawImage($foregroundImage, 0, 0, $foregroundImage.Width, $foregroundImage.Height)

        $outputDir = Split-Path -Parent $Output
        if ($outputDir) {
            New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
        }
        $result.Save($Output, [System.Drawing.Imaging.ImageFormat]::Png)
    }
    finally {
        if ($graphics) {
            $graphics.Dispose()
        }
        if ($result) {
            $result.Dispose()
        }
    }
}
finally {
    if ($foregroundImage) {
        $foregroundImage.Dispose()
    }
    if ($backgroundImage) {
        $backgroundImage.Dispose()
    }
}

Write-Output "Validated layer pair and wrote composite preview: $Output"
