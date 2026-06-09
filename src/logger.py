from datetime import datetime


class LoggerAgent:
    def log(self, message: str) -> None:
        """统一记录错误/信息到控制台。"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
