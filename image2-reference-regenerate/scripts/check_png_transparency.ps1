param(
    [Parameter(Mandatory = $true)]
    [string]$Path,
    [int]$SampleStep = 4
)

Add-Type -AssemblyName System.Drawing

$resolved = Resolve-Path -LiteralPath $Path
$image = [System.Drawing.Bitmap]::FromFile($resolved)

try {
    $hasAlphaFormat = [System.Drawing.Image]::IsAlphaPixelFormat($image.PixelFormat)
    $transparentCount = 0
    $opaqueCount = 0
    $sampledCount = 0

    for ($y = 0; $y -lt $image.Height; $y += [Math]::Max(1, $SampleStep)) {
        for ($x = 0; $x -lt $image.Width; $x += [Math]::Max(1, $SampleStep)) {
            $pixel = $image.GetPixel($x, $y)
            $sampledCount++
            if ($pixel.A -eq 0) {
                $transparentCount++
            }
            elseif ($pixel.A -eq 255) {
                $opaqueCount++
            }
        }
    }

    $hasTransparentPixels = $transparentCount -gt 0
    Write-Output "$($resolved.Path): $($image.Width)x$($image.Height), alpha_format=$hasAlphaFormat, transparent_samples=$transparentCount/$sampledCount"

    if (-not $hasAlphaFormat -or -not $hasTransparentPixels) {
        exit 2
    }
}
finally {
    $image.Dispose()
}
