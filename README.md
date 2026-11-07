# OpenGL ES 3.1 扩展兼容增强模块

**版本：** 1.0  
**模块 ID：** `opengles_31_aep_compat`

## 功能

本模块通过 Magisk Systemless 方式进行两项配置：

1. 设置 `ro.opengles.version=196609`，使系统报告 OpenGL ES 3.1；
2. 添加 `android.hardware.opengles.aep` 功能声明，向 Android 软件包管理器声明 OpenGL ES Extension Pack（AEP）。

## 重要说明

本模块只调整系统属性和 Android 功能声明，不会替换、升级或修改 GPU/EGL/GLES 驱动，也不能凭空增加硬件或驱动实际不支持的 OpenGL 扩展，游戏或应用能否正常运行，仍取决于虚拟机图形后端和底层驱动实际提供的能力。

部分设备的 Vendor 分区布局、系统属性加载机制或权限文件路径可能不同，因此不能保证适用于所有 Android 设备及虚拟机。

## 安装

### Magisk 应用安装（推荐）

1. 在 Magisk 应用中打开“模块”；
2. 选择“从本地安装”，选中本模块 ZIP；
3. 安装完成后重启设备。

### Recovery 安装

压缩包包含 Magisk Recovery 安装入口。Recovery 安装要求设备已安装 Magisk，且 Recovery 能正确挂载并访问 `/data`。不同 Recovery 版本和设备环境可能存在兼容性差异；无法安装时请改用 Magisk 应用安装。

## 验证

重启后可执行：

```sh
su
getprop ro.opengles.version
```

如果属性设置生效，预期输出：

```text
196609
```

检查 AEP 声明文件是否存在：

```sh
ls -l /vendor/etc/permissions/android.hardware.opengles.aep.xml
```

注意：以上检查只能确认声明是否生效，不能证明 GPU 驱动真实支持全部 GLES 3.1 / AEP 扩展。应使用 GLES 能力检测工具查看实际 `GL_VERSION`、`GL_RENDERER` 和 `GL_EXTENSIONS`。

## 卸载

在 Magisk 中禁用或卸载本模块，然后重启设备。

## 构建模块（针对 Windows 环境）

### 一、准备环境

1. 安装 Python 3；
2. 安装时勾选 **Add Python to PATH**；
3. 在 PowerShell 中运行 `py -3 --version`，能显示 Python 版本即表示准备完成。

### 二、打包

在项目根目录打开 PowerShell，运行：

```powershell
.\build.ps1
```

也可以运行：

```powershell
py -3 .\scripts\build.py
```

成功后 ZIP 会生成在 release 文件夹。
