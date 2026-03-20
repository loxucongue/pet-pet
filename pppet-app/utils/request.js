/** 统一封装 uni-app 网络请求。 */
import { API_BASE_URL, REQUEST_TIMEOUT } from "@/config/index.js";
import { clearAll, getToken } from "@/utils/storage.js";

function buildApiUrl(url) {
  if (!url) {
    return API_BASE_URL;
  }

  if (/^https?:\/\//.test(url)) {
    return url;
  }

  return `${API_BASE_URL}${url.startsWith("/") ? url : `/${url}`}`;
}

function getAuthHeaders(extraHeaders = {}, includeJsonContentType = true) {
  const token = getToken();
  return {
    ...(includeJsonContentType ? { "Content-Type": "application/json" } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...extraHeaders,
  };
}

function resolveFileUrl(filePath) {
  if (!filePath) {
    return "";
  }

  if (/^https?:\/\//.test(filePath)) {
    return filePath;
  }

  const staticRelativePath = filePath.replace(/^uploads\//, "").replace(/^\/+/, "");
  return `${API_BASE_URL}/static/${staticRelativePath}`;
}

function handleUnauthorized() {
  clearAll();
  uni.showToast({
    title: "登录已失效，请重新登录",
    icon: "none",
  });

  setTimeout(() => {
    uni.reLaunch({
      url: "/pages/login/index",
    });
  }, 300);
}

function getResponseDetail(responseData) {
  if (!responseData || typeof responseData !== "object") {
    return "";
  }

  if (typeof responseData.detail === "string") {
    return responseData.detail;
  }

  if (typeof responseData.message === "string") {
    return responseData.message;
  }

  return "";
}

function showErrorToast(title) {
  uni.showToast({
    title,
    icon: "none",
  });
}

function request(options) {
  const {
    url,
    method = "GET",
    data,
    header,
    timeout = REQUEST_TIMEOUT,
    showLoading = true,
    loadingTitle = "加载中...",
  } = options;

  return new Promise((resolve, reject) => {
    if (showLoading) {
      uni.showLoading({
        title: loadingTitle,
        mask: true,
      });
    }

    uni.request({
      url: buildApiUrl(url),
      method,
      data,
      timeout,
      header: getAuthHeaders(header),
      success: (response) => {
        const { statusCode, data: responseData } = response;

        if (statusCode >= 200 && statusCode < 300) {
          resolve(responseData ?? null);
          return;
        }

        if (statusCode === 401) {
          handleUnauthorized();
          reject(new Error("未登录或登录已失效"));
          return;
        }

        if (statusCode === 403) {
          const message = getResponseDetail(responseData) || "权限不足";
          showErrorToast(message);
          reject(new Error(message));
          return;
        }

        if (statusCode === 422) {
          showErrorToast("请检查输入内容");
          reject(new Error("请检查输入内容"));
          return;
        }

        if (statusCode >= 500) {
          showErrorToast("服务器繁忙，请稍后重试");
          reject(new Error("服务器繁忙，请稍后重试"));
          return;
        }

        const message = getResponseDetail(responseData) || `请求失败（${statusCode}）`;
        showErrorToast(message);
        reject(new Error(message));
      },
      fail: (error) => {
        showErrorToast("网络异常，请检查网络连接");
        reject(error);
      },
      complete: () => {
        if (showLoading) {
          uni.hideLoading();
        }
      },
    });
  });
}

export const get = (url, params, options = {}) => request({ url, method: "GET", data: params, ...options });
export const post = (url, data, options = {}) => request({ url, method: "POST", data, ...options });
export const put = (url, data, options = {}) => request({ url, method: "PUT", data, ...options });
export const del = (url, data, options = {}) => request({ url, method: "DELETE", data, ...options });

const http = { get, post, put, del };

export default http;
export { buildApiUrl, getAuthHeaders, resolveFileUrl };
