/** 体检分析模块接口。 */
import { get, post, put } from "@/utils/request.js";

function withLongTimeout(options = {}) {
  return {
    timeout: 90000,
    ...options,
  };
}

export function getHealthQuota(options) {
  return get("/api/health/quota", undefined, options);
}

export function analyzeHealthReport(data, options) {
  return post("/api/health/analyze", data, withLongTimeout(options));
}

export function getHealthReportList(params, options) {
  return get("/api/health/reports", params, options);
}

export function getHealthReportDetail(reportId, options) {
  return get(`/api/health/reports/${reportId}`, undefined, options);
}

export function updateHealthReportIndicators(reportId, data, options) {
  return put(`/api/health/reports/${reportId}/indicators`, data, options);
}

export function reanalyzeHealthReport(reportId, options) {
  return post(`/api/health/reports/${reportId}/reanalyze`, undefined, withLongTimeout(options));
}
