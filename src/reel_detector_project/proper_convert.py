#!/usr/bin/env python3
"""
Proper PCAP to CSV converter using tshark (fast path)
- Supports resume via --resume flag: continues from the last timestamp in existing CSV
- Optional --max to limit number of rows appended in this run
- Requires tshark to be installed and available on PATH
"""
import csv
import sys
import os
import argparse
import shutil
import subprocess
from pathlib import Path
from typing import Optional


def get_last_timestamp(csv_path: str) -> Optional[float]:
    """Return last timestamp from existing CSV, or None if not found."""
    if not os.path.exists(csv_path):
        return None
    last_ts: Optional[float] = None
    try:
        with open(csv_path, 'rb') as f:
            try:
                f.seek(0, os.SEEK_END)
            except OSError:
                return None
            size = f.tell()
            if size == 0:
                return None
            buffer_size = 8192
            data = b''
            pos = size
            while pos > 0:
                read_size = buffer_size if pos >= buffer_size else pos
                pos -= read_size
                f.seek(pos)
                chunk = f.read(read_size)
                data = chunk + data
                lines = data.splitlines()
                if pos != 0:
                    # keep the first (possibly partial) line for next loop
                    data = lines[0]
                    lines = lines[1:]
                for line in reversed(lines):
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith(b'ts,'):
                        return last_ts
                    parts = line.split(b',')
                    try:
                        ts_val = float(parts[0].decode('ascii', errors='ignore'))
                        last_ts = ts_val
                        return last_ts
                    except Exception:
                        continue
            return last_ts
    except Exception:
        return None


def ensure_tshark_available() -> None:
    if shutil.which('tshark') is None:
        print('Error: tshark not found on PATH. Please install Wireshark/tshark and try again.')
        sys.exit(1)


def build_tshark_cmd(pcap_path: str, min_ts: Optional[float], max_rows: Optional[int]) -> list[str]:
    cmd = [
        'tshark',
        '-r', pcap_path,
        '-T', 'fields',
        '-e', 'frame.time_epoch',
        '-e', 'frame.len',
        '-e', 'ip.src',
        '-e', 'ip.dst',
        '-E', 'header=n',
        '-E', 'separator=,',
        '-E', 'quote=n',
        '-E', 'occurrence=f',
    ]
    if min_ts is not None:
        cmd.extend(['-Y', f'frame.time_epoch > {min_ts}'])
    if max_rows is not None:
        cmd.extend(['-c', str(max_rows)])
    return cmd


def stream_tshark_to_csv(cmd: list[str], out_csv: str, append: bool) -> tuple[int, int]:
    """Run tshark and stream its CSV-like output into out_csv.
    Returns (rows_written, errors)
    """
    rows_written = 0
    errors = 0

    # Open CSV in text mode and write header if not appending
    with open(out_csv, 'a' if append else 'w', newline='') as f:
        writer = csv.writer(f)
        if not append:
            writer.writerow(['ts', 'length', 'src', 'dst'])

        # Launch tshark
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',
        )
        try:
            assert proc.stdout is not None
            for line in proc.stdout:
                line = line.strip('\r\n')
                if not line:
                    continue
                parts = line.split(',')
                # Normalize to 4 columns (ts,len,src,dst)
                if len(parts) < 2:
                    errors += 1
                    continue
                ts = parts[0]
                length = parts[1]
                src = parts[2] if len(parts) > 2 and parts[2] else '0.0.0.0'
                dst = parts[3] if len(parts) > 3 and parts[3] else '0.0.0.0'
                writer.writerow([ts, length, src, dst])
                rows_written += 1
        finally:
            # Drain and terminate
            try:
                proc.kill()
            except Exception:
                pass
            try:
                proc.wait(timeout=5)
            except Exception:
                pass
            # Print last stderr line if useful
            if proc.stderr is not None:
                err_out = proc.stderr.read() or ''
                if err_out.strip():
                    last_line = err_out.strip().splitlines()[-1]
                    print('tshark stderr:', last_line)
    return rows_written, errors


def convert_with_tshark(pcap_path: str, csv_path: str, resume: bool, max_rows: Optional[int]) -> bool:
    min_ts = None
    append = False
    if resume and os.path.exists(csv_path):
        min_ts = get_last_timestamp(csv_path)
        if min_ts is not None:
            print(f'Resume enabled. Skipping packets with ts <= {min_ts}')
            append = True
        else:
            print('Resume requested but no usable timestamp found. Starting fresh.')
    cmd = build_tshark_cmd(pcap_path, min_ts, max_rows)
    print('Running:', ' '.join(cmd))
    rows, errs = stream_tshark_to_csv(cmd, csv_path, append)
    print('Conversion complete!')
    print(f'Total rows written this run: {rows}')
    print(f'Errors (lines skipped): {errs}')
    print(f'Output saved to: {csv_path}')
    return rows > 0 or append  # consider success if we appended or wrote rows


def main():
    parser = argparse.ArgumentParser(description='Convert PCAP/PCAPNG to CSV using tshark')
    parser.add_argument('pcap', nargs='?', default='data/raw/Thursday-WorkingHours.pcap')
    parser.add_argument('out', nargs='?', default='data/thursday_traffic.csv')
    parser.add_argument('--max', type=int, default=None, help='Max rows to write in this run')
    parser.add_argument('--resume', action='store_true', help='Resume from last timestamp in existing CSV')
    args = parser.parse_args()

    ensure_tshark_available()

    pcap_file = args.pcap
    csv_file = args.out

    if not Path(pcap_file).exists():
        print(f'Error: PCAP file not found: {pcap_file}')
        sys.exit(1)

    ok = convert_with_tshark(pcap_file, csv_file, resume=args.resume, max_rows=args.max)
    sys.exit(0 if ok else 2)


if __name__ == '__main__':
    main()
