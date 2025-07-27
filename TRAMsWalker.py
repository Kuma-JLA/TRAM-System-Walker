import os
import re
import csv
import cv2
import time
import winsound
import pygame
from pynput import keyboard
import subprocess
import threading
from datetime import datetime
from pygrabber.dshow_graph import FilterGraph
import logging
import builtins

#各種パス設定
original_iqcapture_path = r"C:/Tektronix/TRAMsWalker/RSA_API_TRAMs-master/Utilities/RSA_API Apps V3.11/Apps/x64/IQcapture.exe"
iqcapture_path = r"C:/Tektronix/TRAMsWalker/RSA_API_TRAMs-master/Utilities/RSA_API Apps V3.11/Apps/x64/IQcapture_TRAMs.exe"
output_directory = r"C:/Tektronix/TRAMsWalker/results"
log_directory = r"C:/Tektronix/TRAMsWalker/results/logs"

#RSAシリアル番号指定
device_serial_mapping = {
    "B021101": None,
    "B021110": None,
}

# 処理リスト
tasks = [
    ("dev={B021110} cf=5190e6 bw=40e6 dest=2 fn=iqstream_5170-5210_B021110 msec=60000", "dev={B021101} cf=922.5e6 bw=15e6 dest=2 fn=iqstream_915-930_B021101 msec=60000"),
    ("dev={B021110} cf=5230e6 bw=40e6 dest=2 fn=iqstream_5210-5250_B021110 msec=60000", "dev={B021101} cf=2417.5e6 bw=35e6 dest=2 fn=iqstream_2400-2435_B021101 msec=60000"),
    ("dev={B021110} cf=5270e6 bw=40e6 dest=2 fn=iqstream_5250-5290_B021110 msec=60000", "dev={B021101} cf=2450e6 bw=30e6 dest=2 fn=iqstream_2435-2465_B021101 msec=60000"),
    ("dev={B021110} cf=5310e6 bw=40e6 dest=2 fn=iqstream_5290-5330_B021110 msec=60000", "dev={B021101} cf=2482.5e6 bw=35e6 dest=2 fn=iqstream_2465-2500_B021101 msec=60000"),
    ("dev={B021110} cf=5505e6 bw=30e6 dest=2 fn=iqstream_5490-5520_B021110 msec=60000", ""),
    ("dev={B021110} cf=5540e6 bw=40e6 dest=2 fn=iqstream_5520-5560_B021110 msec=60000", ""),
    ("dev={B021110} cf=5580e6 bw=40e6 dest=2 fn=iqstream_5560-5600_B021110 msec=60000", ""),
    ("dev={B021110} cf=5620e6 bw=40e6 dest=2 fn=iqstream_5600-5640_B021110 msec=60000", ""),
    ("dev={B021110} cf=5660e6 bw=40e6 dest=2 fn=iqstream_5640-5680_B021110 msec=60000", ""),
    ("dev={B021110} cf=5695e6 bw=30e6 dest=2 fn=iqstream_5680-5710_B021110 msec=60000", ""),
]
#正常ファイルサイズ
valid_sizes = [6720003352, 13440003352]

#ログ設定
os.makedirs(log_directory, exist_ok=True)
log_path = os.path.join(
    log_directory,
    datetime.now().strftime("session_%Y%m%d_%H%M%S.log")
)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    handlers=[
        logging.FileHandler(log_path, encoding="utf-8")
    ]
)
_orig_print = builtins.print
_orig_input = builtins.input
def print(*args, **kwargs):
    msg = " ".join(str(a) for a in args)
    logging.info(msg)
    _orig_print(*args, **kwargs)
def input(prompt=""):
    logging.info(f"INPUT prompt: {prompt!r}")
    resp = _orig_input(prompt)
    logging.info(f"INPUT response: {resp!r}")
    return resp
builtins.print = print
builtins.input = input

#カメラ初期化
graph = FilterGraph()
devices = graph.get_input_devices()
print("Available devices:", devices)
camera_name = "RICOH THETA UVC"
camera_id = devices.index(camera_name) if camera_name in devices else 0
print(f"Selected camera ID: {camera_id}")
def init_capture():
    global capture
    if 'capture' in globals():
        try:
            capture.release()
        except:
            pass
    capture = cv2.VideoCapture(camera_id)
    return capture.isOpened()
