#!/usr/bin/env python3
"""
Test script to examine first few packets of PCAP file
"""
import struct
from pathlib import Path

def examine_pcap_header(pcap_path, max_packets=10):
    """Examine the first few packets to understand the format"""
    print(f"Examining first {max_packets} packets of {pcap_path}")
    
    with open(pcap_path, 'rb') as pcapfile:
        # Read PCAP global header (24 bytes)
        global_header = pcapfile.read(24)
        print(f"Global header length: {len(global_header)} bytes")
        
        if len(global_header) >= 4:
            magic = struct.unpack('I', global_header[:4])[0]
            print(f"Magic number: {hex(magic)}")
            
            if magic == 0xa1b2c3d4:
                endian = '>'
                print("Detected big-endian PCAP format")
            elif magic == 0xd4c3b2a1:
                endian = '<'
                print("Detected little-endian PCAP format")
            else:
                print(f"Unexpected magic number - this might not be a standard PCAP file")
                return
        
        print("\nExamining packet headers:")
        print("-" * 60)
        
        for i in range(max_packets):
            # Read packet header (16 bytes)
            header = pcapfile.read(16)
            if len(header) < 16:
                print(f"Packet {i}: Could not read full header (only {len(header)} bytes)")
                break
            
            # Parse packet header
            try:
                ts_sec, ts_usec, incl_len, orig_len = struct.unpack(f'{endian}IIII', header)
                timestamp = ts_sec + ts_usec / 1000000.0
                
                print(f"Packet {i}:")
                print(f"  Timestamp: {timestamp}")
                print(f"  Included length: {incl_len}")
                print(f"  Original length: {orig_len}")
                
                # Check if length seems reasonable
                if incl_len > 65535:
                    print(f"  WARNING: Packet length {incl_len} is unusually large!")
                elif incl_len == 0:
                    print(f"  WARNING: Packet length is 0!")
                elif incl_len < 60:  # Minimum Ethernet frame size
                    print(f"  WARNING: Packet length {incl_len} is very small")
                else:
                    print(f"  Length looks reasonable")
                
                # Try to read packet data
                if incl_len > 0 and incl_len <= 65535:
                    packet_data = pcapfile.read(incl_len)
                    if len(packet_data) == incl_len:
                        print(f"  Successfully read {len(packet_data)} bytes of packet data")
                        
                        # Try to extract first few bytes
                        if len(packet_data) >= 4:
                            first_bytes = ' '.join(f'{b:02x}' for b in packet_data[:4])
                            print(f"  First 4 bytes: {first_bytes}")
                    else:
                        print(f"  WARNING: Could only read {len(packet_data)} of {incl_len} bytes")
                else:
                    print(f"  Skipping packet data due to invalid length")
                
                print()
                
            except Exception as e:
                print(f"Packet {i}: Error parsing header: {e}")
                print()
                break

if __name__ == '__main__':
    pcap_file = "data/raw/Thursday-WorkingHours.pcap"
    
    if not Path(pcap_file).exists():
        print(f"Error: PCAP file not found: {pcap_file}")
        exit(1)
    
    examine_pcap_header(pcap_file, max_packets=5)
