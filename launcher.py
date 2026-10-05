import tkinter as tk
from tkinter import ttk, messagebox
import requests
import os
import sys
import threading
import subprocess
import webbrowser
import time

REPO_OWNER = "actepp"
REPO_NAME = "OGSR_Game_Editor"
API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
EXE_NAME = "OGSR_Game_Editor.exe"
VERSION_FILE = "version.txt"


def get_local_version():
    try:
        base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        version_path = os.path.join(base_dir, VERSION_FILE)
        with open(version_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return None


def get_latest_release():
    try:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "OGSR-Game-Editor-Launcher"
        }
        resp = requests.get(API_URL, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return {
            "tag": data.get("tag_name", "").lstrip("v"),
            "name": data.get("name", ""),
            "url": data.get("html_url", ""),
            "published_at": data.get("published_at", ""),
        }
    except Exception as e:
        print(f"[Launcher] Error fetching release: {e}")
        return None


def find_exe_asset(release_data):
    if not release_data:
        return None
    try:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "OGSR-Game-Editor-Launcher"
        }
        resp = requests.get(API_URL, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        for asset in data.get("assets", []):
            if asset["name"].lower() == EXE_NAME.lower():
                return {
                    "url": asset["browser_download_url"],
                    "size": asset["size"],
                }
    except Exception:
        pass
    return None


class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("OGSR Game Editor Launcher")
        self.resizable(False, False)
        self.geometry("500x320")
        self.configure(padx=20, pady=20)

        self.local_version = get_local_version()
        self.latest_info = None
        self.asset_info = None
        self.downloading = False

        self._build_ui()
        self.after(100, self._check_update)

    def _build_ui(self):
        ttk.Label(self, text="OGSR Game Editor Launcher", font=("Segoe UI", 16, "bold")).pack(pady=(0, 10))

        self.status_var = tk.StringVar(value="Проверка...")
        ttk.Label(self, textvariable=self.status_var, font=("Segoe UI", 10)).pack(pady=(0, 5))

        self.version_var = tk.StringVar(value=f"Локальная версия: {self.local_version or 'не найдена'}")
        ttk.Label(self, textvariable=self.version_var, font=("Segoe UI", 9)).pack(pady=(0, 5))

        self.latest_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.latest_var, font=("Segoe UI", 9)).pack(pady=(0, 10))

        self.progress = ttk.Progressbar(self, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=(0, 10))

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=(10, 0))

        self.btn_update = ttk.Button(btn_frame, text="Обновить", command=self._confirm_update)
        self.btn_update.pack(side=tk.LEFT, padx=5)

        self.btn_launch = ttk.Button(btn_frame, text="Запустить OGSR Editor", command=self._launch_exe)
        self.btn_launch.pack(side=tk.LEFT, padx=5)

        self.btn_open_releases = ttk.Button(btn_frame, text="Релизы на GitHub", command=self._open_releases)
        self.btn_open_releases.pack(side=tk.LEFT, padx=5)

    def _set_busy(self, busy: bool):
        self.downloading = busy
        state = tk.DISABLED if busy else tk.NORMAL
        self.btn_update.config(state=state)
        self.btn_launch.config(state=state)
        self.btn_open_releases.config(state=state)

    def _check_update(self):
        def worker():
            exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            exe_path = os.path.join(exe_dir, EXE_NAME)
            exe_exists = os.path.exists(exe_path)

            release = get_latest_release()
            asset = find_exe_asset(release)

            self.after(0, lambda: self._on_check_complete(release, asset, exe_exists))

        threading.Thread(target=worker, daemon=True).start()

    def _on_check_complete(self, release, asset, exe_exists):
        if not release:
            self.status_var.set("Не удалось проверить обновления. Проверьте интернет.")
            self.latest_var.set("")
            return

        self.latest_info = release
        self.asset_info = asset
        self.latest_var.set(f"Последняя версия: {release['tag']} ({release['published_at'][:10]})")

        if not exe_exists:
            self.status_var.set("Редактор не найден. Нажмите «Обновить» для скачивания.")
            self.btn_launch.config(state=tk.DISABLED)
            return

        if not self.local_version:
            self.status_var.set("Версия не определена. Вы можете запустить или обновить редактор.")
            return

        if self.local_version != release["tag"]:
            self.status_var.set(f"Доступно обновление: {self.local_version} → {release['tag']}")
            self.btn_update.config(state=tk.NORMAL)
        else:
            self.status_var.set("У вас установлена последняя версия.")
            self.btn_update.config(state=tk.DISABLED)

    def _confirm_update(self):
        if not self.asset_info or not self.latest_info:
            return

        answer = messagebox.askyesno(
            "Обновление",
            f"Доступна версия {self.latest_info['tag']}.\n\n"
            f"Обновить сейчас?\n"
            f"Текущая версия: {self.local_version or 'не определена'}"
        )
        if answer:
            self._start_update()

    def _kill_exe(self):
        exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        exe_path = os.path.join(exe_dir, EXE_NAME)
        if not os.path.exists(exe_path):
            return True

        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", EXE_NAME],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            time.sleep(1)
            return True
        except Exception:
            pass

        try:
            import signal
            os.kill(os.getpid(), signal.SIGTERM)
        except Exception:
            pass

        return False

    def _start_update(self):
        if not self.asset_info or not self.latest_info:
            messagebox.showinfo("Обновление", "Нет информации для обновления.")
            return

        if self.downloading:
            return

        self._set_busy(True)
        self.progress["value"] = 0
        self.status_var.set("Подготовка к обновлению...")

        def worker():
            try:
                exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
                exe_path = os.path.join(exe_dir, EXE_NAME)
                version_path = os.path.join(exe_dir, VERSION_FILE)

                self.after(0, lambda: self.status_var.set("Закрываю редактор..."))
                self._kill_exe()

                self.after(0, lambda: self.status_var.set("Удаляю старую версию..."))
                if os.path.exists(exe_path):
                    os.remove(exe_path)

                self.after(0, lambda: self.status_var.set("Скачиваю обновление..."))

                with requests.get(self.asset_info["url"], stream=True, timeout=60) as r:
                    r.raise_for_status()
                    total = int(r.headers.get("content-length", 0))
                    downloaded = 0
                    with open(exe_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                if total:
                                    pct = downloaded / total * 100
                                    self.after(0, lambda p=pct: self.progress.config(value=p))

                with open(version_path, "w", encoding="utf-8") as f:
                    f.write(self.latest_info["tag"])

                self.local_version = self.latest_info["tag"]
                self.version_var.set(f"Локальная версия: {self.local_version}")

                self.after(0, lambda: self._on_update_complete(True))
            except Exception as e:
                self.after(0, lambda: self._on_update_complete(False, str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_update_complete(self, success, error=""):
        self._set_busy(False)
        if success:
            self.status_var.set("Обновление установлено.")
            messagebox.showinfo("Готово", "Обновление установлено успешно.\n\nНажмите «Запустить», чтобы открыть редактор.")
            self.btn_launch.config(state=tk.NORMAL)
        else:
            self.status_var.set("Ошибка обновления.")
            messagebox.showerror("Ошибка", f"Не удалось обновить редактор:\n{error}")

    def _launch_exe(self):
        exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        exe_path = os.path.join(exe_dir, EXE_NAME)
        if not os.path.exists(exe_path):
            messagebox.showerror("Ошибка", f"Файл {EXE_NAME} не найден.\nСначала скачайте редактор через кнопку «Обновить».")
            return

        try:
            subprocess.Popen([exe_path], shell=False, cwd=exe_dir)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось запустить редактор:\n{e}")

    def _open_releases(self):
        url = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/releases"
        webbrowser.open(url)


if __name__ == "__main__":
    app = Launcher()
    app.mainloop()