if not init_capture():
    print("カメラが開けません。カメラの状態を確認してください。")

#RSA測定ログ記録用CSVファイルのパスとヘッダ
csv_file_path = "execution_result.csv"
rsa_header = [
    "実験名", "TD", "CD", "SL", "実行時刻", "全体実行時間"
] + [f"time_B021101_{i+1}" for i in range(len(tasks))] + [f"time_B021110_{i+1}" for i in range(len(tasks))] + [f"size_B021101_{i+1}" for i in range(len(tasks))] + [f"size_B021110_{i+1}" for i in range(len(tasks))]

#測定完了画面表示関数
def flash_green_screen():
    """画面を指定色で点滅させ、キー・マウス・タッチ操作で停止"""
    key_pressed = False
    def on_event():
        nonlocal key_pressed
        key_pressed = True
    keyboard_listener = keyboard.Listener(on_press=lambda key: on_event())
    keyboard_listener.start()
    #色読み込み
    default_color = (0, 255, 0)
    color_file = os.path.expanduser("~/Desktop/Customize/color.txt")
    if os.path.exists(color_file):
        try:
            with open(color_file, "r") as f:
                line = f.readline().strip()
                r, g, b = map(int, line.split(","))
                flash_color = (r, g, b)
        except Exception as e:
            flash_color = default_color
    else:
        flash_color = default_color
    #点滅処理
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Flashing Color Screen")
    while not key_pressed:
        for event in pygame.event.get():
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
                key_pressed = True
        screen.fill(flash_color)
        pygame.display.flip()
        time.sleep(0.2)
        screen.fill((0, 0, 0))
        pygame.display.flip()
        time.sleep(0.2)
    pygame.quit()
    keyboard_listener.stop()

#画像キャプチャ関数
def capture_image():
    global cmpl_measure, capture
    sec = 0
    count = 1
    max_retries = 2 #再接続試行回数
    retry_delay = 2 #再接続間隔（秒）
    while not cmpl_measure:
        if sec % 60 == 0:
            if not capture.isOpened():
                print("カメラが切断されました。再接続を試みます…")
                for attempt in range(1, max_retries + 1):
                    if init_capture():
                        print(f"再接続成功（試行 {attempt} 回目）")
                        break
                    else:
                        print(f"再接続失敗（試行 {attempt} 回目）。{retry_delay}秒後に再試行します。")
                        time.sleep(retry_delay)
                else:
                    print("再接続に失敗しました。画像キャプチャをスキップします。")
                    sec += 1
                    time.sleep(1)
                    continue
            #フレーム取得（安定のため連続読み込み）
            ret = False
            frame = None
            for _ in range(10):
                ok, img = capture.read()
                if ok:
                    ret, frame = ok, img
                    break
            if ret:
                filename = f"{count}.jpg"
                cv2.imwrite(filename, frame)
                print(f"画像 {filename} を保存しました")
                count += 1
            else:
                print("フレームの取得に失敗しました。次回まで待機します。")
        sec += 1
        time.sleep(1)

#無線LAN測定
def signal_percent_to_dbm(percent):
    """シグナル強度(%)を dBm に変換"""
    return (percent / 2) - 100
def calculate_frequency(channel, band):
    """バンドとチャネルから周波数を算出"""
    try:
        channel = int(channel)
        if "2.4 GHz" in band:
            return 2407 + (channel * 5)
        elif "5 GHz" in band:
            return 5000 + (channel * 5)
        elif "6 GHz" in band:
            return 5950 + (channel * 5)
    except ValueError:
        print(f"チャネルの解析に失敗: {channel} (バンド: {band})")
    return ""
