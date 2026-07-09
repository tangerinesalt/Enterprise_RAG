## ADDED Requirements

### Requirement: Storage operations SHALL remain within declared root directories

系统 SHALL 在执行知识库、会话、聊天文件相关的读写、删除、列举和自动创建操作前，将用户输入解析为受限路径，并验证最终路径仍位于对应根目录内。

#### Scenario: Reject traversal outside KB files root
- **WHEN** 客户端或 CLI 传入会使目标文件规范化后落到 `kb/<name>/files/` 之外的文件名或目标路径
- **THEN** 系统拒绝该操作
- **THEN** 不创建、覆盖、读取或删除任何根目录外文件

#### Scenario: Reject traversal outside session chats root
- **WHEN** 客户端传入会使 `chat_file` 规范化后落到 `sessions/<name>/chats/` 之外的值
- **THEN** 系统拒绝该操作
- **THEN** 不读取、删除或写入任何根目录外聊天文件

### Requirement: Session and knowledge base identifiers SHALL be path-safe

系统 SHALL 只接受满足以下规则的会话名与知识库名：去除首尾空白后仍非空；不包含路径分隔符、绝对路径语义、盘符前缀、UNC 前缀和 `.` / `..` 路径段；不包含尾随空格或点；不命中 Windows 保留设备名；不包含控制字符。

#### Scenario: Reject invalid knowledge base name
- **WHEN** 客户端提交包含 `/`、`\`、`..` 或绝对路径语义的知识库名
- **THEN** 系统拒绝创建、读取、删除或绑定该知识库
- **THEN** 返回稳定的非法输入错误

#### Scenario: Reject invalid session name
- **WHEN** 客户端提交包含 `/`、`\`、`..` 或绝对路径语义的会话名
- **THEN** 系统拒绝创建、读取、删除或更新该会话
- **THEN** 返回稳定的非法输入错误

#### Scenario: Reject Windows-reserved or trimmed-empty identifier
- **WHEN** 客户端提交去除首尾空白后为空的名称，或提交 `CON`、`NUL`、`COM1` 等 Windows 保留设备名
- **THEN** 系统拒绝该名称
- **THEN** 不创建任何知识库或会话目录

### Requirement: Web-uploaded filenames SHALL be treated as leaf filenames

系统 SHALL 将 Web 上传场景中的客户端文件名先裁剪为叶子文件名，再仅基于该叶子文件名决定是否接受文件；如果裁剪后的叶子文件名本身不合法，则 SHALL 拒绝该文件。

#### Scenario: Upload strips client path components
- **WHEN** 客户端上传文件且 `filename` 含有目录分隔信息
- **THEN** 系统只使用该文件的叶子文件名参与落盘
- **THEN** 最终文件仍被限制在目标知识库的文件根目录内

#### Scenario: Upload rejects invalid leaf filename
- **WHEN** 客户端文件名在裁剪为叶子文件名后仍为非法名称，例如空白名、尾随点名或 Windows 保留设备名
- **THEN** 系统拒绝该文件
- **THEN** 不会创建目标文件
