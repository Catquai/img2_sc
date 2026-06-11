Add-Type -AssemblyName System.Drawing

$OutDir = Join-Path (Get-Location) "generated_clean_icon_variants"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

function ColorFromHex([string]$Hex, [int]$Alpha = 255) {
    $h = $Hex.TrimStart("#")
    return [System.Drawing.Color]::FromArgb($Alpha,
        [Convert]::ToInt32($h.Substring(0, 2), 16),
        [Convert]::ToInt32($h.Substring(2, 2), 16),
        [Convert]::ToInt32($h.Substring(4, 2), 16))
}

function New-RoundRectPath([float]$X, [float]$Y, [float]$W, [float]$H, [float]$R) {
    $p = New-Object System.Drawing.Drawing2D.GraphicsPath
    $d = $R * 2
    $p.AddArc($X, $Y, $d, $d, 180, 90)
    $p.AddArc($X + $W - $d, $Y, $d, $d, 270, 90)
    $p.AddArc($X + $W - $d, $Y + $H - $d, $d, $d, 0, 90)
    $p.AddArc($X, $Y + $H - $d, $d, $d, 90, 90)
    $p.CloseFigure()
    return $p
}

function Fill-RoundRect($G, [float]$X, [float]$Y, [float]$W, [float]$H, [float]$R, $Color) {
    $path = New-RoundRectPath $X $Y $W $H $R
    $brush = New-Object System.Drawing.SolidBrush $Color
    $G.FillPath($brush, $path)
    $brush.Dispose()
    $path.Dispose()
}

function Fill-Poly($G, $Points, $Color) {
    $pts = @()
    foreach ($p in $Points) {
        $pts += New-Object System.Drawing.PointF($p[0], $p[1])
    }
    $brush = New-Object System.Drawing.SolidBrush $Color
    $G.FillPolygon($brush, $pts)
    $brush.Dispose()
}

