param(
    [Parameter(Mandatory = $true)][int]$TargetPid,
    [string]$ButtonText = 'Sempre carregar',
    [int]$MaxRounds = 12
)

$ErrorActionPreference = 'Continue'

$src = @'
using System;
using System.Runtime.InteropServices;
using System.Text;

public static class SecDlg
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

    public static string FindAndClick(uint pid, string buttonText)
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
            result = "clicked hwnd=" + hit.ToInt64() + " on dialog hwnd=" + h.ToInt64() + " title='" + title + "'";
            return false;
        }, IntPtr.Zero);
        return result;
    }

    public static int CountVisibleSecurityDialogs(uint pid)
    {
        int count = 0;
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
            if (title.ToString().Contains("Seguran")) count++;
            return true;
        }, IntPtr.Zero);
        return count;
    }
}
'@

Add-Type -TypeDefinition $src -ErrorAction SilentlyContinue

$pid32 = [uint32]$TargetPid
for ($round = 1; $round -le $MaxRounds; $round++) {
    $open = [SecDlg]::CountVisibleSecurityDialogs($pid32)
    Write-Host ("round {0}: visible security dialogs = {1}" -f $round, $open)
    if ($open -eq 0) {
        Write-Host 'queue empty'
        break
    }
    $msg = [SecDlg]::FindAndClick($pid32, $ButtonText)
    if ($msg -eq $null) {
        Write-Host "button '$ButtonText' not found in the open dialog"
        break
    }
    Write-Host ("round {0}: {1}" -f $round, $msg)
    Start-Sleep -Seconds 3
}

Write-Host ('final visible security dialogs = ' + [SecDlg]::CountVisibleSecurityDialogs($pid32))
