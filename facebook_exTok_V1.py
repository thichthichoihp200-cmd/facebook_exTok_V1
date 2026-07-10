import threading, time, requests, json, os, concurrent.futures, random
from colorama import Fore, Style, init

# Khởi tạo màu sắc
init(autoreset=True)

# --- CẤU HÌNH ---
CONFIG_FILE = "config_facebook_exTok.json"
BASE_URL = "https://api.extok.net/api"
print_lock = threading.Lock()

def log(msg, color=Fore.WHITE, style=Style.NORMAL):
    with print_lock:
        print(style + color + msg)

def worker(headers, account_list, min_delay, max_delay, retry_limit):
    for acc in account_list:
        uid = acc.get('fb_id')
        name = acc.get('facebook_name', 'Unknown')
        empty_count = 0
        
        while empty_count < retry_limit:
            try:
                res = requests.get(f"{BASE_URL}/facebook-jobs", params={"fb_id": uid, "limit": 1}, headers=headers, timeout=10).json()
                
                if res.get("status") == 200 and res.get("data"):
                    empty_count = 0
                    job = res["data"][0]
                    delay = random.randint(min_delay, max_delay)
                    
                    # LOG ĐẾM NGƯỢC
                    log(f"★ [Acc: {name}] Bắt đầu Job {job['id']}...", Fore.CYAN + Style.BRIGHT)
                    for i in range(delay, 0, -1):
                        print(f"{Style.BRIGHT}{Fore.CYAN}   -> [Acc: {name}] Đang làm... còn {i}s", end="\r")
                        time.sleep(1)
                    print(" " * 50, end="\r") # Xóa dòng đếm ngược sau khi xong
                    
                    resp = requests.post(f"{BASE_URL}/facebook-jobs/complete", json={"job_id": job['id'], "uid": uid, "success": True}, headers=headers).json()
                    
                    if resp.get('status') == 200:
                        coin = resp.get("coin_statistics", {}).get("current_coin", "N/A")
                        log(f"✔ [Acc: {name}] HOÀN THÀNH Job {job['id']} | Số dư: {Fore.YELLOW + Style.BRIGHT}{coin} Coin", Fore.GREEN + Style.BRIGHT)
                    else:
                        log(f"✘ [Acc: {name}] Lỗi xác nhận Job {job['id']}", Fore.RED + Style.BRIGHT)
                else:
                    empty_count += 1
                    log(f"⚠ [Acc: {name}] Không có job ({empty_count}/{retry_limit})", Fore.MAGENTA + Style.BRIGHT)
                    time.sleep(10)
            except Exception as e:
                log(f"❗ [Acc: {name}] Lỗi kết nối: {e}", Fore.RED + Style.BRIGHT)
                break
    log(f"✨ Luồng xử lý cho danh sách tài khoản đã kết thúc!", Fore.WHITE + Style.BRIGHT + Fore.MAGENTA)

def main():
    print(Fore.YELLOW + Style.BRIGHT + "=== TOOL EXTOK FACEBOOK ĐA LUỒNG RỰC RỠ ===")
    
    if not os.path.exists(CONFIG_FILE):
        token = input(Fore.GREEN + "Nhập JWT Token: " + Style.RESET_ALL).strip()
        with open(CONFIG_FILE, "w") as f: json.dump({"TOKEN": token}, f, indent=4)
        data = {"TOKEN": token}
    else:
        with open(CONFIG_FILE, "r") as f: data = json.load(f)

    headers = {"Authorization": f"Bearer {data.get('TOKEN', '')}", "Content-Type": "application/json"}
    
    try:
        accounts = requests.get(f"{BASE_URL}/facebook-account?limit=100", headers=headers, timeout=10).json().get("data", [])
    except: accounts = []

    if not accounts: 
        print(Fore.RED + Style.BRIGHT + "Lỗi tải tài khoản!")
        return

    print(Fore.WHITE + f"Tổng số tài khoản tìm thấy: {Fore.CYAN + Style.BRIGHT}{len(accounts)}")
    print(Fore.BLUE + Style.BRIGHT + "\n--- DANH SÁCH TÀI KHOẢN ---")
    for i, acc in enumerate(accounts, 1):
        print(f"{Fore.GREEN}{i}. {Fore.YELLOW}{acc.get('facebook_name', 'Unknown')}{Style.RESET_ALL} (ID: {Fore.MAGENTA}{acc.get('fb_id', 'N/A')}{Style.RESET_ALL})")
    print(Fore.BLUE + Style.BRIGHT + "---------------------------\n")

    try:
        num_threads = int(input(Fore.GREEN + "Nhập số luồng: " + Style.RESET_ALL))
        min_d = int(input(Fore.GREEN + "Delay min (s): " + Style.RESET_ALL))
        max_d = int(input(Fore.GREEN + "Delay max (s): " + Style.RESET_ALL))
        retry_limit = int(input(Fore.GREEN + "Số lần thử khi hết job: " + Style.RESET_ALL))
    except ValueError:
        print(Fore.RED + "Vui lòng nhập đúng định dạng số!")
        return

    chunks = [[] for _ in range(num_threads)]
    for i, acc in enumerate(accounts):
        chunks[i % num_threads].append(acc)

    print(Fore.YELLOW + Style.BRIGHT + "\n>>> ĐANG BẮT ĐẦU CHẠY ĐA LUỒNG VỚI ĐẾM NGƯỢC... <<<\n")
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        for chunk in chunks:
            if chunk:
                executor.submit(worker, headers, chunk, min_d, max_d, retry_limit)

if __name__ == "__main__":
    main()
