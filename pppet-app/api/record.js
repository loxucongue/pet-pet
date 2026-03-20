/** 记录模块接口。 */
import { del, get, post, put } from "@/utils/request.js";

export function getRecordList(params, options) {
  return get("/api/records", params, options);
}

export function getRecordDetail(recordId, options) {
  return get(`/api/records/${recordId}`, undefined, options);
}

export function createRecord(data, options) {
  return post("/api/records", data, options);
}

export function updateRecord(recordId, data, options) {
  return put(`/api/records/${recordId}`, data, options);
}

export function deleteRecord(recordId, options) {
  return del(`/api/records/${recordId}`, undefined, options);
}

export function getWeightTrend(params, options) {
  return get("/api/records/stats/weight", params, options);
}

export function getExpenseStats(params, options) {
  return get("/api/records/stats/expense", params, options);
}
