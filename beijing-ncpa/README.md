# 北京国家大剧院 · National Centre for the Performing Arts

使用 Blender 5.2.1 LTS 制作的原创建筑可视化作品，可编辑源工程与 Cyber-Sight Geo GLB 同时交付。主要表现钛金属半椭球壳体、渐开式玻璃帷幕、内侧双层钢肋、金色歌剧院包覆、环廊、分区镜面水池、水下入馆通道、下沉阶梯、铺装、园林及灯具。

## 资料与精度

主体东西 212.2 m、南北 143.64 m、顶部 46.285 m。尺寸采用公开施工介绍口径；部分介绍为 46.68 m。资料包括建筑师提供的实景与带比例尺、北向的总平面，《Architectural Record》2008.07 的总平面与厅堂剖面，以及蓬皮杜中心收藏的竞赛剖面。完整出处、访问限制与本地文件对应见 [参考资料目录](references/README.md)。

这是照片和公开图纸重建，不是实测／BIM。玻璃边界、板块分格、内厅可见体量、入口深度和景观为视觉估算。约 19,316 块钛板、1,288 块玻璃是本模型分格数量，不宣称为逐块竣工复刻。水池采用图纸比例重建的圆角矩形，理论净水域约 35,350 m²，贴近公开 35,500 m²；模型分区墙和水下通道会略减少可见水域。主体外壳保持无地上常规门洞的特征。

未重建邻近人民大会堂、完整城市街区、地下三层设施、座椅或全部机电。内厅用于玻璃遮挡和夜景层次。夜景参照暖色内厅与钛壳星点照片，是静态建筑展示方案，不复刻某场活动灯光。

## 运行资产

| 质量 | 文件 | 用途 |
| --- | --- | --- |
| 主版本 | `beijing-ncpa.glb` | 精细钛板、扣件、玻璃钢架和景观；适合近景与录屏 |
| 平衡 | `beijing-ncpa-balanced.glb` | 简化树冠与细构件，保留主体分格 |
| 兼容 | `beijing-ncpa-compatible.glb` | 连续钛壳、较少内侧钢架与简化树冠，保留身份、尺度及夜景 |

三者共享同一坐标、朝向和尺寸。Scene 质量切换不会自动更换 GLB URL，按需要手动选择资产。预算统计、文件哈希与 Khronos 结果见 `validation.json`；主版本约 52 万面，场地与细密结构使其高于单体建议起点，平衡／兼容版供较弱设备选择，不承诺 FPS。

## 地理参考和 Geo 使用

唯一 `GEO_ROOT.extras` 内嵌规范 WGS84 字段：116.38355° E、39.90334° N，approximate，来源为 OpenStreetMap 建筑中心并交叉核对档案馆 GPS。绝对椭球高未知，未写入 `ellipsoid_height_m`；选择模型坐标时由 Geo 按当前地形采样。`height_m=46.285` 仅为建筑尺寸。

模型采用米制，地面／水线基准为主体平面中心 z=0，入口阶梯低至约 -4.9 m。Blender 工作坐标 X=东、Y=北；唯一根变换完成朝向校准，导出后 glTF +Z=东、+X=北、+Y=上。加载 scale=1、heading=pitch=roll=0，北侧入口向北。`placement.json` 是说明与手工输入记录，Geo 不会自动请求它。无地形展示可显式输入高度 0，此值不代表实测海拔或椭球高。

在 [Cyber-Sight Geo](https://cyber-sight-geo.vercel.app/geo.html) 的 数据 → 外部数据 输入 [主版本 GLB URL](https://sample-data-jt.vercel.app/beijing-ncpa/beijing-ncpa.glb)，加载并选择模型坐标。底图和地形衔接、入口地下区域及北向须结合实际场景人工核对。

## 材质与昼夜

标准 glTF metallic-roughness PBR。裸钛使用 metallic=1 和拉丝粗糙度；玻璃为 metallic=0，独立 alpha BLEND、轻微板间变化和 clearcoat，水面为介电材质。透明玻璃是便于当前引擎显示的近似，未依赖不支持的 Transmission／Volume。石材、木材、草地含原创 256 px 平铺颜色、粗糙度与 OpenGL +Y 法线图，石材以 1 m 模块 UV 重复；树冠用空间形态和多种颜色。所有引用纹理的 primitive 具有 UV，法线贴图网格保留匹配切线。19 张图像自包含于 GLB，纹理源在 `textures/` 及 `.blend` 内。

屋面星点、歌剧院金色背光、环廊线灯与到达区灯具为四组独立 Emissive 夜景通道，白天由 Geo 关闭，日落渐变，夜间开启。没有资产内置时钟、动态随机灯光或导出的灯光、相机、摄影棚地面。Cycles 展示灯会产生真实受光和水面倒影；Geo 的 Emissive 不等同于照亮周围地面，动态环境反射也不自动含本建筑或邻楼。两者的视觉验收记录分开。

规范基准：Cyber-Sight 远端 `6262b51b890748eecdba4bbca46343d08a97db6c`，制作与渲染标准均为 2026-10-04 版本，见参考目录链接。

## 文件与复现

- `beijing-ncpa.blend`：可编辑分组、纹理和摄影机／灯光。
- `build_model.py`：确定性原创建模及主资产导出。
- `export_variants.py`：从同一源工程生成两个轻量版本。
- `finalize_glb.py`：只移除未使用的切线流并重排内嵌 buffer；不改变材质和外观。
- `render_preview.py`、`render_all.py`：Cycles 昼、夜、日落、鸟瞰、材质近景、入口与正立面图。
- `validate_glb.cjs`、`*-khronos.json`、`validation.json`：官方验证、尺寸、纹理、朝向、定位和依赖检查。
- `delivery-verification.json`：Git／Vercel／远端字节验证，与浏览器记录独立。

在 Blender 后台执行 `--python build_model.py`，再执行 `--python export_variants.py`。安装官方 `gltf-validator` npm 包后执行 `node validate_glb.cjs beijing-ncpa.glb beijing-ncpa-balanced.glb beijing-ncpa-compatible.glb`。执行 `--python render_all.py` 输出所有展示图。原始照片与图纸仅本地保存，未嵌入原创模型。

发布和浏览器验收正在进行；完成状态以 `delivery-verification.json` 和截图为准。
