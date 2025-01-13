import subprocess
import time
import re

iqcapture_path = r"C:/Users/AWCC/Downloads/RSA_API-master/RSA_API-master/Utilities/RSA_API Apps V3.11/Apps/x64/IQcapture.exe"

# シリアル番号どデバイスIDを取得・記録するための配列
device_serial_mapping = {
    "B021101": None,
    "B021110": None,
}

# 処理リスト
tasks = [
    ("dev={B021110} cf=5190e6 bw=40e6 dest=2 fn=iqstream_5170-5210_B021110 msec=1000", "dev={B021101} cf=922.5e6 bw=15e6 dest=2 fn=iqstream_915-930_B021101 msec=1000"),
    ("dev={B021110} cf=5230e6 bw=40e6 dest=2 fn=iqstream_5210-5250_B021110 msec=1000", "dev={B021101} cf=2417.5e6 bw=35e6 dest=2 fn=iqstream_2400-2435_B021101 msec=1000"),
    ("dev={B021110} cf=5270e6 bw=40e6 dest=2 fn=iqstream_5250-5290_B021110 msec=1000", "dev={B021101} cf=2450e6 bw=30e6 dest=2 fn=iqstream_2435-2465_B021101 msec=1000"),
    ("dev={B021110} cf=5310e6 bw=40e6 dest=2 fn=iqstream_5290-5330_B021110 msec=1000", "dev={B021101} cf=2482.5e6 bw=35e6 dest=2 fn=iqstream_2465-2500_B021101 msec=1000"),
    ("dev={B021110} cf=5505e6 bw=30e6 dest=2 fn=iqstream_5490-5520_B021110 msec=1000", ""),
    ("dev={B021110} cf=5540e6 bw=40e6 dest=2 fn=iqstream_5520-5560_B021110 msec=1000", ""),
    ("dev={B021110} cf=5580e6 bw=40e6 dest=2 fn=iqstream_5560-5600_B021110 msec=1000", ""),
    ("dev={B021110} cf=5620e6 bw=40e6 dest=2 fn=iqstream_5600-5640_B021110 msec=1000", ""),
    ("dev={B021110} cf=5660e6 bw=40e6 dest=2 fn=iqstream_5640-5680_B021110 msec=1000", ""),
    ("dev={B021110} cf=5695e6 bw=30e6 dest=2 fn=iqstream_5680-5710_B021110 msec=1000", ""),
]


def get_device_mapping():
    #IQcapture.exeを引数なしで実行、シリアル番号とデバイスIDの対応を取得
    try:
        result = subprocess.run([iqcapture_path], capture_output=True, text=True, shell=True)
        output = result.stdout
        pattern = r"Dev:(\d+)\s+ID:(\d+)\s+S/N:\"(\w+)\""
        matches = re.findall(pattern, output)

        for dev, _, serial in matches:
            if serial in device_serial_mapping:
                device_serial_mapping[serial] = dev

        print(f"devs: {device_serial_mapping}")
    except Exception as e:
        print(f"errr: {e}")

def process_task(dev0_args, dev1_args):
    #与えられた引数でIQ記録処理
    processes = []

    if dev0_args:
        dev0_args = dev0_args.format(**device_serial_mapping)
        print(f"strt: {dev0_args}")
        process = subprocess.Popen(
            [iqcapture_path] + dev0_args.split(),
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        processes.append((process, dev0_args))

    if dev1_args:
        dev1_args = dev1_args.format(**device_serial_mapping)
        print(f"strt: {dev1_args}")
        process = subprocess.Popen(
            [iqcapture_path] + dev1_args.split(),
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        processes.append((process, dev1_args))

    for process, args in processes:
        process.wait()
        print(f"cmpl: {args}")

def run_tasks():
    #処理リストを順に実行
    for dev0_args, dev1_args in tasks:
        process_task(dev0_args, dev1_args)
        time.sleep(1)

if __name__ == "__main__":
    print(f"strt: init")
    get_device_mapping()
    if None in device_serial_mapping.values():
        print(f"errr: init")
        print(f"errr: デバイスIDが正しく取得できませんでした。USBケーブルの再接続や充電ケーブルの接続を試してください。")
    else:
        print(f"cmpl: init")
        run_tasks()
