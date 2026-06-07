param(
    [Parameter(Mandatory = $true)]
    [string]$Source,
    [Parameter(Mandatory = $true)]
    [string]$Output,
    [string]$KeyColor = "#00ff00",
    [int]$Tolerance = 70,
    [int]$Softness = 35,
    [int]$Despill = 25,
    [int]$KeyDominanceThreshold = 8,
    [int]$AlphaCutoff = 3
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
$keyChannels = @($key.R, $key.G, $key.B)
$highChannelIndexes = @()
$lowChannelIndexes = @()
for ($index = 0; $index -lt 3; $index++) {
    if ($keyChannels[$index] -ge 128) {
        $highChannelIndexes += $index
    }
    else {
        $lowChannelIndexes += $index
    }
}
if ($highChannelIndexes.Count -eq 0 -or $lowChannelIndexes.Count -eq 0) {
    throw "KeyColor must contain at least one high and one low RGB channel, such as #00ff00, #ff00ff, #0000ff, or #ff0000."
}

function Get-AverageChannel {
    param(
        [int[]]$Channels,
        [int[]]$Indexes
    )
    $sum = 0.0
    foreach ($index in $Indexes) {
        $sum += $Channels[$index]
    }
    return $sum / $Indexes.Count
}

$keyHighAverage = Get-AverageChannel -Channels $keyChannels -Indexes $highChannelIndexes
$keyLowAverage = Get-AverageChannel -Channels $keyChannels -Indexes $lowChannelIndexes
$keyDominanceRange = [Math]::Max(1.0, $keyHighAverage - $keyLowAverage)
$resolved = Resolve-Path -LiteralPath $Source
$bitmap = [System.Drawing.Bitmap]::FromFile($resolved.Path)
$result = New-Object System.Drawing.Bitmap -ArgumentList @(
    $bitmap.Width,
    $bitmap.Height,
    [System.Drawing.Imaging.PixelFormat]::Format32bppArgb
)

try {
    for ($y = 0; $y -lt $bitmap.Height; $y++) {
        for ($x = 0; $x -lt $bitmap.Width; $x++) {
            $p = $bitmap.GetPixel($x, $y)
            $dr = $p.R - $key.R
            $dg = $p.G - $key.G
            $db = $p.B - $key.B
            $distance = [Math]::Sqrt($dr * $dr + $dg * $dg + $db * $db)

            $pixelChannels = @([int]$p.R, [int]$p.G, [int]$p.B)
            $pixelHighAverage = Get-AverageChannel -Channels $pixelChannels -Indexes $highChannelIndexes
            $pixelLowAverage = Get-AverageChannel -Channels $pixelChannels -Indexes $lowChannelIndexes
            $keyDominance = $pixelHighAverage - $pixelLowAverage
            $dominanceAlpha = [Math]::Round(255 * (1 - ([Math]::Max(0, $keyDominance) / $keyDominanceRange)))
            $dominanceAlpha = [Math]::Max(0, [Math]::Min(255, $dominanceAlpha))

            if ($distance -le $Tolerance -or $dominanceAlpha -le 0) {
                $alpha = 0
            }
            elseif ($distance -le ($Tolerance + $Softness)) {
                $alpha = [Math]::Round(255 * (($distance - $Tolerance) / [Math]::Max(1, $Softness)))
            }
            else {
                $alpha = $p.A
            }

            if ($keyDominance -gt $KeyDominanceThreshold) {
                $alpha = [Math]::Min($alpha, $dominanceAlpha)
            }

            if ($alpha -le $AlphaCutoff) {
                # Transparent pixels must not retain hidden key-color RGB because
                # later resizing can interpolate that RGB back into visible edges.
                $alpha = 0
                $r = 0
                $g = 0
                $b = 0
            }
            elseif ($alpha -lt 255) {
                # Reverse the compositing of a semi-transparent foreground over the key color.
                $a = $alpha / 255.0
                $r = [Math]::Round(($p.R - (1 - $a) * $key.R) / $a)
                $g = [Math]::Round(($p.G - (1 - $a) * $key.G) / $a)
                $b = [Math]::Round(($p.B - (1 - $a) * $key.B) / $a)
                $r = [Math]::Max(0, [Math]::Min(255, $r))
                $g = [Math]::Max(0, [Math]::Min(255, $g))
                $b = [Math]::Max(0, [Math]::Min(255, $b))
            }
            else {
                $r = $p.R
                $g = $p.G
                $b = $p.B
            }

            if ($alpha -gt 0 -and $Despill -gt 0) {
                $correctedChannels = @([double]$r, [double]$g, [double]$b)
                $correctedHighAverage = Get-AverageChannel -Channels $correctedChannels -Indexes $highChannelIndexes
                $correctedLowAverage = Get-AverageChannel -Channels $correctedChannels -Indexes $lowChannelIndexes
                $spill = [Math]::Max(0, $correctedHighAverage - $correctedLowAverage - $Despill)
                if ($spill -gt 0) {
                    foreach ($index in $highChannelIndexes) {
                        $correctedChannels[$index] = [Math]::Max(0, $correctedChannels[$index] - $spill)
                    }
                    $r = [Math]::Round($correctedChannels[0])
                    $g = [Math]::Round($correctedChannels[1])
                    $b = [Math]::Round($correctedChannels[2])
                }
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