def parse_wifi_data(data):
    """取得したWi-Fiデータを解析"""
    wifi_list = []
    current_data = {}
    for line in data.split("\n"):
        line = line.strip()
        ssid_match = re.match(r"^SSID\s+\d+\s*:\s(.+)", line)
        bssid_match = re.match(r"^BSSID\s+\d+\s*:\s([\w:-]+)", line)
        signal_match = re.match(r"^シグナル\s*:\s(\d+)%", line)
        network_match = re.match(r"^ネットワークの種類\s*:\s(.+)", line)
        auth_match = re.match(r"^認証\s*:\s(.+)", line)
        encrypt_match = re.match(r"^暗号化\s*:\s(.+)", line)
        channel_match = re.match(r"^チャネル\s*:\s(\d+)", line)
        band_match = re.match(r"^バンド\s*:\s(.+)", line)
        wireless_type_match = re.match(r"^無線タイプ\s*:\s(.+)", line)
        basic_rates_match = re.match(r"^基本レート \(Mbps\)\s*:\s*(.+)", line)
        other_rates_match = re.match(r"^他のレート \(Mbps\)\s*:\s*(.+)", line)
        if ssid_match:
            if current_data:
                wifi_list.append(current_data)
            current_data = {"SSID": ssid_match.group(1)}
        elif bssid_match:
            current_data["BSSID"] = bssid_match.group(1)
        elif signal_match:
            percent = int(signal_match.group(1))
            current_data["シグナル(%)"] = percent
            current_data["RSSI_dBm"] = signal_percent_to_dbm(percent)
        elif network_match:
            current_data["ネットワークの種類"] = network_match.group(1)
        elif auth_match:
            current_data["認証"] = auth_match.group(1)
        elif encrypt_match:
            current_data["暗号化"] = encrypt_match.group(1)
        elif channel_match:
            current_data["チャネル"] = channel_match.group(1)
        elif band_match:
            band = band_match.group(1)
            current_data["バンド"] = band
        elif "チャネル" in current_data:
            current_data["周波数(MHz)"] = calculate_frequency(current_data["チャネル"], band)
        elif wireless_type_match:
            current_data["無線タイプ"] = wireless_type_match.group(1)
        elif basic_rates_match:
            current_data["基本レート(Mbps)"] = basic_rates_match.group(1)
        elif other_rates_match:
            current_data["他のレート(Mbps)"] = other_rates_match.group(1)
    if current_data:
        wifi_list.append(current_data)
    return wifi_list
