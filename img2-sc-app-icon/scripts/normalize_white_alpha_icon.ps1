param(
    [Parameter(Mandatory = $true)]
    [string]$Source,
    [Parameter(Mandatory = $true)]
    [string]$Output,
    [ValidateRange(0, 254)]
    [int]$AlphaCutoff = 2
)

Add-Type -AssemblyName System.Drawing

$sourcePath = (Resolve-Path -LiteralPath $Source).Path
$sourceImage = [System.Drawing.Bitmap]::FromFile($sourcePath)
$result = New-Object System.Drawing.Bitmap -ArgumentList @(
    $sourceImage.Width,
    $sourceImage.Height,
    [System.Drawing.Imaging.PixelFormat]::Format32bppArgb
)

try {
    for ($y = 0; $y -lt $sourceImage.Height; $y++) {
        for ($x = 0; $x -lt $sourceImage.Width; $x++) {
            $pixel = $sourceImage.GetPixel($x, $y)
            if ($pixel.A -le $AlphaCutoff) {
                $result.SetPixel($x, $y, [System.Drawing.Color]::FromArgb(0, 0, 0, 0))
            }
            else {
                $result.SetPixel($x, $y, [System.Drawing.Color]::FromArgb($pixel.A, 255, 255, 255))
            }
        }
    }

    $outputDir = Split-Path -Parent $Output
    if ($outputDir) {
        New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
    }
    $result.Save($Output, [System.Drawing.Imaging.ImageFormat]::Png)
}
finally {
    $result.Dispose()
    $sourceImage.Dispose()
}

Write-Output "Normalized visible pixels to pure white and preserved alpha: $Output"
