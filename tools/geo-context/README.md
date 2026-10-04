# 开放建筑数据街区生成器

为 Cyber Sight 的全球地标录屏生成可复用周边。工具在资产制作侧运行，Sight 读取静态场景；不需要地图 API key、业务后台或浏览器实时生成。

## 完整生成流程

需要 Python 3.12+。几何、UV、法线、切线和 glTF 导出由脚本直接完成，运行不依赖 Blender；可以在 Blender 导入 GLB 检查资产。共享 PBR 图像由 Pillow/NumPy 生成，没有第三方照片或固定太阳阴影。

```bash
python -m venv .venv
.venv/bin/pip install -r tools/geo-context/requirements.txt
.venv/bin/python tools/geo-context/fetch_context.py --config tools/geo-context/configs/taipei-101.json --output downloads/taipei-101
.venv/bin/python tools/geo-context/build_context.py --config tools/geo-context/configs/taipei-101.json --buildings downloads/taipei-101/building.geojson --parts downloads/taipei-101/building_part.geojson --output geo-context/taipei-101-v2
.venv/bin/python tools/geo-context/validate_context.py geo-context/taipei-101-v2
.venv/bin/python -m unittest discover -s tools/geo-context -p 'test_*.py' -v
```

Windows 使用 `.venv\Scripts\python.exe` 和 `.venv\Scripts\pip.exe`。如网络使用 HTTPS 代理，下载脚本读取标准代理配置，不保存或输出代理凭据。

输出目录必须为空，使用新版本目录，避免覆盖已发布资产。已发布 `sources/*.geojson.gz` 带数据版本，可直接用于重复生成。原始官方 CLI 下载文件也可使用，但需保留其 `.state` 发布版本记录。

## 新增地标

复制配置并修改 id、名称、模型 URL、WGS84 锚点与半径。先核对下载数据中的目标 ID，填写 exclude_building_ids；可选 exclude_polygon 使用 WGS84 GeoJSON Polygon，覆盖精细模型替换的实际占地，不能使用高塔包围球。height_overrides_m 按要素 ID 提供经核对的离地顶部高度。

默认半径与网格支持 50–20000 米、100–2000 米。查询跨日期变更线时拆分，几何使用局部 AEQD 和每瓦片 ECEF/ENU 锚点。生成输出只表示选中区域，不承诺任意城市完整覆盖。

生成 scene.json 包含版本、名称、主体、区域瓦片、地理锚点与署名。Sight → 数据 → 外部数据 → 地标与周边，填写 scene.json URL 或使用台北示例。主体仍询问使用 GLB/场景输入坐标；位置、高度、缩放、姿态或地形不匹配时隐藏周边并提示。

## 第一版范围

- Overture 固定发布版本，含其已融合的 OSM 轮廓、楼层、建筑分段与可用材料属性；不再重复追加相同 OSM 建筑。
- 外墙、屋顶、庭院孔洞、悬空底面、PBR/米制 UV、法线/切线、固定种子变化与窗灯纹理。
- 400 米起点空间网格，完整/简化两级几何和 3D Tiles 1.1，主体与分段在生成阶段排除。
- 缺失高度按楼层/类型估算并统计；OSM 建筑分段的 height 是离地顶部，不能再加 min_height。未知非平顶屋面简化为平顶。
- 共享玻璃办公、住宅、混凝土、砖墙、商业及屋顶材质；静态窗灯分布由 Sight 唯一时钟及太阳高度调亮。
- 当前地面为 WGS84 椭球体。真实地形、道路/交通、树木准确位置、真实人工受光和城市反射为后续。

## 验证

Python 验证覆盖所有瓦片：二进制结构、引用、法线/切线、三角形朝向、孔洞、排除主体、ENU 右手变换与包围体。Khronos 验证另需 `gltf-validator`：

```bash
npm install --prefix /tmp/geo-gltf-check gltf-validator
NODE_PATH=/tmp/geo-gltf-check/node_modules node tools/geo-context/validate-gltf.cjs geo-context/taipei-101-v2
```

这属于资产检查，不执行 Sight 前端或浏览器自动化测试。最终环绕、昼夜、三档质量与录屏效果由维护者在 Sight 人工验收。

## 数据许可

源建筑主题和提取结果按 ODbL-1.0 使用，公开可复现源数据、配置和版本。署名 OpenStreetMap contributors、Overture Maps Foundation，以及实际使用的附加来源。台北提取包含 Qian Shi et al. 的 East Asian Buildings（CC BY 4.0，doi:10.5281/zenodo.8174931）。详见 [Overture attribution](https://docs.overturemaps.org/attribution/) 和 [OSM copyright](https://www.openstreetmap.org/copyright)。

本目录原创脚本及原创程序化纹理采用 MIT，数据与生成几何的来源义务不由代码许可替代。场景 metadata 记录来源、版本、估算统计与限制；录屏保留数据署名。