function Save-Icon([string]$Name, [int]$Size, [string]$Top, [string]$Bottom, [scriptblock]$DrawSymbol) {
    $S = 4
    $W = $Size * $S
    $bmp = New-Object System.Drawing.Bitmap $W, $W, ([System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $rect = New-Object System.Drawing.RectangleF(0, 0, $W, $W)
    $brush = New-Object System.Drawing.Drawing2D.LinearGradientBrush($rect, (ColorFromHex $Top), (ColorFromHex $Bottom), 90)
    $clip = New-RoundRectPath 0 0 ($W - 1) ($W - 1) ($W * 0.26)
    $g.SetClip($clip)
    $g.FillRectangle($brush, $rect)
    $g.ResetClip()
    $brush.Dispose()
    $clip.Dispose()

    $glowBrush = New-Object System.Drawing.SolidBrush (ColorFromHex "#ffffff" 22)
    $g.FillEllipse($glowBrush, ($W * .12), ($W * .07), ($W * .76), ($W * .78))
    $glowBrush.Dispose()

    & $DrawSymbol $g $W $W

    $small = New-Object System.Drawing.Bitmap $Size, $Size, ([System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $sg = [System.Drawing.Graphics]::FromImage($small)
    $sg.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $sg.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $sg.DrawImage($bmp, 0, 0, $Size, $Size)
    $sg.Dispose()
    $bmp.Dispose()
    $g.Dispose()
    $small.Save((Join-Path $OutDir $Name), [System.Drawing.Imaging.ImageFormat]::Png)
    $small.Dispose()
}

$Folder = {
    param($g, $W, $H)
    Fill-RoundRect $g ($W*.17) ($H*.27) ($W*.66) ($H*.48) ($W*.105) (ColorFromHex "#fff2b0" 245)
    Fill-RoundRect $g ($W*.17) ($H*.33) ($W*.66) ($H*.46) ($W*.09) (ColorFromHex "#ffd15b" 235)
    Fill-RoundRect $g ($W*.17) ($H*.27) ($W*.30) ($H*.16) ($W*.085) (ColorFromHex "#fff5c7" 250)
    $b = New-Object System.Drawing.SolidBrush (ColorFromHex "#fff2b0" 245)
    $g.FillRectangle($b, ($W*.25), ($H*.37), ($W*.55), ($H*.07)); $b.Dispose()
    Fill-RoundRect $g ($W*.24) ($H*.48) ($W*.52) ($H*.20) ($W*.045) (ColorFromHex "#ffe98f" 154)
}

$Android = {
    param($g, $W, $H)
    Fill-RoundRect $g ($W*.26) ($H*.30) ($W*.48) ($H*.47) ($W*.18) (ColorFromHex "#c7ff8a" 225)
    $b = New-Object System.Drawing.SolidBrush (ColorFromHex "#b6f56f" 225)
    $g.FillRectangle($b, ($W*.26), ($H*.48), ($W*.48), ($H*.28)); $b.Dispose()
    $pen = New-Object System.Drawing.Pen((ColorFromHex "#d9ffba" 245), ($W*.035))
    $g.DrawLine($pen, ($W*.35), ($H*.25), ($W*.28), ($H*.15))
    $g.DrawLine($pen, ($W*.65), ($H*.25), ($W*.73), ($H*.15))
    $pen.Dispose()
    $eye = New-Object System.Drawing.SolidBrush (ColorFromHex "#19c84f" 235)
    $g.FillEllipse($eye, ($W*.38), ($H*.34), ($W*.07), ($H*.07))
    $g.FillEllipse($eye, ($W*.57), ($H*.34), ($W*.07), ($H*.07))
    $eye.Dispose()
    $line = New-Object System.Drawing.Pen((ColorFromHex "#64dd58" 125), ($W*.025))
    $g.DrawLine($line, ($W*.29), ($H*.51), ($W*.71), ($H*.51)); $line.Dispose()
}

$Image = {
    param($g, $W, $H)
    Fill-RoundRect $g ($W*.20) ($H*.20) ($W*.60) ($H*.60) ($W*.13) (ColorFromHex "#b8ffc9" 232)
    Fill-RoundRect $g ($W*.28) ($H*.28) ($W*.44) ($H*.44) ($W*.055) (ColorFromHex "#51df6e" 225)
    Fill-Poly $g @(@(($W * .31),($H * .67)),@(($W * .45),($H * .48)),@(($W * .56),($H * .60)),@(($W * .63),($H * .53)),@(($W * .71),($H * .67))) (ColorFromHex "#28cf55" 255)
    Fill-RoundRect $g ($W*.61) ($H*.34) ($W*.09) ($H*.09) ($W*.04) (ColorFromHex "#30d659" 255)
    Fill-RoundRect $g ($W*.34) ($H*.38) ($W*.23) ($H*.30) ($W*.03) (ColorFromHex "#24d760" 218)
}

$Video = {
    param($g, $W, $H)
    Fill-RoundRect $g ($W*.20) ($H*.21) ($W*.60) ($H*.58) ($W*.14) (ColorFromHex "#c1efff" 226)
    Fill-RoundRect $g ($W*.28) ($H*.29) ($W*.44) ($H*.42) ($W*.075) (ColorFromHex "#9edfff" 172)
    Fill-Poly $g @(@(($W * .43),($H * .39)),@(($W * .43),($H * .61)),@(($W * .62),($H * .50))) (ColorFromHex "#20acd8" 255)
    $pen = New-Object System.Drawing.Pen((ColorFromHex "#74d6f2" 92), ($W*.035))
    $g.DrawEllipse($pen, ($W*.37), ($H*.33), ($W*.29), ($H*.33)); $pen.Dispose()
}

$Cleanup = {
    param($g, $W, $H)
    Fill-RoundRect $g ($W*.31) ($H*.36) ($W*.38) ($H*.41) ($W*.055) (ColorFromHex "#ceff8b" 230)
    Fill-RoundRect $g ($W*.23) ($H*.29) ($W*.54) ($H*.08) ($W*.04) (ColorFromHex "#dfffba" 245)
    Fill-RoundRect $g ($W*.40) ($H*.22) ($W*.20) ($H*.10) ($W*.05) (ColorFromHex "#eaffc9" 245)
    $b = New-Object System.Drawing.SolidBrush (ColorFromHex "#b7f070" 195)
    $g.FillRectangle($b, ($W*.37), ($H*.39), ($W*.26), ($H*.28)); $b.Dispose()
    $pen = New-Object System.Drawing.Pen((ColorFromHex "#4acb47" 210), ($W*.045))
    $g.DrawLine($pen, ($W*.36), ($H*.65), ($W*.64), ($H*.65)); $pen.Dispose()
}

Save-Icon "notif_bigfile_variant.png" 108 "#fff83c" "#ffa826" $Folder
Save-Icon "notif_ic_app_variant.png" 108 "#82ff9b" "#48df64" $Android
Save-Icon "icon_image_variant.png" 120 "#8dffa1" "#46de68" $Image
Save-Icon "icon_tt_clean_video_variant.png" 120 "#42e8f2" "#28a8e8" $Video
Save-Icon "notif_ic_cleanup_variant.png" 108 "#79ff99" "#49df66" $Cleanup
