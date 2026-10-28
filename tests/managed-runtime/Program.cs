using System.Security.Cryptography;
using System.Runtime.InteropServices;

if (RuntimeInformation.ProcessArchitecture != Architecture.RiscV64)
    throw new Exception("Not an RV64 managed runtime");
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
Console.WriteLine($"PASS: RV64 managed arithmetic, threads, SHA256 and async I/O; {RuntimeInformation.FrameworkDescription}");
