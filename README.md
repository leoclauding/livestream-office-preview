# 直播电商办公室 · Studio / Office

可公开分享的交互式设计方案，包含可点击平面图、三条运营动线、3D 实时漫游和 Blender 渲染。

## 本地预览

在项目根目录运行 `python3 -m http.server 8000`。首页为 `index.html`，第一人称 3D 漫游为 `walk.html`，支持 `#room=studio-a` 等房间链接。

- 电脑可用 WASD 或方向键移动及转向，也可拖动鼠标观察。
- 手机在画面左侧滑动移动，在右侧滑动观察。
- 选择房间可直接到达，亦可使用楼层鸟瞰与地图。

## 设计与更新

- `design/layout.json` 保存示意平面及设备和房间安排。实际尺寸、入口和设备接口仍需现场核实。
- `blender -b -P design/render.py -- studio-a studio-b axon` 重新生成两个直播间及楼层鸟瞰。
- `blender -b -P design/export-walk.py -- arrival` 生成漫游模型、碰撞范围以及接待走廊、会客室的路径追踪效果图。
- 运行 `npm install` 与 `npm run build` 后，将新的 `assets/walk.js` 一并提交。扩展模型或材质后须重新输出模型。
- GitHub Pages 直接从 `main` 分支根目录部署。参考照片及视频保存在本地，公开文件只包含重建后的模型、设计数据和渲染图。

## 材质来源

实时和 Blender 共用按实际纹理宽度铺设的颜色、法线及粗糙度贴图。纹理与示意窗外 HDR 环境来自 Poly Haven，授权为 [CC0](https://polyhaven.com/license)。

- [Walnut Veneer](https://polyhaven.com/a/walnut_veneer)
- [Grey Cartago 03](https://polyhaven.com/a/grey_cartago_03)
- [Brown Leather](https://polyhaven.com/a/brown_leather)
- [Hotel Rooftop Balcony](https://polyhaven.com/a/hotel_rooftop_balcony)

接待区地面使用调色后的 [Marble 01](https://polyhaven.com/a/marble_01)，地毯与装饰织物使用 [Denim Fabric 05](https://polyhaven.com/a/denim_fabric_05) 的织纹。两套素材均为 CC0。
