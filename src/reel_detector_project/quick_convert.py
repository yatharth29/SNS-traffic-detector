#!/usr/bin/env python3
"""
Quick PCAP to CSV converter for Thursday traffic data
"""
import csv
import struct
import sys
from pathlib import Path

def quick_pcap_to_csv(pcap_path, csv_path):
    """Convert PCAP to CSV using basic file reading"""
    print(f"Converting {pcap_path} to {csv_path}...")
    
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['ts', 'length', 'src', 'dst'])
        
        # Read PCAP file in binary mode
        with open(pcap_path, 'rb') as pcapfile:
            # Read PCAP global header (24 bytes)
            # Magic number, version, timezone, sigfigs, snaplen, linktype
            global_header = pcapfile.read(24)
            if len(global_header) < 24:
                print("Error: Invalid PCAP file - too short")
                return
            
            # Check magic number (0xa1b2c3d4 for big-endian, 0xd4c3b2a1 for little-endian)
            magic = struct.unpack('I', global_header[:4])[0]
            if magic not in [0xa1b2c3d4, 0xd4c3b2a1]:
                print(f"Warning: Unexpected magic number: {hex(magic)}")
            
            packet_count = 0
            while True:
                # Read packet header (16 bytes)
                header = pcapfile.read(16)
                if len(header) < 16:
                    break
                
                # Parse packet header: ts_sec, ts_usec, incl_len, orig_len
                ts_sec, ts_usec, incl_len, orig_len = struct.unpack('IIII', header)
                timestamp = ts_sec + ts_usec / 1000000.0
                
                # Validate packet length
                if incl_len > 65535 or incl_len == 0:
                    print(f"Warning: Invalid packet length {incl_len} at packet {packet_count}")
                    continue
                
                # Read packet data
                packet_data = pcapfile.read(incl_len)
                if len(packet_data) < incl_len:
                    print(f"Warning: Could not read full packet data for packet {packet_count}")
                    break
                
                # Extract IP addresses if possible (simplified parsing)
                src_ip = "0.0.0.0"
                dst_ip = "0.0.0.0"
                
                # Try to parse IP header (minimum 20 bytes for IPv4 header)
                if len(packet_data) >= 20:
                    try:
                        # Check if it's IPv4 (version 4, header length 5-15)
                        version_ihl = packet_data[0]
                        version = (version_ihl >> 4) & 0x0F
                        ihl = (version_ihl & 0x0F) * 4
                        
                        if version == 4 and ihl >= 20 and len(packet_data) >= ihl:
                            # Extract source and destination IP addresses
                            src_ip = '.'.join(str(b) for b in packet_data[12:16])
                            dst_ip = '.'.join(str(b) for b in packet_data[16:20])
                    except:
                        pass  # Use default values if parsing fails
                
                writer.writerow([timestamp, incl_len, src_ip, dst_ip])
                packet_count += 1
                
                if packet_count % 10000 == 0:
                    print(f"Processed {packet_count} packets...")
    
    print(f"Conversion complete! Processed {packet_count} packets.")
    print(f"Output saved to: {csv_path}")

if __name__ == '__main__':
    pcap_file = "data/raw/Thursday-WorkingHours.pcap"
    csv_file = "data/thursday_traffic.csv"
    
    if not Path(pcap_file).exists():
        print(f"Error: PCAP file not found: {pcap_file}")
        sys.exit(1)
    
    quick_pcap_to_csv(pcap_file, csv_file)
