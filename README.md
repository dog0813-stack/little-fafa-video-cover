# 小发发视频封面

把口播稿或主副标题做成 4500 × 8000 的高清封面，沿用小发发的演讲底图、优设标题黑和两套固定版式。

## 发给同事的一句话

> 请从 https://github.com/dog0813-stack/little-fafa-video-cover 安装「小发发视频封面」，按仓库首页配好字体和出图环境，再试做一张封面确认能用。

把这句话粘贴到自己的 Codex 即可。仓库开放匿名下载，无需 GitHub 账号或邀请。也可以将[发行页](https://github.com/dog0813-stack/little-fafa-video-cover/releases/latest)的技能 ZIP 附给 Codex，从附件安装。

## Codex 安装步骤

1. **安装技能。** 使用内置 `$skill-installer`，技能地址为 `https://github.com/dog0813-stack/little-fafa-video-cover/tree/v1.1.1/little-fafa-video-cover`。只安装该子目录。使用附件时从 ZIP 取同一子目录即可。
2. **处理已安装版本。** 若同名技能已在本机，先把该版本下载到临时目录并核对随版本提供的文件。相同就直接检查字体和试图。旧版的标准文件可备份后更新，保留用户字体、独立 Python 环境及其他本地文件。如发现用户改过的模板或脚本，先保全修改再与用户确认。
3. **准备字体。** 先检查技能的 `assets`、用户随请求提供的文件、系统字体目录，以及下载目录中名称含「优设标题黑」的文件。若字体在已下载的字体压缩包内，仅取对应 TTF。将找到的优设标题黑放入已安装技能的 `assets`，文件名可用 `优设标题黑.ttf`。这样之后出图就能直接找到字体。若确实没有，请同事登录[优设官方发布页](https://www.uisdc.com/uisdc-first-free-font)下载字体，拿到文件后接着试图。
4. **准备出图环境。** 优先使用已有的 Python 3.10+ 和 Pillow 10+。若已有合适的 Python 但缺 Pillow，可在已安装技能的 `.venv` 建独立环境并安装 `Pillow>=10`，后续出图使用该环境的 Python。
5. **试做一张。** 在临时目录写入下方的 UTF-8 JSON，用选好的 Python 执行技能内的 `scripts/render.py <文案.json> <试做封面.png>`。打开成图，核对标题和 4500 × 8000 尺寸，再告诉同事可以使用，并给出试图。若字体或仓库访问仍缺失，说明具体缺哪一步。

```json
{"layout":"opinion","top":["没有价格体系，","卖得越多","越被动"],"main":["品牌方，","别被销量骗了！"]}
```

装好后，同事直接说「做这期小发发视频封面」，再贴上口播稿或已定好的主副标题即可。

## 许可证

技能的代码和文档采用 [MIT 许可证](LICENSE)。使用模板中的演讲照片、人物肖像、现场标识或优设标题黑时，相关权利仍归各自权利人。字体可从[优设官方发布页](https://www.uisdc.com/uisdc-first-free-font)取得。
