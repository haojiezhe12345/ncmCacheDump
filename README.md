# ncmCacheDump | 网易云音乐缓存转mp3/flac工具

## 功能
- 自动识别缓存文件名的歌曲ID, 向官方API查找歌曲信息, 并重命名
- 支持处理PC, 安卓的缓存文件
- 多进程并行处理, 充分利用CPU资源

## 使用

环境: `Python >= 3.9`  
模块: `requests` (安装方法: `pip install requests`)

### 1. 双击运行
在 Windows 系统下, 直接双击运行 `convert.py`, 会打开文件夹选择器, 选择网易云缓存目录即可开始转换

### 2. 命令行运行
`python convert.py <缓存文件夹路径>`  
或者将文件夹拖入 `convert.py`

即可开始转换

### 输出目录:
所有歌曲输出到工作目录下的 `output` 文件夹
