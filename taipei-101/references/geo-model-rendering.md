---
title: Geo 外部模型统一渲染标准
scope: platform
repository: Cyber-Sight
status: active
owner: project maintainers
updated: 2026-09-11
---

# Geo 外部模型统一渲染标准

## 背景与目标

普通用户提供外部 glTF/GLB URL 和 WGS84 定位后，模型自动采用系统统一的昼夜渲染。用户不选择渲染 Profile、不编写 Shader，也不逐个配置灯光。系统只负责标准与渲染，不制作、托管、上传或管理模型资产。

## 范围与非目标

本次只涉及 Platform Geo 的外部 glTF/GLB 加载、Scene 渲染能力和必要的使用说明。沿用当前会话资源和原有缩放/姿态调整。不增加资产目录、后端、数据库、场景持久化、外部模型示例、第三方依赖、实时人工光源、Bloom 或天气；不改变成都 3D Tiles 正常科技扫描和 Flight。混合资源错误隔离规则见失败模式。

## 渲染标准

- 保留模型原有基础颜色、纹理、法线、金属度、粗糙度、透明度及 Unlit 语义。
- PBR 材质中的 Emissive 统一解释为夜景通道，白天乘 0，夜间乘 1；保持资产原本的强度比例。无 Emissive 的模型只能随光照改变，不生成窗灯。
- 只使用 `viewer.clock.currentTime`。根据太阳位置与每个模型的 WGS84 位置求太阳高度；相同 UTC 的不同地区独立计算，禁止读取电脑本地小时或按相机位置判断建筑昼夜。
- 高度角大于等于 +2° 为白天，小于等于 -6° 为夜间，中间采用 smoothstep 平滑过渡。每模型环境光贡献从白天原始值平滑降为夜间的 0.2 倍；太阳直射在地平线附近衰减，太阳落到地平线以下后不从地下照亮模型。
- 场景默认太阳照明开启、阴影关闭。现有地球光照开关明确称为“地球光照”，只控制地球表面；模型昼夜始终跟随仿真时间。太阳图形显隐不代表关闭光源。阴影遵循现有 Scene ShadowMap 开关。
- 统一按模型变换矩阵的地固坐标原点定位；输入界面标注 WGS84 经纬度和椭球高（米）。无法确定有效地理位置时保留原始渲染并显示说明，不假定成都或地心是有效地点。

## 职责与公共接口

能力仍属于 `apps/frontend/src/platform/modules/geo/`，不新增跨 Platform 模块的公共 API。

- Time 拥有 Clock 控制，不导入模型渲染实现。
- Scene 创建并释放统一渲染管理器，使用 `plugins/scene/scene.capabilities.ts` 发布 `scene.modelRendering`。Data 显式依赖 Scene，消费 capability，不导入 Scene controller。
- `tools/scene/model-rendering.ts` 暴露 `createGeoModelRenderingManager(viewer)`、`GeoModelRenderingManager`、`GeoModelRenderingRegistration`。接口为 `register(model)` 返回带 `update()` 和 `dispose()` 的注册句柄；管理器提供 `dispose()`。这些是 Geo 内部纯工具接口，不依赖 Vue/插件/UI，也不反向依赖 Data。
- Data 负责下载、变换、ready、定位和 Primitive 生命周期，向纯工具注入管理器；等待原始模型 ready 后、首次可见绘制前注册，在模型矩阵更新后调用句柄 `update()`，在 Primitive 销毁前注销。Cesium 1.144 的 ready 帧尚不绘制模型，此顺序避免新 Shader 阻断 ready。核心 API 原始渲染兼容路径仅供独立工具调用；工作台默认注入统一管理器。
- 资源快照可以保存可读渲染说明，不保存 Cesium 重资源。材质信息只通过公开加载回调检查，不访问私有字段；无可靠证据时保持未知，不宣称已发现缺失材质。

## 数据流与性能

URL/定位 → Data 创建 Model 并等待原始模型 ready → Scene 渲染管理器登记 → 时间和位置求太阳高度 → 更新材质 uniform、环境光及模型直射光 → 自动定位。

管理器只建立一套共享时间/场景更新监听，模型数量增长不增加定时器或监听器。首次注册、时间变化（包括暂停拖动）、位置变化均立即求值。相同时间及配置跳过重复计算，不创建额外 Clock、requestAnimationFrame 或空闲重绘循环。Shader 保持实例稳定，只更新 uniform。

## 失败模式与兼容性

- glTF/GLB 和引用纹理需由浏览器可访问，跨域、下载失败和不支持的必要扩展保留现有可诊断错误路径。
- 无发光材质和 Unlit 是能力边界，不应阻止正常显示；提示准确描述检查结果。混合材质按 primitive 保留 Unlit 原始语义。
- 加载失败、取消、移除、清空、页面卸载必须清理注册、监听器和 Shader。注销恢复原有模型 Shader/IBL/光色状态，不销毁不属于本系统的资源。
- 原始模型等待 ready 期间的场景渲染异常终止等待并清理，错误只说明场景失败，不断言模型是故障源。页面卸载也终止尚未完成的 ready 等待。
- Cesium 的 `scene.renderError` 不提供资源归属。存在待就绪或已加载模型时，不自动回退所有模型或清除 3D Tiles 科技扫描；展示场景级故障提示，维护者可移除最近添加的模型后重试。没有模型时保留既有 Tileset 回退行为。因此混合资源场景的自动回退受到限制，不承诺自动定位或恢复任意 GPU 故障。
- 注册时同步异常恢复原始渲染；ready 后异步 Shader/WebGL 失败不能等同于该同步回退，需要人工检查。真实浏览器视觉与故障恢复仍需验收，不得将静态通过描述为 GPU 验收。
- Cesium 固定为 1.144.0；升级时复核 CustomShader 材质阶段、Unlit 宏和公开回调。统一标准会使已有外部 PBR 模型的 Emissive 白天关闭，资产提供方应遵守夜景通道约定。

## 验证策略

执行格式、类型检查、lint、架构边界、生产构建、文档归档门禁及 diff 审查；按仓库约定不新增或运行前端自动化/浏览器测试。

维护者人工验收：

1. 仅填 URL 和定位可加载并自动取景；缩放/姿态为可选调整，界面无 Profile 和夜景参数。
2. 成都正午/夜间及日落渐变：PBR 明暗和 Emissive 同步；UTC+8 换算正确，时间轴仍明确 UTC。
3. 暂停后拖动、播放、倍速、回到现在及修改位置立即生效；不同经度模型显示各自昼夜，跨日和极昼极夜不使用固定小时分支。
4. 无 Emissive、Unlit、混合材质、透明材质正确显示，提示与实际材质一致。
5. 显隐、移除、失败、退出重入无重复监听器或资源残留；暂停时空闲渲染不持续增长。
6. 地球光照、太阳显隐、阴影开关语义清晰；正常 3D Tiles 科技扫描和 Flight 保持原行为。混合模型/瓦片的场景渲染错误不误清除其他资源样式，按提示人工恢复。

## 关联记录

- [决策](../../decisions/ADR-20260911-geo-external-model-rendering.md)
- [实施计划](../../archive/plans/2026-09-11-geo-external-model-rendering.md)
- [协作记录](../../archive/ai-logs/feat/2026/09/2026-09-11-geo-external-model-rendering.md)
