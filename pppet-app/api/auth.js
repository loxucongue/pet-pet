/** 认证接口。 */
import { post } from "@/utils/request.js";

export function mockLogin(nickname, avatarUrl = "") {
  return post("/api/auth/mock-login", {
    nickname,
    avatar_url: avatarUrl || null,
  });
}

export function wxLogin(code) {
  return post("/api/auth/wx-login", {
    code,
  });
}
