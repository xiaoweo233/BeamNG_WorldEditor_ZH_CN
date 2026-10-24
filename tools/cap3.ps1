Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
public class WinCap3 {
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
  public delegate bool EnumProc(IntPtr hWnd, IntPtr lParam);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb, IntPtr lParam);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint pid);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT r);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int n);
  [DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr hWnd);
  public static IntPtr FindLargest(uint pid, out long area) {
    IntPtr best = IntPtr.Zero; long bestArea = 0;
    EnumWindows(delegate(IntPtr h, IntPtr l) {
      uint p; GetWindowThreadProcessId(h, out p);
      if (p == pid && IsWindowVisible(h)) {
        RECT r; if (GetWindowRect(h, out r)) {
          long a = (long)(r.Right - r.Left) * (r.Bottom - r.Top);
          if (a > bestArea) { bestArea = a; best = h; }
        }
      }
      return true;
    }, IntPtr.Zero);
    area = bestArea;
    return best;
  }
}
"@
$procs = Get-Process -Name "BeamNG.drive*" -ErrorAction SilentlyContinue
if (-not $procs) { Write-Output "NO_PROC"; exit 1 }
$h = [IntPtr]::Zero; $area = 0
foreach ($p in $procs) {
  $a = 0
  $cand = [WinCap3]::FindLargest([uint32]$p.Id, [ref]$a)
  if ($cand -ne [IntPtr]::Zero -and $a -gt $area) { $area = $a; $h = $cand }
}
if ($h -eq [IntPtr]::Zero) { Write-Output "NO_WINDOW"; exit 1 }
[WinCap3]::ShowWindow($h, 9) | Out-Null
[WinCap3]::BringWindowToTop($h) | Out-Null
[WinCap3]::SetForegroundWindow($h) | Out-Null
Start-Sleep -Milliseconds 1500
$r = New-Object WinCap3+RECT
[WinCap3]::GetWindowRect($h, [ref]$r) | Out-Null
$w = $r.Right - $r.Left; $hgt = $r.Bottom - $r.Top
if ($w -lt 200 -or $hgt -lt 200) { Write-Output "SMALL ${w}x${hgt}"; exit 2 }
$bmp = New-Object System.Drawing.Bitmap $w, $hgt
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($r.Left, $r.Top, 0, 0, $bmp.Size)
$out = "D:\Documents\Beamng\current\mods\_work\window_shot.png"
$bmp.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()
Write-Output "SAVED $out ${w}x${hgt} area=$area"
