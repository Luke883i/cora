using System;
using System.Buffers;
using Xunit;

namespace MemoryPack.Tests;

public class NativeVarIntByteContract
{
    [Fact]
    public void UInt16PayloadConsumesAllBytes()
    {
        var buffer = new ArrayBufferWriter<byte>();
        using var state = MemoryPackWriterOptionalStatePool.Rent(null);
        var writer = new MemoryPackWriter<ArrayBufferWriter<byte>>(ref buffer, state);
        writer.WriteVarInt((ushort)200);
        writer.WriteVarInt((byte)1);
        writer.Flush();

        Assert.Equal("85C80001", Convert.ToHexString(buffer.WrittenSpan));
        using var readState = MemoryPackReaderOptionalStatePool.Rent(null);
        var reader = new MemoryPackReader(buffer.WrittenSpan, readState);
        Assert.Equal((byte)200, reader.ReadVarIntByte());
        Assert.Equal((byte)1, reader.ReadVarIntByte());
    }

    [Fact]
    public void UInt16ValueOverflowIsRejected()
    {
        var buffer = new ArrayBufferWriter<byte>();
        using var state = MemoryPackWriterOptionalStatePool.Rent(null);
        var writer = new MemoryPackWriter<ArrayBufferWriter<byte>>(ref buffer, state);
        writer.WriteVarInt((ushort)256);
        writer.Flush();

        Assert.Equal("850001", Convert.ToHexString(buffer.WrittenSpan));
        using var readState = MemoryPackReaderOptionalStatePool.Rent(null);
        var reader = new MemoryPackReader(buffer.WrittenSpan, readState);
        bool overflow = false;
        try { reader.ReadVarIntByte(); }
        catch (OverflowException) { overflow = true; }
        Assert.True(overflow, "UInt16(256) must fail checked conversion to byte");
    }

    [Fact]
    public void DirectByteWireMarkerRegressionControl()
    {
        var buffer = new ArrayBufferWriter<byte>();
        using var state = MemoryPackWriterOptionalStatePool.Rent(null);
        var writer = new MemoryPackWriter<ArrayBufferWriter<byte>>(ref buffer, state);
        writer.WriteVarInt((byte)200);
        writer.WriteVarInt((byte)1);
        writer.Flush();

        Assert.Equal("87C801", Convert.ToHexString(buffer.WrittenSpan));
        using var readState = MemoryPackReaderOptionalStatePool.Rent(null);
        var reader = new MemoryPackReader(buffer.WrittenSpan, readState);
        Assert.Equal((byte)200, reader.ReadVarIntByte());
        Assert.Equal((byte)1, reader.ReadVarIntByte());
    }
}
