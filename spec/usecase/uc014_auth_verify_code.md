# uc014 验证码登录并创建用户

## 文档维护说明

| 字段 | 内容 |
|---|---|
| 服务名称 | AI 投资人格与持仓适配分析系统 |
| 用例编号 | uc014 |
| 用例名称 | 验证码登录并创建用户 |
| 维护人员 | Lei Jianqiu |
| 生成日期 | 2026-05-08 |
| 代码来源 | `investment_analysis/api.py`、`investment_analysis/storage.py` |

## 1. 用例概述

用户输入邮箱或手机号请求验证码，校验通过后自动创建用户并返回 Bearer token。当前本地版本直接在响应中返回 `dev_code` 便于开发调试；生产环境应接入短信或邮件服务并移除该字段。

## 2. 输入输出

### 请求验证码

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| contact | string | 是 | 邮箱或手机号 |

响应包含 `code_id`、`contact_type`、`contact`、`expires_in_seconds`、`dev_code`。

### 验证登录

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| contact | string | 是 | 邮箱或手机号 |
| code | string | 是 | 6 位验证码 |

响应包含 `user`、`token`、`expires_at`。

## 3. 主流程

```text
1. 用户提交邮箱或手机号。
2. 服务识别 contact_type，生成 6 位验证码并保存 hash。
3. 用户提交 contact 和 code。
4. 服务校验验证码未过期、未消费且 hash 匹配。
5. 若用户不存在则创建用户，若存在则更新 last_login_at。
6. 创建 session token 并返回。
```

## 4. 数据表

| 表 | 说明 |
|---|---|
| `users` | 用户主表 |
| `verification_codes` | 验证码记录 |
| `sessions` | token 会话 |

## 5. 验收标准

1. 邮箱或手机号可请求验证码。
2. 正确验证码可自动创建用户并返回 token。
3. 错误或过期验证码返回 401。
4. token 可用于 `/api/v1/me` 和登录态分析请求。
