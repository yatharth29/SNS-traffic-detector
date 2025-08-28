#!/usr/bin/env python3
"""
Robust PCAP to CSV converter for Thursday traffic data
"""
import csv
import struct
import sys
from pathlib import Path

def robust_pcap_to_csv(pcap_path, csv_path):
    """Convert PCAP to CSV with better error handling"""
    print(f"Converting {pcap_path} to {csv_path}...")
    
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['ts', 'length', 'src', 'dst'])
        
        # Read PCAP file in binary mode
        with open(pcap_path, 'rb') as pcapfile:
            # Read PCAP global header (24 bytes)
            global_header = pcapfile.read(24)
            if len(global_header) < 24:
                print("Error: Invalid PCAP file - too short")
                return
            
            # Check magic number and determine endianness
            magic = struct.unpack('I', global_header[:4])[0]
            if magic == 0xa1b2c3d4:
                endian = '>'
                print("Detected big-endian PCAP format")
            elif magic == 0xd4c3b2a1:
                endian = '<'
                print("Detected little-endian PCAP format")
            else:
                print(f"Warning: Unexpected magic number: {hex(magic)}")
                endian = '<'  # Default to little-endian
            
            packet_count = 0
            error_count = 0
            
            while True:
                try:
                    # Read packet header (16 bytes)
                    header = pcapfile.read(16)
                    if len(header) < 16:
                        break
                    
                    # Parse packet header with correct endianness
                    ts_sec, ts_usec, incl_len, orig_len = struct.unpack(f'{endian}IIII', header)
                    timestamp = ts_sec + ts_usec / 1000000.0
                    
                    # Validate packet length
                    if incl_len > 65535 or incl_len == 0:
                        print(f"Warning: Invalid packet length {incl_len} at packet {packet_count}")
                        error_count += 1
                        # Skip this packet and try to find next valid header
                        continue
                    
                    # Read packet data
                    packet_data = pcapfile.read(incl_len)
                    if len(packet_data) < incl_len:
                        print(f"Warning: Could not read full packet data for packet {packet_count}")
                        break
                    
                    # Extract IP addresses with better parsing
                    src_ip, dst_ip = extract_ip_addresses(packet_data)
                    
                    writer.writerow([timestamp, incl_len, src_ip, dst_ip])
                    packet_count += 1
                    
                    if packet_count % 10000 == 0:
                        print(f"Processed {packet_count} packets...")
                        
                except Exception as e:
                    print(f"Error processing packet {packet_count}: {e}")
                    error_count += 1
                    # Try to recover by reading ahead
                    pcapfile.read(1)
                    continue
    
    print(f"Conversion complete!")
    print(f"Total packets processed: {packet_count}")
    print(f"Errors encountered: {error_count}")
    print(f"Output saved to: {csv_path}")

def extract_ip_addresses(packet_data):
    """Extract IP addresses from packet data with better parsing"""
    src_ip = "0.0.0.0"
    dst_ip = "0.0.0.0"
    
    try:
        # Minimum size for Ethernet + IP headers
        if len(packet_data) < 34:
            return src_ip, dst_ip
        
        # Skip Ethernet header (14 bytes) and check IP version
        ip_start = 14
        if ip_start + 20 > len(packet_data):
            return src_ip, dst_ip
        
        # Check if it's IPv4
        version_ihl = packet_data[ip_start]
        version = (version_ihl >> 4) & 0x0F
        
        if version == 4:
            # Extract IP addresses (offset 12 and 16 from IP header start)
            src_bytes = packet_data[ip_start + 12:ip_start + 16]
            dst_bytes = packet_data[ip_start + 16:ip_start + 20]
            
            if len(src_bytes) == 4 and len(dst_bytes) == 4:
                src_ip = '.'.join(str(b) for b in src_bytes)
                dst_ip = '.'.join(str(b) for b in dst_bytes)
                
    except Exception:
        pass  # Return default values if parsing fails
    
    return src_ip, dst_ip

if __name__ == '__main__':
    pcap_file = "data/raw/Thursday-WorkingHours.pcap"
    csv_file = "data/thursday_traffic.csv"
    
    if not Path(pcap_file).exists():
        print(f"Error: PCAP file not found: {pcap_file}")
        sys.exit(1)
    
    robust_pcap_to_csv(pcap_file, csv_file)
