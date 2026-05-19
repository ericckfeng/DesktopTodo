# macOS 執行檔

此資料夾用於存放 macOS 版本的執行檔。

## 產生方式

由於 macOS 執行檔**必須在 macOS 上打包**，請在 Mac 電腦上執行以下步驟：

### 方法一：使用打包腳本（推薦）
```bash
cd DesktopTodo
chmod +x build_macos.sh
./build_macos.sh
```

### 方法二：手動打包
```bash
pip3 install pyinstaller
pyinstaller --onefile --windowed --name DesktopTodo DesktopTodo.py
# 產出檔案位於 dist/DesktopTodo
```

打包完成後，將產出的執行檔放入此資料夾即可。
