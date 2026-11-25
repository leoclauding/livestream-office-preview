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
- `blender -b -P design/export-walk.py -- arrival` 生成漫游模型、碰撞范围和接待走廊渲染。
- 运行 `npm install` 与 `npm run build` 后，将新的 `assets/walk.js` 一并提交。扩展模型或材质后须重新输出模型。
- GitHub Pages 直接从 `main` 分支根目录部署。参考照片及视频保存在本地，公开文件只包含重建后的模型、设计数据和渲染图。
