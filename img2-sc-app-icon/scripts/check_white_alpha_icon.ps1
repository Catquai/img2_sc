param(
    [Parameter(Mandatory = $true)]
    [string]$Path,
    [ValidateRange(1, 2147483647)]
    [int]$SampleStep = 1
)

Add-Type -AssemblyName System.Drawing

$resolved = Resolve-Path -LiteralPath $Path
$image = [System.Drawing.Bitmap]::FromFile($resolved.Path)
$transparentCount = 0
$visibleCount = 0
$nonWhiteVisibleCount = 0

try {
    for ($y = 0; $y -lt $image.Height; $y += $SampleStep) {
        for ($x = 0; $x -lt $image.Width; $x += $SampleStep) {
            $pixel = $image.GetPixel($x, $y)
            if ($pixel.A -eq 0) {
                $transparentCount++
            }
            else {
                $visibleCount++
                if ($pixel.R -ne 255 -or $pixel.G -ne 255 -or $pixel.B -ne 255) {
                    $nonWhiteVisibleCount++
                }
            }
        }
    }
}
finally {
    $image.Dispose()
}

Write-Output "$($resolved.Path): transparent_pixels=$transparentCount, visible_pixels=$visibleCount, non_white_visible_pixels=$nonWhiteVisibleCount, sample_step=$SampleStep"

if ($transparentCount -eq 0 -or $visibleCount -eq 0 -or $nonWhiteVisibleCount -gt 0) {
    exit 2
}
