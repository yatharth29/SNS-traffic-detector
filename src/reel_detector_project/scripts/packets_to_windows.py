#!/usr/bin/env python3
"""
Convert packet CSV (ts,length,src,dst) into windowed features CSV.
- Prefilters to rows involving the target device IP for speed
- Auto-detects device IP using a capped sample if not provided
- Uses notebooks/windows.py compute_sliding_windows

Usage:
  python scripts/packets_to_windows.py --in data/thursday_traffic.csv --out data/windows_from_thursday.csv --device-ip 192.168.10.50 --win 10 --step 10
  python scripts/packets_to_windows.py --in data/thursday_traffic.csv --out data/windows_from_thursday.csv   # auto-detect device from sample
"""
import argparse
import os
import sys
import pandas as pd
from pathlib import Path

# Import windowing util
sys.path.append(str(Path('notebooks').resolve()))
from windows import compute_sliding_windows  # type: ignore

PRIVATE_PREFIXES = (
    '10.',
    '172.16.', '172.17.', '172.18.', '172.19.', '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.', '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.',
    '192.168.'
)

SAMPLE_ROWS_FOR_AUTODETECT = 250_000


def is_private(ip: str) -> bool:
    return isinstance(ip, str) and any(ip.startswith(p) for p in PRIVATE_PREFIXES)


def autodetect_device_ip_from_sample(csv_path: str) -> str:
    print(f'[autodetect] Sampling first {SAMPLE_ROWS_FOR_AUTODETECT} rows to detect device IP...')
    sample = pd.read_csv(csv_path, nrows=SAMPLE_ROWS_FOR_AUTODETECT)
    if not {'ts','length','src','dst'}.issubset(sample.columns):
        raise ValueError('Input must contain columns: ts,length,src,dst')
    recv = sample.groupby('dst')['length'].sum().sort_values(ascending=False)
    for ip, _ in recv.items():
        if is_private(ip):
            print(f'[autodetect] Chosen by dst bytes: {ip}')
            return ip
    send = sample.groupby('src')['length'].sum().sort_values(ascending=False)
    for ip, _ in send.items():
        if is_private(ip):
            print(f'[autodetect] Chosen by src bytes: {ip}')
            return ip
    fallback = str(recv.index[0]) if len(recv) else '0.0.0.0'
    print(f'[autodetect] Fallback: {fallback}')
    return fallback


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='inp', required=True, help='Input packet CSV path')
    ap.add_argument('--out', dest='out', required=True, help='Output windows CSV path')
    ap.add_argument('--device-ip', dest='device_ip', default=None, help='Device IP to compute features for')
    ap.add_argument('--win', dest='win', type=float, default=10.0, help='Window size seconds (default 10)')
    ap.add_argument('--step', dest='step', type=float, default=10.0, help='Step seconds (default 10)')
    args = ap.parse_args()

    inp = args.inp
    outp = args.out

    if not os.path.exists(inp):
        print(f'Input not found: {inp}')
        sys.exit(1)

    # Detect or use provided device IP
    device_ip = args.device_ip or autodetect_device_ip_from_sample(inp)
    print(f'Using device IP: {device_ip}')

    # Load full CSV but only required columns to save RAM
    usecols = ['ts','length','src','dst']
    print('[load] Reading full CSV with required columns...')
    df = pd.read_csv(inp, usecols=usecols)

    # Prefilter rows involving the device to speed up windowing dramatically
    print('[filter] Prefiltering to rows where src==device or dst==device...')
    mask = (df['src'] == device_ip) | (df['dst'] == device_ip)
    dff = df.loc[mask].copy()
    del df

    if dff.empty:
        print('No rows found involving device. Exiting.')
        sys.exit(2)

    dff = dff.sort_values('ts').reset_index(drop=True)

    print(f'[window] Computing windows (win={args.win}, step={args.step}) on {len(dff)} rows...')
    windows_df = compute_sliding_windows(dff, device_ip=device_ip, window_size=args.win, step=args.step)
    if windows_df.empty:
        print('No windows produced (empty dataframe).')
        sys.exit(3)

    Path(os.path.dirname(outp) or '.').mkdir(parents=True, exist_ok=True)
    windows_df.to_csv(outp, index=False)
    print(f'Saved {len(windows_df)} windows to {outp}')
    print('Columns:', list(windows_df.columns))

if __name__ == '__main__':
    main()
