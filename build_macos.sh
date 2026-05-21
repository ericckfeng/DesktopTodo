#!/bin/bash
# ===================================================
# DesktopTodo macOS 打包腳本
# 在 macOS 上執行此腳本即可產生 DesktopTodo.app
# ===================================================

echo "📦 DesktopTodo macOS 打包工具"
echo "================================"

# 檢查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 找不到 Python3，請先安裝：https://www.python.org/downloads/"
    exit 1
fi

# 檢查/安裝 PyInstaller
if ! python3 -m PyInstaller --version &> /dev/null; then
    echo "📥 正在安裝 PyInstaller..."
    pip3 install pyinstaller
fi

# 取得腳本所在目錄
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🔨 開始打包..."
python3 -m PyInstaller \
    --onefile \
    --windowed \
    --name DesktopTodo \
    "$SCRIPT_DIR/DesktopTodo.py"

# 移動產出檔案
if [ -f "$SCRIPT_DIR/dist/DesktopTodo" ]; then
    mkdir -p "$SCRIPT_DIR/release/macos"
    mv "$SCRIPT_DIR/dist/DesktopTodo" "$SCRIPT_DIR/release/macos/DesktopTodo"
    rm -rf "$SCRIPT_DIR/build" "$SCRIPT_DIR/dist" "$SCRIPT_DIR/DesktopTodo.spec"
    echo ""
    echo "✅ 打包完成！執行檔位於："
    echo "   $SCRIPT_DIR/release/macos/DesktopTodo"
    echo ""
    echo "💡 您可以將它拖曳到 Applications 資料夾中使用。"
else
    echo "❌ 打包失敗，請檢查上方錯誤訊息。"
    exit 1
fi
