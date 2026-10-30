using System;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text;

// microfreak-emu starts a native binary named "renode", or mono plus
// bin/Renode.exe. Renode 1.16 on Windows is a .NET Framework executable
// that runs on its own. This wrapper is that native binary.
internal static class RenodeWin
{
    private const string RenodeExe = @"C:\Users\thisi\dev\micro-orchid\.tools\renode-1.17.0\renode_1.17.0-portable\renode.exe";
    private const string RenodeRoot = @"C:\Users\thisi\dev\micro-orchid\.tools\renode-1.17.0\renode_1.17.0-portable";

    private static int Main(string[] args)
    {
        var psi = new ProcessStartInfo();
        psi.FileName = RenodeExe;
        psi.WorkingDirectory = RenodeRoot;
        psi.UseShellExecute = false;
        psi.Arguments = Quote(args);
        var process = Process.Start(psi);
        if (process == null)
            return 1;
        // mfemu kills this wrapper on timeout. Without a job, that leaves
        // Renode.exe running and holding the monitor port.
        var job = CreateJobObject(IntPtr.Zero, null);
        if (job != IntPtr.Zero)
        {
            var info = new JOBOBJECT_EXTENDED_LIMIT_INFORMATION();
            info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
            var size = Marshal.SizeOf(info);
            var ptr = Marshal.AllocHGlobal(size);
            Marshal.StructureToPtr(info, ptr, false);
            SetInformationJobObject(job, JobObjectExtendedLimitInformation, ptr, (uint)size);
            Marshal.FreeHGlobal(ptr);
            AssignProcessToJobObject(job, process.Handle);
        }
        process.WaitForExit();
        return process.ExitCode;
    }

    private const uint JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000;
    private const int JobObjectExtendedLimitInformation = 9;

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode)]
    private static extern IntPtr CreateJobObject(IntPtr lpJobAttributes, string name);

    [DllImport("kernel32.dll")]
    private static extern bool SetInformationJobObject(IntPtr hJob, int jobObjectInfoClass, IntPtr lpJobObjectInfo, uint cbJobObjectInfoLength);

    [DllImport("kernel32.dll")]
    private static extern bool AssignProcessToJobObject(IntPtr hJob, IntPtr hProcess);

    [StructLayout(LayoutKind.Sequential)]
    private struct JOBOBJECT_BASIC_LIMIT_INFORMATION
    {
        public long PerProcessUserTimeLimit;
        public long PerJobUserTimeLimit;
        public uint LimitFlags;
        public UIntPtr MinimumWorkingSetSize;
        public UIntPtr MaximumWorkingSetSize;
        public uint ActiveProcessLimit;
        public UIntPtr Affinity;
        public uint PriorityClass;
        public uint SchedulingClass;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct IO_COUNTERS
    {
        public ulong ReadOperationCount;
        public ulong WriteOperationCount;
        public ulong OtherOperationCount;
        public ulong ReadTransferCount;
        public ulong WriteTransferCount;
        public ulong OtherTransferCount;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct JOBOBJECT_EXTENDED_LIMIT_INFORMATION
    {
        public JOBOBJECT_BASIC_LIMIT_INFORMATION BasicLimitInformation;
        public IO_COUNTERS IoInfo;
        public UIntPtr ProcessMemoryLimit;
        public UIntPtr JobMemoryLimit;
        public UIntPtr PeakProcessMemoryUsed;
        public UIntPtr PeakJobMemoryUsed;
    }

    private static string Quote(string[] args)
    {
        var builder = new StringBuilder();
        foreach (var arg in args)
        {
            if (builder.Length > 0)
                builder.Append(' ');
            if (arg.IndexOfAny(new[] { ' ', '\t', '"' }) >= 0)
                builder.Append('"').Append(arg.Replace("\"", "\\\"")).Append('"');
            else
                builder.Append(arg);
        }
        return builder.ToString();
    }
}
