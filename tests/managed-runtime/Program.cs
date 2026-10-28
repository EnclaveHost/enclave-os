using System.Security.Cryptography;
using System.Runtime.InteropServices;

var expectedArchitecture = args.Length == 0 ? Architecture.RiscV64 : args[0] switch {
    "riscv64" => Architecture.RiscV64,
    "x86_64" => Architecture.X64,
    _ => throw new Exception("Unknown target architecture")
};
if (RuntimeInformation.ProcessArchitecture != expectedArchitecture)
    throw new Exception("Wrong managed runtime architecture");
var expected = Enumerable.Range(0, 10000).Select(i => (long)i * i).Sum();
long parallel = 0;
Parallel.For(0, 10000, new ParallelOptions { MaxDegreeOfParallelism = 2 },
    i => Interlocked.Add(ref parallel, (long)i * i));
if (parallel != expected) throw new Exception("Parallel JIT arithmetic differs");
var bytes = System.Text.Encoding.UTF8.GetBytes("abc");
if (Convert.ToHexString(SHA256.HashData(bytes)) != "BA7816BF8F01CFEA414140DE5DAE2223B00361A396177A9CB410FF61F20015AD")
    throw new Exception("Crypto reference mismatch");
var file = Path.GetTempFileName();
try {
    await File.WriteAllBytesAsync(file, bytes);
    if (!(await File.ReadAllBytesAsync(file)).SequenceEqual(bytes))
        throw new Exception("Async file mismatch");
} finally { File.Delete(file); }
if (Environment.GetEnvironmentVariable("ENCLAVE_EXPECT_POLICY") == "1") {
    if (Native.geteuid() != 1000) throw new Exception("Wrong desktop UID");
    foreach (var task in Directory.GetDirectories("/proc/self/task")) {
        var fields = File.ReadAllLines(task + "/status")
            .Select(line => line.Split(':', 2)).Where(pair => pair.Length == 2)
            .ToDictionary(pair => pair[0], pair => pair[1].Trim());
        if (fields["NoNewPrivs"] != "1" || fields["Seccomp"] != "2")
            throw new Exception("Managed thread did not inherit policy");
    }
    var memory = Native.mmap(IntPtr.Zero, 4096, 7, 0x22, -1, 0);
    var error = Marshal.GetLastPInvokeError();
    if (memory != new IntPtr(-1) || (error != 1 && error != 12))
        throw new Exception("Explicit RWX mapping was not rejected");
    if (File.ReadAllLines("/proc/self/maps").Any(line =>
        line.Split(' ', StringSplitOptions.RemoveEmptyEntries)[1].StartsWith("rwx")))
        throw new Exception("Managed process has an RWX mapping");
    Console.WriteLine("ENCLAVE_MANAGED_POLICY_OK");
}
Console.WriteLine($"PASS: {expectedArchitecture} managed arithmetic, threads, SHA256 and async I/O; {RuntimeInformation.FrameworkDescription}");

static class Native {
    [DllImport("libc", SetLastError = true)]
    public static extern IntPtr mmap(IntPtr address, nuint length, int prot, int flags, int fd, long offset);
    [DllImport("libc")]
    public static extern uint geteuid();
}
