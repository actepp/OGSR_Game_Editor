import tkinter as tk
from tkinter import ttk, messagebox
import requests
import os
import sys
import threading
import subprocess
import webbrowser
from urllib.parse import urlparse

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
        resp = requests.get(API_URL, timeout=10)
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

        self.btn_update = ttk.Button(btn_frame, text="Обновить", command=self._start_update)
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

            print(f"[Launcher] exe_dir: {exe_dir}")
            print(f"[Launcher] exe_path: {exe_path}")
            print(f"[Launcher] exe_exists: {exe_exists}")

            release = get_latest_release()
            print(f"[Launcher] release: {release}")

            asset = find_exe_asset(release)
            print(f"[Launcher] asset: {asset}")

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
            self.status_var.set("Редактор не найден. Скачиваю последнюю версию...")
            self._start_update()
            return

        if not self.local_version:
            self.status_var.set("Версия не определена. Вы можете запустить или обновить редактор.")
            return

        if self.local_version != release["tag"]:
            self.status_var.set(f"Доступно обновление: {self.local_version} → {release['tag']}")
        else:
            self.status_var.set("У вас установлена последняя версия.")

    def _start_update(self):
        if not self.asset_info or not self.latest_info:
            messagebox.showinfo("Обновление", "Нет информации для обновления.")
            return

        if self.downloading:
            return

        self._set_busy(True)
        self.progress["value"] = 0
        self.status_var.set("Скачивание обновления...")

        def worker():
            try:
                exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
                exe_path = os.path.join(exe_dir, EXE_NAME)
                new_exe_path = exe_path + ".new"

                with requests.get(self.asset_info["url"], stream=True, timeout=60) as r:
                    r.raise_for_status()
                    total = int(r.headers.get("content-length", 0))
                    downloaded = 0
                    with open(new_exe_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                if total:
                                    pct = downloaded / total * 100
                                    self.after(0, lambda p=pct: self.progress.config(value=p))

                self.after(0, lambda: self._on_update_complete(True))
            except Exception as e:
                self.after(0, lambda: self._on_update_complete(False, str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_update_complete(self, success, error=""):
        self._set_busy(False)
        if success:
            exe_path = os.path.join(os.path.dirname(sys.executable), EXE_NAME)
            if not os.path.exists(exe_path):
                self.status_var.set("Редактор скачан. Нажмите «Запустить».")
                messagebox.showinfo("Готово", "Редактор скачан успешно.\n\nНажмите «Запустить», чтобы открыть его.")
            else:
                self.status_var.set("Обновление скачано. Оно будет установлено после перезапуска.")
                messagebox.showinfo("Обновление", "Обновление скачано успешно.\n\n"
                                                  "Нажмите «Запустить», чтобы запустить редактор.\n"
                                                  "После его закрытия обновление будет установлено автоматически.")
        else:
            self.status_var.set("Ошибка скачивания обновления.")
            messagebox.showerror("Ошибка", f"Не удалось скачать обновление:\n{error}")

    def _launch_exe(self):
        exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        exe_path = os.path.join(exe_dir, EXE_NAME)
        if not os.path.exists(exe_path):
            messagebox.showerror("Ошибка", f"Файл {EXE_NAME} не найден.\nСначала скачайте редактор через кнопку «Обновить».")
            return

        new_exe_path = exe_path + ".new"
        if os.path.exists(new_exe_path):
            bat_path = os.path.join(exe_dir, "update.bat")
            with open(bat_path, "w", encoding="utf-8") as f:
                f.write("@echo off\n")
                f.write("timeout /t 3 /nobreak >nul\n")
                f.write(f"move /Y \"{new_exe_path}\" \"{exe_path}\"\n")
                f.write(f"del /F /Q \"%~f0\"\n")

            try:
                subprocess.Popen([bat_path], shell=False, cwd=exe_dir)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось запустить обновление:\n{e}")
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
