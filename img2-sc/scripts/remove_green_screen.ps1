param(
    [Parameter(Mandatory = $true)]
    [string]$Source,
    [Parameter(Mandatory = $true)]
    [string]$Output,
    [string]$KeyColor = "#00ff00",
    [int]$Tolerance = 70,
    [int]$Softness = 35,
    [int]$Despill = 25
)

Add-Type -AssemblyName System.Drawing

function Convert-HexColor {
    param([string]$Value)
    if ($Value -notmatch '^#([0-9a-fA-F]{6})$') {
        throw "Use a hex color like #00ff00."
    }
    $hex = $Value.Substring(1)
    return [System.Drawing.Color]::FromArgb(
        255,
        [Convert]::ToInt32($hex.Substring(0, 2), 16),
        [Convert]::ToInt32($hex.Substring(2, 2), 16),
        [Convert]::ToInt32($hex.Substring(4, 2), 16)
    )
}

$key = Convert-HexColor -Value $KeyColor
$resolved = Resolve-Path -LiteralPath $Source
$bitmap = [System.Drawing.Bitmap]::FromFile($resolved.Path)
$result = New-Object System.Drawing.Bitmap -ArgumentList @(
    $bitmap.Width,
    $bitmap.Height,
    [System.Drawing.Imaging.PixelFormat]::Format32bppArgb
)

try {
    $maxDistance = [Math]::Sqrt(3 * 255 * 255)
    for ($y = 0; $y -lt $bitmap.Height; $y++) {
        for ($x = 0; $x -lt $bitmap.Width; $x++) {
            $p = $bitmap.GetPixel($x, $y)
            $dr = $p.R - $key.R
            $dg = $p.G - $key.G
            $db = $p.B - $key.B
            $distance = [Math]::Sqrt($dr * $dr + $dg * $dg + $db * $db)

            if ($distance -le $Tolerance) {
                $alpha = 0
            }
            elseif ($distance -le ($Tolerance + $Softness)) {
                $alpha = [Math]::Round(255 * (($distance - $Tolerance) / [Math]::Max(1, $Softness)))
            }
            else {
                $alpha = $p.A
            }

            $r = $p.R
            $g = $p.G
            $b = $p.B
            if ($alpha -gt 0 -and $Despill -gt 0 -and $p.G -gt $p.R -and $p.G -gt $p.B) {
                $limit = [Math]::Min(255, [Math]::Max($p.R, $p.B) + $Despill)
                $g = [Math]::Min([int]$p.G, [int]$limit)
            }

            $result.SetPixel($x, $y, [System.Drawing.Color]::FromArgb([int]$alpha, [int]$r, [int]$g, [int]$b))
        }
    }

    $outputDir = Split-Path -Parent $Output
    if ($outputDir) {
        New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
    }
    $result.Save($Output, [System.Drawing.Imaging.ImageFormat]::Png)
}
finally {
    if ($result) {
        $result.Dispose()
    }
    if ($bitmap) {
        $bitmap.Dispose()
    }
}

Write-Output "Wrote $Output"
