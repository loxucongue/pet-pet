/** 日期处理工具。 */

export function padNumber(value) {
  return String(value).padStart(2, "0");
}

export function formatDate(date) {
  return `${date.getFullYear()}-${padNumber(date.getMonth() + 1)}-${padNumber(date.getDate())}`;
}

export function formatMonth(date) {
  return `${date.getFullYear()}-${padNumber(date.getMonth() + 1)}`;
}

export function getToday() {
  return formatDate(new Date());
}

export function getCurrentYear() {
  return new Date().getFullYear();
}

export function getMonthRange(monthText) {
  const [year, month] = monthText.split("-").map(Number);
  const first = new Date(year, month - 1, 1);
  const last = new Date(year, month, 0);

  return {
    start: formatDate(first),
    end: formatDate(last),
  };
}

export function shiftMonth(monthText, offset) {
  const [year, month] = monthText.split("-").map(Number);
  const nextDate = new Date(year, month - 1 + offset, 1);
  return formatMonth(nextDate);
}

export function formatDisplayDate(dateText) {
  if (!dateText) {
    return "";
  }

  const [year, month, day] = dateText.split("-");
  return `${year}年${Number(month)}月${Number(day)}日`;
}

export function formatDisplayMonth(monthText) {
  if (!monthText) {
    return "";
  }

  const [year, month] = monthText.split("-");
  return `${year}年${Number(month)}月`;
}
