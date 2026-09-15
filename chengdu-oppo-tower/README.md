# 成都 OPPO 大厦 · 简化模型

按本目录六张照片制作的基础轮廓模型：错层竖向体块、蓝灰玻璃幕墙、银色竖梃、简化 OPPO 标志与暖色办公窗光。不是测绘或施工模型；体块宽深、局部高度、窗灯分布为照片近似。

## 在线加载

- URL: https://sample-data-jt.vercel.app/chengdu-oppo-tower/chengdu-oppo-tower.glb
- WGS84 经度：104.07807
- WGS84 纬度：30.51732
- 椭球高：0 m（无地形模式贴椭球面展示；不是实测地面高程）
- 缩放：1
- Heading / Pitch / Roll：0 / 0 / 0 度；南北长轴已在模型中旋转。
- 建筑高度：206 m；Blender 米制、Z-up，导出标准 glTF Y-up。
- 使用真实地形时，需要按地形或测绘资料调整椭球高。

GLB extras 保存定位提示，但 Geo 不会自动读取这些值，请在外部数据面板输入。Geo 当前资源仅保存在会话内，刷新后需要重新加载。

## 昼夜规范

遵循 Cyber-Sight `docs/platform/design/modules/geo-model-rendering.md`（2026-09-15 从 GitHub 核对）。标准 PBR 基础颜色、金属度和粗糙度；窗灯发光强度 2.8，标志 2.0，使用 `KHR_materials_emissive_strength`。没有 Unlit、导出灯光或摄像机，没有外部贴图依赖。白天由 Geo 关闭发光，夜间由 Geo 开启，过渡取决于仿真时间和太阳高度。

## 文件

- `chengdu-oppo-tower.glb`：在线资产，约 2.1 MB。
- `chengdu-oppo-tower.blend`：可编辑源文件。
- `build_model.py`：通过 Blender MCP 在 Blender 中运行的生成脚本。
- `placement.json`：加载参数与来源。

## 来源

- 坐标与南北方向：[OpenStreetMap way 1212154634](https://www.openstreetmap.org/way/1212154634)，© OpenStreetMap contributors，ODbL。坐标为公开建筑轮廓中心近似。
- 高度 206 米：[The Skyscraper Center](https://www.skyscrapercenter.com/building/oppo-technology-and-research-center/30287)。
- 外观：用户提供的 1.jpg 至 6.jpg；没有将照片作为模型纹理。
