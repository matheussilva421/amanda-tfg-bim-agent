param(
    [Parameter(Mandatory = $true)][int]$TargetPid,
    [Parameter(Mandatory = $true)][string]$DialogTitle,
    [Parameter(Mandatory = $true)][string]$ButtonText
)

$ErrorActionPreference = 'Continue'

$src = @'
using System;
using System.Runtime.InteropServices;
using System.Text;

public static class OneClick
{
    public delegate bool EnumProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb, IntPtr lp);
    [DllImport("user32.dll")] public static extern bool EnumChildWindows(IntPtr parent, EnumProc cb, IntPtr lp);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint pid);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetClassName(IntPtr h, StringBuilder s, int n);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern IntPtr SendMessage(IntPtr h, uint msg, IntPtr wp, IntPtr lp);

    public const uint BM_CLICK = 0x00F5;

    public static string Click(uint pid, string dialogTitle, string buttonText)
    {
        string result = null;
        EnumWindows((h, lp) =>
        {
            uint p;
            GetWindowThreadProcessId(h, out p);
            if (p != pid) return true;
            var cls = new StringBuilder(256);
            GetClassName(h, cls, cls.Capacity);
            if (cls.ToString() != "#32770") return true;
            if (!IsWindowVisible(h)) return true;
            var title = new StringBuilder(512);
            GetWindowText(h, title, title.Capacity);
            if (!title.ToString().Equals(dialogTitle)) return true;

            IntPtr hit = IntPtr.Zero;
            EnumChildWindows(h, (c, l2) =>
            {
                var cc = new StringBuilder(256);
                GetClassName(c, cc, cc.Capacity);
                if (cc.ToString() != "Button") return true;
                var ct = new StringBuilder(512);
                GetWindowText(c, ct, ct.Capacity);
                if (ct.ToString() == buttonText)
                {
                    hit = c;
                    return false;
                }
                return true;
            }, IntPtr.Zero);

            if (hit == IntPtr.Zero) return true;
            SendMessage(hit, BM_CLICK, IntPtr.Zero, IntPtr.Zero);
            result = "clicked '" + buttonText + "' hwnd=" + hit.ToInt64() + " on dialog '" + title + "'";
            return false;
        }, IntPtr.Zero);
        return result;
    }
}
'@

Add-Type -TypeDefinition $src -ErrorAction SilentlyContinue
$msg = [OneClick]::Click([uint32]$TargetPid, $DialogTitle, $ButtonText)
if ($msg -eq $null) { Write-Host 'NOT CLICKED: no matching dialog/button' } else { Write-Host $msg }

