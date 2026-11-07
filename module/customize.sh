#!/system/bin/sh

# 使用 Magisk 默认解压流程，将模块文件安装到模块目录。
SKIPUNZIP=0

# 输出模块安装信息。
ui_print "- 正在安装 OpenGL ES 3.1 扩展兼容增强..."
ui_print " "

# 读取当前系统报告的 OpenGL ES 版本。
GLES_VER="$(getprop ro.opengles.version 2>/dev/null)"
ui_print "[*] 当前系统报告的 GLES 版本属性：${GLES_VER:-未读取到}"
ui_print "[*] OpenGL ES 3.1 对应的属性值：196609"

# 检查 AEP 功能声明文件是否已解压到模块目录。
AEP_XML="$MODPATH/system/vendor/etc/permissions/android.hardware.opengles.aep.xml"
if [ -f "$AEP_XML" ]; then
    ui_print "[*] AEP 功能声明文件检查通过。"
else
    ui_print "[!] 未找到 AEP 功能声明文件，请检查模块压缩包。"
fi

ui_print " "
ui_print "[说明] 本模块会调整 OpenGL ES 版本声明，并添加 AEP 功能标识。"
ui_print "[说明] 本模块不会修改 GPU 驱动，也不能补齐驱动缺失的真实扩展。"
ui_print "[提示] 安装完成后请重启设备。"
