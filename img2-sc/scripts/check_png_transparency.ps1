param(
    [Parameter(Mandatory = $true)]
    [string]$Path,
    [ValidateRange(1, 2147483647)]
    [int]$SampleStep = 1
)

Add-Type -AssemblyName System.Drawing

$resolved = Resolve-Path -LiteralPath $Path
$image = [System.Drawing.Bitmap]::FromFile($resolved)

try {
    $hasAlphaFormat = [System.Drawing.Image]::IsAlphaPixelFormat($image.PixelFormat)
    $transparentCount = 0
    $partialAlphaCount = 0
    $opaqueCount = 0
    $checkedCount = 0

    for ($y = 0; $y -lt $image.Height; $y += $SampleStep) {
        for ($x = 0; $x -lt $image.Width; $x += $SampleStep) {
            $pixel = $image.GetPixel($x, $y)
            $checkedCount++
            if ($pixel.A -eq 0) {
                $transparentCount++
            }
            elseif ($pixel.A -lt 255) {
                $partialAlphaCount++
            }
            elseif ($pixel.A -eq 255) {
                $opaqueCount++
            }
        }
    }

    $hasTransparentPixels = $transparentCount -gt 0
    Write-Output "$($resolved.Path): $($image.Width)x$($image.Height), alpha_format=$hasAlphaFormat, transparent_pixels=$transparentCount, partial_alpha_pixels=$partialAlphaCount, opaque_pixels=$opaqueCount, checked_pixels=$checkedCount, sample_step=$SampleStep"

    if (-not $hasAlphaFormat -or -not $hasTransparentPixels) {
        exit 2
    }
}
finally {
    $image.Dispose()
}
