# 无 Docker 时的测试基础设施选项

## 优先顺序

1. **Testcontainers**（有 Docker，首选）：真实镜像、方言一致、官方推荐。
2. **远程 Docker 主机**（本机无 Docker 但有 VM/服务器）：`DOCKER_HOST` 指向远程 daemon。
3. **嵌入式二进制**（MariaDB4j / embedded-redis）：真实服务器语义、无 Docker，但首次要下载二进制。
4. **内存库 + mock**（H2 MODE=MySQL / Mockito）：最快但方言/行为有差，只用于纯逻辑层。

## 远程 Docker 主机（VirtualBox 等）要点

- daemon 监听：systemd 服务默认 `-H fd://` 会覆盖 daemon.json 的 `hosts`，需 drop-in 显式指定：
  ```ini
  [Service]
  ExecStart=
  ExecStart=/usr/sbin/dockerd -H unix:///var/run/docker.sock -H tcp://<host-only-ip>:2375 --containerd=/run/containerd/containerd.sock
  ```
  daemon.json 里不要再写 `hosts`（会报"同时指定"错误）。
- **容器映射端口必须测试机可达**：NAT 只转发 SSH，随机映射端口到不了 → 用 Host-Only/桥接网卡，`DOCKER_HOST=tcp://<host-only-ip>:2375`；
- `ssh://` 方式：docker-java 默认不支持，需额外加 `docker-java-transport-ssh`，或直接用 tcp；
- 镜像源被墙：配 `registry-mirrors`（如 `https://docker.1ms.run`），首次拉取镜像。

## 判定表

| 场景 | 选择 |
|------|------|
| 验证 SQL 方言/索引/锁行为 | Testcontainers 真 MySQL |
| 验证 Redis/MQ 真实行为 | Testcontainers 容器 |
| 纯逻辑、无 SQL | Mockito 单测 |
| 本机无 Docker、有 VM | 远程 tcp daemon |
| 完全离线且要真实服务器 | 嵌入式二进制（预置下载缓存） |
