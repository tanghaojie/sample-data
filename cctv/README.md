# CCTV Headquarters · 中央电视台总部大楼

根据用户提供的九张照片与结构剖面图制作的建筑可视化作品。通过已安装的 Blender MCP 在 Blender 5.2 中建模；所有几何为本次生成，没有使用第三方模型或照片贴图。建筑冠部参考高度 234 m，双塔在两个方向倾斜约 6°，上下相反转角的 L 形连接体形成真实三维闭环。细部尺寸、场地、灯光分布为照片近似，不是测绘或施工模型。

## 资产

- [GLB 在线模型](https://sample-data-jt.vercel.app/cctv/cctv-headquarters.glb)
- `cctv-headquarters.blend`：可编辑源文件，含独立预览相机与灯光。
- `build_model.py`：完整建模脚本。
- `preview-day.png`、`preview-night.png`、`preview-structure.png`：Blender 昼夜与仰视检查图。
- `placement.json`：Geo 手动加载参数。
- `validation.json`：二进制结构、包围盒、材质、面数与 SHA-256 检查。

## 造型与细节

双向倾斜塔楼、折角悬挑、贯通洞口、斜屋面、分区加密的菱形斜撑、金属边缘、独立幕墙窗格、竖梃、横梁、楼板遮挡带、悬挑底部的观察窗、九层裙房、六组屋顶卫星天线、入口雨棚、台阶与克制的景观台基。材质按类别合并为 23 个网格，约 11.25 万三角面，GLB 约 6.3 MB。

## Geo 标准与放置

已于 2026-09-28 从 GitHub 核对 [Cyber-Sight 外部模型统一渲染标准](https://github.com/tanghaojie/Cyber-Sight/blob/master/docs/platform/design/modules/geo-model-rendering.md)。

使用标准 glTF 2.0 PBR 金属度/粗糙度材质；七类 Emissive 为夜景通道，包括暖色、弱光、冷色办公室、内立面照明、悬挑底面、门厅、景观灯。Geo 根据模型所在地太阳高度自动切换，白天发光乘 0、夜间乘 1，+2° 到 -6° 平滑过渡。没有 Unlit、灯光扩展、摄像机或外部纹理依赖。仅景观灯与门厅使用 `KHR_materials_emissive_strength`。

Blender 米制 Z-up，导出标准 glTF Y-up。原点在地面附近的建筑场地中心；冠部金属收边与底端框架各有约 0.19 m 的几何厚度余量。

在 [Geo 在线工作台](https://cyber-sight-geo.vercel.app/geo.html) 中打开“数据 → 外部数据”，输入 GLB URL，WGS84 经度 `116.4577`、纬度 `39.9123`、椭球高 `0`、缩放 `1`、姿态 `0/0/0`。位置是建筑中心近似；高度 0 适用于无地形展示，朝向为展示默认值，精确配准需现场校核。仿真时间使用 UTC，例如北京正午为 `04:00 UTC`，20 时为 `12:00 UTC`。

预览图使用 Blender 光照，不能代替 Cesium 的 GPU 昼夜验收。当前浏览器安全检查因无法可靠确认 Chrome 当前网址而停止，在线模型加载与昼夜效果尚未验收。

## 参考与边界

- [OMA 项目页](https://www.oma.com/projects/cctv-headquarters)：连续三维闭环与悬挑概念。
- [Arup 项目页](https://www.arup.com/en-us/projects/china-central-television-headquarters/)：234 m 高度与倾斜双塔结构。
- [Arup Journal 2005/2](https://www.arup.com/globalassets/downloads/arup-journal/the-arup-journal-2005-issue-2.pdf)：双向 6° 倾斜、九层裙房及高空悬挑结构说明。
- 用户提供的 `imgs/` 只用作造型参考，不随资产重新发布。
