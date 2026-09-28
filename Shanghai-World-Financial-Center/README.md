# 上海环球金融中心 · Shanghai World Financial Center

根据本目录用户提供的多角度照片、立面结构图制作的建筑可视化模型。主体高 492 m、原始方形底面边长 58 m；两道弧形削切立面向顶部收成薄刃，顶部梯形洞口真实贯通。含幕墙分格、金属收边、上下观景廊、入口雨棚和简化台基。细部尺寸、弧线、灯光分布为照片近似，不是测绘或施工模型。

## Geo 加载

- GLB：[在线资产](https://sample-data-jt.vercel.app/Shanghai-World-Financial-Center/shanghai-world-financial-center.glb)
- WGS84 经度 `121.50306`，纬度 `31.23655`（公开资料建筑中心近似）。
- 椭球高 `0 m`、缩放 `1`、Heading / Pitch / Roll `0 / 0 / 0`。
- 原点在底面中心；米制 Blender Z-up，导出为标准 glTF Y-up。
- 高度 0 适合无地形展示，不代表实测地面高程；朝向为展示默认值，精确配准须另外校核。
- 在“数据 → 外部数据”输入 URL 与坐标，点击“加载 glTF / GLB”；加载成功会自动定位，也可点击资源旁的“定位”。资源仅保存在当前网页会话，刷新后需重新加载。

## 昼夜

按 [Cyber-Sight 统一渲染规范](https://github.com/tanghaojie/Cyber-Sight/blob/master/docs/platform/design/modules/geo-model-rendering.md) 制作，2026-09-28 从远端重新核对。使用标准 PBR 金属度/粗糙度；办公室、入口、观景廊、顶部轮廓使用 Emissive 夜景通道和 `KHR_materials_emissive_strength`。Geo 根据模型位置和仿真太阳高度，在 +2° 至 -6° 之间平滑切换；白天发光关闭，夜间保留资产强度比例。没有 Unlit、嵌入灯光、摄像机、Bloom 或外部贴图依赖。

`preview-day.png` 与 `preview-night.png` 是 Blender 材质检查图，不代表 Cesium 的完全一致光照。Blend 文件中的灯光和相机仅供预览，不在 GLB 内。

## 文件

- `shanghai-world-financial-center.glb`：可发布模型。
- `shanghai-world-financial-center.blend`：可编辑源文件。
- `build_model.py`：通过 Blender MCP 执行的建模脚本。
- `placement.json`：手动加载参数。
- `validation.json`：导出结构、尺寸、发光材质与 SHA-256 检查结果。
- `validate_glb.cjs`：本地结构检查工具（不是完整 Khronos 合规认证）。

## 参考

- 用户提供的 `imgs/` 照片与结构图：仅用于观察，没有作为纹理打包，也没有重新发布参考图片。
- [建筑官方网站](https://swfc-shanghai.com/about_intro.php?l=en)：492 m、101 层。
- [KPF 设计说明](https://www.kpf.com/project/shanghai-world-financial-center)：方形棱柱与两道弧面。
- [CTBUH 建筑案例](https://global.ctbuh.org/resources/papers/download/14-case-study-shanghai-world-financial-center.pdf)：58 m 方形底面与 492 m 高度。
- [公开位置参考](https://www.scraperbase.com/China/Shanghai/Shanghai_World_Financial_Center)：建筑中心近似坐标。
