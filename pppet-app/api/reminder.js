/** 提醒模块接口。 */
import { del, get, post, put } from "@/utils/request.js";

export function createReminder(data, options) {
  return post("/api/reminders", data, options);
}

export function getReminderList(params, options) {
  return get("/api/reminders", params, options);
}

export function getUpcomingReminders(params, options) {
  return get("/api/reminders/upcoming", params, options);
}

export function completeReminder(reminderId, options) {
  return post(`/api/reminders/${reminderId}/complete`, undefined, options);
}

export function updateReminder(reminderId, data, options) {
  return put(`/api/reminders/${reminderId}`, data, options);
}

export function deleteReminder(reminderId, options) {
  return del(`/api/reminders/${reminderId}`, undefined, options);
}
