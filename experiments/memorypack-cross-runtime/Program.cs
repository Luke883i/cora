using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using MemoryPack;

if (args.Length != 5)
    throw new ArgumentException("F5 usage: emit|consume GOLDENS.json DIRECTORY EXPECTED_MAJOR RECEIPT.json");
string operation = args[0];
string goldens = args[1];
string directory = args[2];
int expectedMajor = int.Parse(args[3]);
string receiptPath = args[4];
if (Environment.Version.Major != expectedMajor)
    throw new InvalidOperationException($"Expected real runtime {expectedMajor}; got {Environment.Version}");
if (operation != "emit" && operation != "consume")
    throw new ArgumentException("Unsupported operation");
using var source = JsonDocument.Parse(File.ReadAllText(goldens));
var cases = source.RootElement.GetProperty("cases").EnumerateArray().ToArray();
if (cases.Length != 10) throw new InvalidOperationException("Expected ten independent oracle cases");
int assertions = 0;
void Check(bool predicate, string identity)
{
    assertions++;
    if (!predicate) throw new InvalidOperationException("F5 native contract violation: " + identity);
}
void Bytes(byte[] actual, byte[] expected, string identity)
{
    Check(actual.SequenceEqual(expected), identity + " actual=" + Convert.ToHexString(actual) + " expected=" + Convert.ToHexString(expected));
}
void EqualTime(DateTimeOffset actual, DateTimeOffset expected, string identity)
{
    Check(actual.UtcTicks == expected.UtcTicks && actual.Offset == expected.Offset && actual.Ticks == expected.Ticks, identity);
}
Directory.CreateDirectory(directory);
foreach (var entry in cases)
{
    string id = entry.GetProperty("id").GetString()!;
    if (id.Any(c => !(char.IsLetterOrDigit(c) || c == '-')))
        throw new InvalidDataException("Invalid fixture identity");
    long ticks = entry.GetProperty("utcTicks").GetInt64();
    int offset = entry.GetProperty("offsetMinutes").GetInt32();
    DateTimeOffset value = new DateTimeOffset(ticks, TimeSpan.Zero).ToOffset(TimeSpan.FromMinutes(offset));
    byte[] net10 = Convert.FromHexString(entry.GetProperty("net10Hex").GetString()!);
    byte[] net9 = Convert.FromHexString(entry.GetProperty("net9Hex").GetString()!);
    byte[] unity = Convert.FromHexString(entry.GetProperty("unityHex").GetString()!);
    Check(net10.Length == 16 && net9.Length == 16 && unity.Length == 16, id + ":sizes");
    if (operation == "emit")
    {
        byte[] emittedNet10 = MemoryPackSerializer.Serialize<Net10DateTimeOffset>(value);
        byte[] emittedUnity = MemoryPackSerializer.Serialize<UnityDateTimeOffset>(value);
        Bytes(emittedNet10, net10, id + ":net10-vs-external-oracle");
        Bytes(emittedUnity, unity, id + ":unity-vs-external-oracle");
        File.WriteAllBytes(Path.Combine(directory, id + ".net10.bin"), emittedNet10);
        File.WriteAllBytes(Path.Combine(directory, id + ".unity.bin"), emittedUnity);
        byte[] native = MemoryPackSerializer.Serialize(value);
        Check(native.Length == 16, id + ":native-size");
        EqualTime(MemoryPackSerializer.Deserialize<DateTimeOffset>(native), value, id + ":native-local-only");
        File.WriteAllBytes(Path.Combine(directory, id + ".native-local-only.bin"), native);
    }
    else
    {
        byte[] inboundNet10 = File.ReadAllBytes(Path.Combine(directory, id + ".net10.bin"));
        byte[] inboundUnity = File.ReadAllBytes(Path.Combine(directory, id + ".unity.bin"));
        Bytes(inboundNet10, net10, id + ":net10-persisted-byte-identity");
        Bytes(inboundUnity, unity, id + ":unity-persisted-byte-identity");
        EqualTime(MemoryPackSerializer.Deserialize<Net10DateTimeOffset>(inboundNet10), value, id + ":net10-cross-process");
        EqualTime(MemoryPackSerializer.Deserialize<UnityDateTimeOffset>(inboundUnity), value, id + ":unity-cross-process");
        EqualTime(MemoryPackSerializer.Deserialize<Net10DateTimeOffset>(net9), value, id + ":net9-golden-compat");
    }
}
var receipt = new {
    schema = "cora-memorypack-native-f5-process/v1", operation,
    runtime_major = Environment.Version.Major,
    framework = System.Runtime.InteropServices.RuntimeInformation.FrameworkDescription,
    cases = cases.Length, assertions, status = "PASS",
    contract = operation == "emit" ? "fixed-wrapper-wire-emission" : "fixed-wrapper-cross-process-consumption"
};
Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(receiptPath))!);
File.WriteAllText(receiptPath, JsonSerializer.Serialize(receipt));
Console.WriteLine(JsonSerializer.Serialize(receipt));