def wifiscan_save_to_csv(wifi_list, measurement_td, filename="wifiscan_results.csv"):
    """Wi-Fiスキャンデータを指定されたディレクトリにCSVファイルとして保存"""
    #保存先ディレクトリのパスを生成
    save_dir = os.path.join(output_directory, experiment_name, filename)
    save_dir_path = os.path.dirname(save_dir)
    #保存先ディレクトリが存在しない場合は作成
    if save_dir_path and not os.path.exists(save_dir_path):
        os.makedirs(save_dir_path)
    #各Wi-Fiデータに TD を追加
    for wifi_data in wifi_list:
        wifi_data["実験名"] =  experiment_name
    for wifi_data in wifi_list:
        wifi_data["TD"] = measurement_td
    #ヘッダーのフィールド名
    fieldnames = [
        "実験名", "TD", "SSID", "BSSID", "シグナル(%)", "RSSI_dBm", "チャネル", "バンド", "周波数(MHz)",
        "ネットワークの種類", "認証", "暗号化", "無線タイプ", "基本レート(Mbps)", "他のレート(Mbps)"
    ]
    #ファイルが存在するか確認
    file_exists = os.path.exists(save_dir)
    #ファイルを開いて書き込み
    with open(save_dir, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        #初回のみヘッダーを追加
        if not file_exists:
            writer.writeheader()
        #Wi-Fiデータを書き込み
        writer.writerows(wifi_list)
def get_wifiscan_data():
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "networks", "mode=bssid"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        return result.stdout
    except Exception as e:
        print(f"Wi-Fiスキャン失敗: {e}")
        return ""
#WiFiをScanして保存する関数
def wifiscan():
    global cmpl_measure
    while not cmpl_measure:
        data = get_wifiscan_data()
        if not data:
            print("Wi-Fiスキャンデータが取得できませんでした")
            time.sleep(1)
            continue
        parsed_data = parse_wifi_data(data)
        wifiscan_save_to_csv(parsed_data, measurement_td)
        time.sleep(1)

#RSAシリアル番号↔デバイスID変換関数
def get_device_mapping():
    try:
        result = subprocess.run([original_iqcapture_path], capture_output=True, text=True, shell=True)
        output = result.stdout
        pattern = r"Dev:(\d+)\s+ID:(\d+)\s+S/N:\"(\w+)\""
        matches = re.findall(pattern, output)
        for dev, _, serial in matches:
            if serial in device_serial_mapping:
                device_serial_mapping[serial] = dev
        print(f"devs: {device_serial_mapping}")
    except Exception as e:
        print(f"errr: {e}")

#測定処理関数
def process_task(B021110_args, B021101_args, task_idx, times_B021110, times_B021101, sizes_B021110, sizes_B021101):
    processes = []

    if B021110_args:
        B021110_args = B021110_args.format(**device_serial_mapping)
        start_time = time.time()
        process = subprocess.Popen(
            [iqcapture_path] + B021110_args.split(),
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        processes.append((process, start_time, task_idx, "B021110", B021110_args))

    if B021101_args:
        B021101_args = B021101_args.format(**device_serial_mapping)
        start_time = time.time()
        process = subprocess.Popen(
            [iqcapture_path] + B021101_args.split(),
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        processes.append((process, start_time, task_idx, "B021101", B021101_args))

    for process, start_time, idx, device, args in processes:
        try:
            process.wait(timeout=300)  # 300秒以内に完了するか待機
        except subprocess.TimeoutExpired:
            print(f"        TIMEOUT: {device} {idx+1} 超過による強制終了")
            process.kill()

        elapsed_time = time.time() - start_time
        filename_match = re.search(r"fn=(\S+)", args)
        filename = filename_match.group(1) + ".tiq" if filename_match else "unknown.tiq"
        file_path = os.path.join(filename)

        size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        if device == "B021110":
            times_B021110[idx] = elapsed_time
            sizes_B021110[idx] = size
        elif device == "B021101":
            times_B021101[idx] = elapsed_time
            sizes_B021101[idx] = size

        print(f"        msrd: {device} {idx+1}\n               TIME: {elapsed_time:.2f}[s]\n               SIZE: {size}[byte]")

#測定処理ハンドリング関数
def run_tasks():
    global cmpl_measure, experiment_name, measurement_td, measurement_cd, measurement_sl
    #実行ディレクトリのパスを生成
    measurement_dir = os.path.join(output_directory, experiment_name, measurement_td)
    
    #ディレクトリが存在する場合、警告を表示し測定点名入力に戻る
    if os.path.exists(measurement_dir):
        print(f"警告: ディレクトリ {measurement_dir} は既に存在します。上書きによるデータ消失を防ぐため、別の測定点名を入力してください。")
        return
    #ディレクトリが存在しない場合、新規作成
    os.makedirs(measurement_dir, exist_ok=True)
    os.chdir(measurement_dir)
    print(f"作業ディレクトリを変更: {measurement_dir}")

    #測定中フラッグを未完了にリセット
    cmpl_measure = False
    
    # 画像キャプチャを別スレッドで開始
    capture_thread = threading.Thread(target=capture_image)
    capture_thread.daemon = True
    capture_thread.start()
    # WiFiScanを別スレッドで開始
    wifi_thread = threading.Thread(target=wifiscan)
    wifi_thread.daemon = True
    wifi_thread.start()

    times_B021110 = [0] * len(tasks)
    times_B021101 = [0] * len(tasks)
    sizes_B021110 = [0] * len(tasks)
    sizes_B021101 = [0] * len(tasks)
    start_time = time.time()
    for idx, (B021110_args, B021101_args) in enumerate(tasks):
        #1回目の測定
        process_task(B021110_args, B021101_args,
                    idx, times_B021110, times_B021101,
                    sizes_B021110, sizes_B021101)
        #失敗判定
        failed_B021110 = B021110_args and sizes_B021110[idx] not in valid_sizes
        failed_B021101 = B021101_args and sizes_B021101[idx] not in valid_sizes
        if failed_B021110 or failed_B021101:
            if failed_B021110:
                print(f"再試行: index {idx} の B021110 の測定データが不正 ({sizes_B021110[idx]}B)")
            if failed_B021101:
                print(f"再試行: index {idx} の B021101 の測定データが不正 ({sizes_B021101[idx]}B)")

            #失敗したものだけ再測定
            process_task(
                B021110_args if failed_B021110 else None,
                B021101_args if failed_B021101 else None,
                idx, times_B021110, times_B021101,
                sizes_B021110, sizes_B021101
            )

        elapsed = time.time() - start_time
        execution_time = {
            "実験名": experiment_name,
            "TD": measurement_td,
            "CD": measurement_cd,
            "SL": measurement_sl,
            "実行時刻": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "全体実行時間": elapsed,
        }
        for i in range(len(tasks)):
            execution_time[f"time_B021101_{i+1}"] = times_B021101[i]
            execution_time[f"time_B021110_{i+1}"] = times_B021110[i]
            execution_time[f"size_B021101_{i+1}"] = sizes_B021101[i]
            execution_time[f"size_B021110_{i+1}"] = sizes_B021110[i]
        #RSA測定内容ログ記録
        rsa_save_to_csv(execution_time)
    #全タスク完了後RSA測定内容ログ最終記録
    total_elapsed = time.time() - start_time
    summary = execution_time.copy()
    summary["全体実行時間"] = total_elapsed
    summary["実行時刻"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rsa_save_to_csv(summary)
    #測定完了フラッグ
    cmpl_measure = True
    #測定完了通知
    try:
        sound_path = os.path.expanduser("~/Desktop/Customize/sound.wav")
        winsound.PlaySound(sound_path, winsound.SND_FILENAME)
    except Exception as e:
        print(e)
        pass 
    flash_green_screen()
    
#RSA測定内容ログ出力関数
def rsa_save_to_csv(execution_time):
    """
    指定TDごとに1行を維持(更新/追加）。
    """
    csv_path = os.path.join(output_directory, execution_time["実験名"], f"rsa_results.csv")
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    #新規ファイルならヘッダー＋行を書き込んで終了
    if not os.path.exists(csv_path):
        with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rsa_header)
            writer.writeheader()
            writer.writerow(execution_time)
        return
    #読み込み－除外リスト作成
    rows = []
    with open(csv_path, mode="r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            #同一実験名＋TDの行はスキップ
            if not (row["実験名"] == execution_time["実験名"] and row["TD"] == execution_time["TD"]):
                rows.append(row)
    #上書き書き戻し＋新行追加
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rsa_header)
        writer.writeheader()
        writer.writerows(rows)
        writer.writerow(execution_time)

if __name__ == "__main__":
    print(f"strt: init")
    get_device_mapping()
    if None in device_serial_mapping.values():
        print(f"errr: デバイスIDが正しく取得できません。")
    else:
        print(f"cmpl: init")
        while True:
            prev_measurement_cd = ""
            prev_measurement_sl = ""
            print("\n\n")
            experiment_name = input("トンネル名称を入力してください ('cmpl'で終了): ")
            if experiment_name.lower() == "cmpl":
                break
            while True:
                print("\n\n")
                measurement_td = input("測定点TDを入力してください ('cmpl'で実験名入力に戻る): ")
                if measurement_td.lower() == "cmpl":
                    break
                # 左右の壁からの距離を入力し、中央線からの距離を計算
                while True:
                    dL_input = input(f"左壁までの距離を入力してください（m） 未入力で前回のトンネル中央からの距離[{prev_measurement_cd}]を利用: ").strip()
                    if dL_input == "":
                        measurement_cd = prev_measurement_cd
                        break
                    dR_input = input("右壁までの距離を入力してください（m）: ").strip()
                    try:
                        distance_from_left = float(dL_input)
                        distance_from_right = float(dR_input)
                        tunnel_width = distance_from_left + distance_from_right
                        measurement_cd = (distance_from_left - distance_from_right) / 2
                        break
                    except ValueError:
                        print("⚠ 入力が数値ではありません。もう一度入力してください。")
                prev_measurement_cd = measurement_cd

                measurement_sl = input(f"測定点のspringLevelからの距離を入力してください(上+,下-) 未入力で前回の値[{prev_measurement_sl}]を利用: ")
                if measurement_sl == "":
                    measurement_sl = prev_measurement_sl
                prev_measurement_sl = measurement_sl
                print(f"実験: {experiment_name}, TD: {measurement_td}, CD: {measurement_cd}, SL: {measurement_sl}")
                start = input(f"Enterで測定を開始します。(cmplで最初に戻る)")
                if start.lower() == "cmpl":
                    break
                run_tasks()
                input("Enter で次の測定へ進みます")
        print("測定を完了しました。")
    capture.release()
