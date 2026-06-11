param(
    [Parameter(Mandatory = $true)][string]$Source,
    [Parameter(Mandatory = $true)][string]$Output,
    [int]$Size = 108
)

Add-Type -AssemblyName System.Drawing
Add-Type -ReferencedAssemblies "System.Drawing" -TypeDefinition @"
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;

public static class GreenScreenIconProcessor
{
    static bool IsKeyGreen(byte b, byte g, byte r, byte a)
    {
        if (a < 8) return true;
        if (g < 170) return false;
        if (g < r + 55) return false;
        if (g < b + 55) return false;
        int dr = r;
        int dg = g - 255;
        int db = b;
        return (dr * dr + dg * dg + db * db) < 22500;
    }

    public static void Process(string sourcePath, string outputPath, int size)
    {
        using (Bitmap original = new Bitmap(sourcePath))
        using (Bitmap src = new Bitmap(original.Width, original.Height, PixelFormat.Format32bppArgb))
        {
            using (Graphics gg = Graphics.FromImage(src))
            {
                gg.DrawImage(original, 0, 0, original.Width, original.Height);
            }

            int w = src.Width;
            int h = src.Height;
            Rectangle rect = new Rectangle(0, 0, w, h);
            BitmapData data = src.LockBits(rect, ImageLockMode.ReadWrite, PixelFormat.Format32bppArgb);
            int stride = data.Stride;
            int bytesLen = Math.Abs(stride) * h;
            byte[] bytes = new byte[bytesLen];
            Marshal.Copy(data.Scan0, bytes, 0, bytesLen);

            bool[] visited = new bool[w * h];
            Queue<int> q = new Queue<int>();
            for (int x = 0; x < w; x++) { q.Enqueue(x); q.Enqueue((h - 1) * w + x); }
            for (int y = 0; y < h; y++) { q.Enqueue(y * w); q.Enqueue(y * w + w - 1); }

            while (q.Count > 0)
            {
                int idx = q.Dequeue();
                if (idx < 0 || idx >= visited.Length || visited[idx]) continue;
                int x = idx % w;
                int y = idx / w;
                int off = y * stride + x * 4;
                if (!IsKeyGreen(bytes[off], bytes[off + 1], bytes[off + 2], bytes[off + 3])) continue;
                visited[idx] = true;
                if (x > 0) q.Enqueue(idx - 1);
                if (x < w - 1) q.Enqueue(idx + 1);
                if (y > 0) q.Enqueue(idx - w);
                if (y < h - 1) q.Enqueue(idx + w);
            }

            int minX = w, minY = h, maxX = -1, maxY = -1;
            for (int y = 0; y < h; y++)
            {
                for (int x = 0; x < w; x++)
                {
                    int idx = y * w + x;
                    int off = y * stride + x * 4;
                    if (visited[idx])
                    {
                        bytes[off] = 0;
                        bytes[off + 1] = 0;
                        bytes[off + 2] = 0;
                        bytes[off + 3] = 0;
                    }
                    else if (bytes[off + 3] > 8)
                    {
                        if (x < minX) minX = x;
                        if (y < minY) minY = y;
                        if (x > maxX) maxX = x;
                        if (y > maxY) maxY = y;
                    }
                }
            }
            Marshal.Copy(bytes, 0, data.Scan0, bytesLen);
            src.UnlockBits(data);

            if (maxX < minX || maxY < minY) throw new Exception("No foreground pixels found after green-screen removal.");

            int contentW = maxX - minX + 1;
            int contentH = maxY - minY + 1;
            using (Bitmap target = new Bitmap(size, size, PixelFormat.Format32bppArgb))
            using (Graphics g = Graphics.FromImage(target))
            {
                g.Clear(Color.FromArgb(0, 0, 0, 0));
                g.SmoothingMode = SmoothingMode.AntiAlias;
                g.InterpolationMode = InterpolationMode.HighQualityBicubic;
                g.PixelOffsetMode = PixelOffsetMode.HighQuality;
                double scale = Math.Min((double)size / contentW, (double)size / contentH);
                int drawW = (int)Math.Round(contentW * scale);
                int drawH = (int)Math.Round(contentH * scale);
                int dx = (int)Math.Round((size - drawW) / 2.0);
                int dy = (int)Math.Round((size - drawH) / 2.0);
                Rectangle srcRect = new Rectangle(minX, minY, contentW, contentH);
                Rectangle dstRect = new Rectangle(dx, dy, drawW, drawH);
                g.DrawImage(src, dstRect, srcRect, GraphicsUnit.Pixel);
                target.Save(outputPath, ImageFormat.Png);
            }
        }
    }
}
"@

$outDir = Split-Path -Parent $Output
if ($outDir) { New-Item -ItemType Directory -Force -Path $outDir | Out-Null }
[GreenScreenIconProcessor]::Process($Source, $Output, $Size)
