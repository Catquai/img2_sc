param(
    [Parameter(Mandatory = $true)]
    [string]$Source,
    [Parameter(Mandatory = $true)]
    [string]$Output,
    [string]$KeyColor = "#00ff00",
    [int]$Tolerance = 70,
    [int]$Softness = 35,
    [int]$Despill = 25,
    [bool]$EdgeConnectedOnly = $true
)

Add-Type -AssemblyName System.Drawing

if ($KeyColor -notmatch '^#([0-9a-fA-F]{6})$') {
    throw "Use a hex color like #00ff00."
}
$hex = $KeyColor.Substring(1)
$keyR = [Convert]::ToInt32($hex.Substring(0, 2), 16)
$keyG = [Convert]::ToInt32($hex.Substring(2, 2), 16)
$keyB = [Convert]::ToInt32($hex.Substring(4, 2), 16)

if (-not ("EdgeConnectedChromaKey" -as [type])) {
    Add-Type -ReferencedAssemblies "System.Drawing" -TypeDefinition @"
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Runtime.InteropServices;

public static class EdgeConnectedChromaKey
{
    static double Distance(byte b, byte g, byte r, int keyR, int keyG, int keyB)
    {
        int dr = r - keyR;
        int dg = g - keyG;
        int db = b - keyB;
        return Math.Sqrt(dr * dr + dg * dg + db * db);
    }

    public static void Process(
        string sourcePath, string outputPath,
        int keyR, int keyG, int keyB,
        int tolerance, int softness, int despill,
        bool edgeConnectedOnly)
    {
        using (Bitmap original = new Bitmap(sourcePath))
        using (Bitmap bitmap = new Bitmap(original.Width, original.Height, PixelFormat.Format32bppArgb))
        {
            using (Graphics g = Graphics.FromImage(bitmap))
            {
                g.DrawImage(original, 0, 0, original.Width, original.Height);
            }

            int w = bitmap.Width;
            int h = bitmap.Height;
            Rectangle rect = new Rectangle(0, 0, w, h);
            BitmapData data = bitmap.LockBits(rect, ImageLockMode.ReadWrite, PixelFormat.Format32bppArgb);
            int stride = data.Stride;
            int byteCount = Math.Abs(stride) * h;
            byte[] pixels = new byte[byteCount];
            Marshal.Copy(data.Scan0, pixels, 0, byteCount);
            bool[] removable = new bool[w * h];

            Func<int, bool> isCandidate = delegate(int index)
            {
                int x = index % w;
                int y = index / w;
                int offset = y * stride + x * 4;
                return Distance(pixels[offset], pixels[offset + 1], pixels[offset + 2], keyR, keyG, keyB)
                    <= tolerance + softness;
            };

            if (edgeConnectedOnly)
            {
                Queue<int> queue = new Queue<int>();
                for (int x = 0; x < w; x++) { queue.Enqueue(x); queue.Enqueue((h - 1) * w + x); }
                for (int y = 0; y < h; y++) { queue.Enqueue(y * w); queue.Enqueue(y * w + w - 1); }
                while (queue.Count > 0)
                {
                    int index = queue.Dequeue();
                    if (index < 0 || index >= removable.Length || removable[index] || !isCandidate(index)) continue;
                    removable[index] = true;
                    int x = index % w;
                    int y = index / w;
                    if (x > 0) queue.Enqueue(index - 1);
                    if (x < w - 1) queue.Enqueue(index + 1);
                    if (y > 0) queue.Enqueue(index - w);
                    if (y < h - 1) queue.Enqueue(index + w);
                }
            }
            else
            {
                for (int index = 0; index < removable.Length; index++) removable[index] = isCandidate(index);
            }

            for (int y = 0; y < h; y++)
            {
                for (int x = 0; x < w; x++)
                {
                    int index = y * w + x;
                    int offset = y * stride + x * 4;
                    byte b = pixels[offset];
                    byte g = pixels[offset + 1];
                    byte r = pixels[offset + 2];
                    byte originalAlpha = pixels[offset + 3];
                    double distance = Distance(b, g, r, keyR, keyG, keyB);

                    int alpha = originalAlpha;
                    if (removable[index])
                    {
                        if (distance <= tolerance) alpha = 0;
                        else alpha = (int)Math.Round(originalAlpha * ((distance - tolerance) / Math.Max(1.0, softness)));
                    }

                    if (alpha > 0 && despill > 0 && keyG > keyR && keyG > keyB && g > r && g > b)
                    {
                        g = (byte)Math.Min(g, Math.Min(255, Math.Max(r, b) + despill));
                    }

                    pixels[offset + 1] = g;
                    pixels[offset + 3] = (byte)Math.Max(0, Math.Min(255, alpha));
                }
            }

            Marshal.Copy(pixels, 0, data.Scan0, byteCount);
            bitmap.UnlockBits(data);
            string directory = Path.GetDirectoryName(outputPath);
            if (!String.IsNullOrEmpty(directory)) Directory.CreateDirectory(directory);
            bitmap.Save(outputPath, ImageFormat.Png);
        }
    }
}
"@
}

[EdgeConnectedChromaKey]::Process(
    (Resolve-Path -LiteralPath $Source).Path,
    $Output,
    $keyR,
    $keyG,
    $keyB,
    $Tolerance,
    $Softness,
    $Despill,
    $EdgeConnectedOnly
)

Write-Output "Wrote $Output (EdgeConnectedOnly=$EdgeConnectedOnly)"
