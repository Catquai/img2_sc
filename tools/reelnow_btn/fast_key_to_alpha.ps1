param(
    [Parameter(Mandatory = $true)][string]$Source,
    [Parameter(Mandatory = $true)][string]$Output,
    [string]$KeyColor = "#ff00ff",
    [int]$Tolerance = 90,
    [int]$Softness = 45,
    [int]$EdgeConnectedOnly = 1
)

Add-Type -AssemblyName System.Drawing

if ($KeyColor -notmatch '^#([0-9a-fA-F]{6})$') {
    throw "Use a hex color like #ff00ff."
}
$hex = $KeyColor.Substring(1)
$keyR = [Convert]::ToInt32($hex.Substring(0, 2), 16)
$keyG = [Convert]::ToInt32($hex.Substring(2, 2), 16)
$keyB = [Convert]::ToInt32($hex.Substring(4, 2), 16)

Add-Type -ReferencedAssemblies "System.Drawing" -TypeDefinition @"
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Runtime.InteropServices;

public static class FastKeyToAlpha
{
    static double Distance(byte b, byte g, byte r, int kr, int kg, int kb)
    {
        int dr = r - kr, dg = g - kg, db = b - kb;
        return Math.Sqrt(dr * dr + dg * dg + db * db);
    }

    public static void Run(string source, string output, int kr, int kg, int kb, int tolerance, int softness, bool edgeOnly)
    {
        using (Bitmap original = new Bitmap(source))
        using (Bitmap bmp = new Bitmap(original.Width, original.Height, PixelFormat.Format32bppArgb))
        {
            using (Graphics g = Graphics.FromImage(bmp)) g.DrawImage(original, 0, 0, original.Width, original.Height);
            int w = bmp.Width, h = bmp.Height;
            Rectangle rect = new Rectangle(0, 0, w, h);
            BitmapData data = bmp.LockBits(rect, ImageLockMode.ReadWrite, PixelFormat.Format32bppArgb);
            int stride = data.Stride;
            byte[] px = new byte[Math.Abs(stride) * h];
            Marshal.Copy(data.Scan0, px, 0, px.Length);
            bool[] remove = new bool[w * h];

            Func<int,bool> candidate = delegate(int idx) {
                int x = idx % w, y = idx / w, off = y * stride + x * 4;
                return Distance(px[off], px[off+1], px[off+2], kr, kg, kb) <= tolerance + softness;
            };

            if (edgeOnly)
            {
                Queue<int> q = new Queue<int>();
                for (int x=0; x<w; x++) { q.Enqueue(x); q.Enqueue((h-1)*w+x); }
                for (int y=0; y<h; y++) { q.Enqueue(y*w); q.Enqueue(y*w+w-1); }
                while (q.Count > 0)
                {
                    int idx = q.Dequeue();
                    if (idx < 0 || idx >= remove.Length || remove[idx] || !candidate(idx)) continue;
                    remove[idx] = true;
                    int x = idx % w, y = idx / w;
                    if (x > 0) q.Enqueue(idx - 1);
                    if (x < w - 1) q.Enqueue(idx + 1);
                    if (y > 0) q.Enqueue(idx - w);
                    if (y < h - 1) q.Enqueue(idx + w);
                }
            }
            else
            {
                for (int i=0; i<remove.Length; i++) remove[i] = candidate(i);
            }

            for (int y=0; y<h; y++)
            for (int x=0; x<w; x++)
            {
                int idx = y*w+x, off = y*stride+x*4;
                if (!remove[idx]) continue;
                double d = Distance(px[off], px[off+1], px[off+2], kr, kg, kb);
                int a = d <= tolerance ? 0 : (int)Math.Round(255.0 * ((d - tolerance) / Math.Max(1, softness)));
                px[off+3] = (byte)Math.Max(0, Math.Min(255, a));
                if (a == 0) { px[off] = 0; px[off+1] = 0; px[off+2] = 0; }
            }

            Marshal.Copy(px, 0, data.Scan0, px.Length);
            bmp.UnlockBits(data);
            string dir = Path.GetDirectoryName(output);
            if (!String.IsNullOrEmpty(dir)) Directory.CreateDirectory(dir);
            bmp.Save(output, ImageFormat.Png);
        }
    }
}
"@

[FastKeyToAlpha]::Run((Resolve-Path -LiteralPath $Source).Path, $Output, $keyR, $keyG, $keyB, $Tolerance, $Softness, ($EdgeConnectedOnly -ne 0))
Write-Output "Wrote $Output"
