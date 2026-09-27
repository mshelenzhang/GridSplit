# GridSplit

[English](README.md) · 中文

一个轻量、跨平台的 Python 图片切分工具，用于将二宫格和四宫格合成图片拆分为独立图片文件。

适用于这样的简单工作流：将一张合成图片快速拆分成多个独立画面，再继续进行编辑、发布或素材整理。

## 功能

- 支持二宫格图片横向或纵向切分
- 支持四宫格图片切分
- 支持 PNG 和 JPEG 图片
- 支持奇数尺寸图片
- 自动生成切分后的图片文件
- 每次运行生成结果清单
- 基于 Python，支持跨平台运行
- 已在 macOS 上测试
- 安装 Python 后可在 Windows 和 Linux 上运行

## 环境要求

- Python 3.10 或更高版本
- Pillow

## 安装

克隆仓库：

```bash
git clone https://github.com/mshelenzhang/GridSplit.git
cd GridSplit
