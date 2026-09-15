param(
    [Parameter(Mandatory = $true)][int]$TargetPid,
    [Parameter(Mandatory = $true)][string]$ButtonText,
    [switch]$WhatIfOnly
)

$ErrorActionPreference = 'Stop'

$signature = @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

public static class DlgClick
{
    public delegate bool EnumProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc callback, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool EnumChildWindows(IntPtr parent, EnumProc callback, IntPtr lParam);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetClassName(IntPtr hWnd, StringBuilder text, int count);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern IntPtr SendMessage(IntPtr hWnd, uint msg, IntPtr wParam, IntPtr lParam);

    public const uint BM_CLICK = 0x00F5;

    public static string FindButton(uint pid, string buttonText)
    {
        string found = null;
        EnumWindows((hWnd, lParam) =>
        {
            uint ownerPid;
            GetWindowThreadProcessId(hWnd, out ownerPid);
            if (ownerPid != pid) return true;
            var cls = new StringBuilder(256);
            GetClassName(hWnd, cls, cls.Capacity);
            if (cls.ToString() != "#32770") return true;

            EnumChildWindows(hWnd, (child, lp) =>
            {
                var childCls = new StringBuilder(256);
                GetClassName(child, childCls, childCls.Capacity);
                if (childCls.ToString() != "Button") return true;
                var text = new StringBuilder(512);
                GetWindowText(child, text, text.Capacity);
                if (text.ToString() == buttonText)
                {
                    found = child.ToInt64().ToString();
                    return false;
                }
                return true;
            }, IntPtr.Zero);

            return found == null;
        }, IntPtr.Zero);
        return found;
    }

    public static void Click(string handleText)
    {
        var handle = new IntPtr(long.Parse(handleText));
        SendMessage(handle, BM_CLICK, IntPtr.Zero, IntPtr.Zero);
    }
}
'@

Add-Type -TypeDefinition $signature -ErrorAction SilentlyContinue

$handle = [DlgClick]::FindButton([uint32]$TargetPid, $ButtonText)
if ($handle -eq $null) {
    Write-Host "button '$ButtonText' not found in pid $TargetPid"
    exit 2
}

Write-Host "found button '$ButtonText' hwnd=$handle in pid $TargetPid"
if ($WhatIfOnly) {
    Write-Host 'what-if only; no click sent'
    exit 0
}

[DlgClick]::Click($handle)
Write-Host 'BM_CLICK sent'
Start-Sleep -Seconds 2
$still = [DlgClick]::FindButton([uint32]$TargetPid, $ButtonText)
if ($still -eq $null) {
    Write-Host 'dialog button is gone; dialog dismissed'
}
else {
    Write-Host 'dialog button still present'
}
