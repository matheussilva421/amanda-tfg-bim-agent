param([Parameter(Mandatory = $true)][int]$TargetPid)

$ErrorActionPreference = 'Continue'

$src = @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

public static class WinTree
{
    public delegate bool EnumProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb, IntPtr lp);
    [DllImport("user32.dll")] public static extern bool EnumChildWindows(IntPtr parent, EnumProc cb, IntPtr lp);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint pid);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetClassName(IntPtr h, StringBuilder s, int n);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);

    private static string Describe(IntPtr h, string prefix)
    {
        var cls = new StringBuilder(256);
        GetClassName(h, cls, cls.Capacity);
        var txt = new StringBuilder(512);
        GetWindowText(h, txt, txt.Capacity);
        return prefix + " hwnd=" + h.ToInt64() + " vis=" + IsWindowVisible(h) + " cls=" + cls + " txt=" + txt;
    }

    public static List<string> Dump(uint targetPid)
    {
        var list = new List<string>();
        EnumWindows((h, lp) =>
        {
            uint p;
            GetWindowThreadProcessId(h, out p);
            if (p != targetPid) return true;
            list.Add(Describe(h, "TOP"));
            EnumChildWindows(h, (c, l2) =>
            {
                list.Add(Describe(c, "    CHILD"));
                return true;
            }, IntPtr.Zero);
            return true;
        }, IntPtr.Zero);
        return list;
    }
}
'@

Add-Type -TypeDefinition $src -ErrorAction SilentlyContinue
[WinTree]::Dump([uint32]$TargetPid) | ForEach-Object { $_ }
