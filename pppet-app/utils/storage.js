/** 本地存储工具。 */
import { TOKEN_STORAGE_KEY, USER_INFO_STORAGE_KEY } from "@/config/index.js";

export function setToken(token) {
  uni.setStorageSync(TOKEN_STORAGE_KEY, token || "");
}

export function getToken() {
  return uni.getStorageSync(TOKEN_STORAGE_KEY) || "";
}

export function removeToken() {
  uni.removeStorageSync(TOKEN_STORAGE_KEY);
}

export function setUserInfo(info) {
  uni.setStorageSync(USER_INFO_STORAGE_KEY, info || null);
}

export function getUserInfo() {
  return uni.getStorageSync(USER_INFO_STORAGE_KEY) || null;
}

export function removeUserInfo() {
  uni.removeStorageSync(USER_INFO_STORAGE_KEY);
}

export function clearAll() {
  uni.clearStorageSync();
}
