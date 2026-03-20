/** 记录分类与子分类配置。 */
export const RECORD_CATEGORY_OPTIONS = [
  {
    key: "健康",
    label: "健康",
    icon: "🩺",
    color: "#FF8BA7",
    subTypes: ["体内驱虫", "体外驱虫", "疫苗接种", "体重记录", "异常症状"],
  },
  {
    key: "日常护理",
    label: "日常护理",
    icon: "🫧",
    color: "#F5C842",
    subTypes: ["洗澡", "美容", "剪指甲", "耳道清洁", "口腔护理"],
  },
  {
    key: "消费",
    label: "消费",
    icon: "🛍️",
    color: "#A88BFF",
    subTypes: ["主粮", "零食", "玩具", "日用品", "其他"],
  },
  {
    key: "医疗",
    label: "医疗",
    icon: "💊",
    color: "#7EC699",
    subTypes: ["门诊就诊", "住院", "用药记录", "复诊", "体检"],
  },
];

export const RECORD_CATEGORY_MAP = RECORD_CATEGORY_OPTIONS.reduce((result, item) => {
  result[item.key] = item;
  return result;
}, {});

export function getCategoryConfig(category) {
  return RECORD_CATEGORY_MAP[category] || RECORD_CATEGORY_OPTIONS[0];
}

export function getSubTypeOptions(category) {
  return getCategoryConfig(category)?.subTypes || [];
}

export function isExpenseCategory(category) {
  return category === "消费";
}

export function isWeightSubType(subType) {
  return subType === "体重记录";
}
