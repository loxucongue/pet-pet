<script setup>
/** 体检分析历史列表页。 */
import { computed, ref } from "vue";
import { onLoad, onShow } from "@dcloudio/uni-app";

import EmptyState from "@/components/EmptyState.vue";
import LoadingOverlay from "@/components/LoadingOverlay.vue";
import { getHealthReportList } from "@/api/health.js";
import { getPetList } from "@/api/pet.js";
import { formatDisplayDate } from "@/utils/date.js";

const loading = ref(false);
const petList = ref([]);
const reportList = ref([]);
const currentPetFilter = ref("all");
const initialPetId = ref("all");

const filterTabs = computed(() => [
  { id: "all", label: "全部宠物" },
  ...petList.value.map((item) => ({ id: String(item.id), label: item.nickname })),
]);

const historyCards = computed(() =>
  reportList.value.map((report) => {
    const pet = petList.value.find((item) => item.id === report.pet_id);
    const indicators = normalizeIndicators(report.parsed_indicators_json);

    return {
      ...report,
      petName: pet?.nickname || "未知宠物",
      statusMeta: getStatusMeta(report.status),
      summary:
        indicators.length > 0
          ? indicators
              .slice(0, 2)
              .map((item) => `${item.name} ${item.value}${item.unit || ""}`)
              .join(" · ")
          : report.ai_interpretation || "等待系统生成概要",
    };
  }),
);

function normalizeIndicators(value) {
  if (Array.isArray(value)) {
    return value;
  }

  if (value && typeof value === "object" && Array.isArray(value.items)) {
    return value.items;
  }

  return [];
}

function getStatusMeta(status) {
  const normalized = String(status || "").toLowerCase();
  if (normalized === "completed") {
    return { text: "已完成", color: "#7EC699", background: "rgba(126, 198, 153, 0.14)" };
  }
  if (normalized === "failed") {
    return { text: "失败", color: "#FF6B6B", background: "rgba(255, 107, 107, 0.14)" };
  }
  if (normalized === "processing") {
    return { text: "分析中", color: "#7DA7E7", background: "rgba(125, 167, 231, 0.14)" };
  }
  return { text: "待处理", color: "#F5C842", background: "rgba(245, 200, 66, 0.16)" };
}

function goBack() {
  if (getCurrentPages().length > 1) {
    uni.navigateBack({ delta: 1 });
    return;
  }

  uni.switchTab({
    url: "/pages/ai/index",
  });
}

async function fetchHistoryData() {
  loading.value = true;
  try {
    const petResponse = await getPetList(undefined, { showLoading: false });
    petList.value = petResponse?.items || [];

    if (currentPetFilter.value !== "all") {
      const matchedPet = petList.value.find((item) => String(item.id) === currentPetFilter.value);
      if (!matchedPet) {
        currentPetFilter.value = petList.value[0] ? String(petList.value[0].id) : "all";
      }
    } else if (initialPetId.value !== "all") {
      const matchedInitialPet = petList.value.find((item) => String(item.id) === initialPetId.value);
      if (matchedInitialPet) {
        currentPetFilter.value = String(matchedInitialPet.id);
      }
    }

    const response = await getHealthReportList(
      currentPetFilter.value === "all" ? undefined : { pet_id: Number(currentPetFilter.value) },
      { showLoading: false },
    );
    reportList.value = response?.items || [];
  } catch (error) {
    reportList.value = [];
  } finally {
    loading.value = false;
  }
}

function switchPetFilter(tabId) {
  if (currentPetFilter.value === tabId) {
    return;
  }

  currentPetFilter.value = tabId;
  fetchHistoryData();
}

function openReportDetail(reportId) {
  uni.navigateTo({
    url: `/pages/ai/report-detail?reportId=${reportId}`,
  });
}

function openUploadPage() {
  const suffix = currentPetFilter.value !== "all" ? `?petId=${currentPetFilter.value}` : "";
  uni.navigateTo({
    url: `/pages/ai/upload-report${suffix}`,
  });
}

onLoad((options) => {
  if (options?.petId) {
    initialPetId.value = String(options.petId);
    currentPetFilter.value = String(options.petId);
  }
});

onShow(() => {
  fetchHistoryData();
});
</script>

<template>
  <view class="history-page">
    <LoadingOverlay :visible="loading" text="正在加载历史分析记录..." />

    <scroll-view scroll-y class="history-page__scroll">
      <view class="page-shell history-page__shell">
        <view class="history-page__topbar">
          <view class="history-page__back" @click="goBack">‹</view>
          <view class="tag-soft">历史归档</view>
        </view>

        <view class="history-page__hero">
          <text class="section-title">历史分析记录</text>
          <text class="section-caption">
            按时间倒序查看每次体检分析的状态与指标概要，点击卡片进入详情。
          </text>
        </view>

        <view class="card">
          <text class="history-page__section-title">宠物筛选</text>
          <scroll-view scroll-x class="history-page__tabs" show-scrollbar="false">
            <view class="history-page__tabs-inner">
              <view
                v-for="tab in filterTabs"
                :key="tab.id"
                class="history-page__tab"
                :class="{ 'history-page__tab--active': currentPetFilter === tab.id }"
                @click="switchPetFilter(tab.id)"
              >
                {{ tab.label }}
              </view>
            </view>
          </scroll-view>
        </view>

        <view class="card history-page__summary-card">
          <view>
            <text class="history-page__section-title">本次筛选共 {{ historyCards.length }} 条记录</text>
            <text class="section-caption">已完成、处理中和失败记录都会保留，方便后续补查。</text>
          </view>
          <view class="btn-secondary history-page__mini-btn" @click="openUploadPage">上传新报告</view>
        </view>

        <view v-if="historyCards.length" class="history-page__list">
          <view
            v-for="report in historyCards"
            :key="report.id"
            class="card history-page__item"
            @click="openReportDetail(report.id)"
          >
            <view class="history-page__item-head">
              <view>
                <text class="history-page__item-title">{{ report.petName }}</text>
                <text class="history-page__item-date">
                  {{ formatDisplayDate(String(report.created_at).slice(0, 10)) }}
                </text>
              </view>
              <view
                class="history-page__status"
                :style="{ color: report.statusMeta.color, background: report.statusMeta.background }"
              >
                {{ report.statusMeta.text }}
              </view>
            </view>

            <text class="history-page__item-summary">{{ report.summary }}</text>
          </view>
        </view>

        <view v-else class="card">
          <EmptyState
            icon="📁"
            text="当前筛选条件下还没有分析记录，上传一份报告后这里就会出现归档。"
            button-text="去上传"
            @action="openUploadPage"
          />
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<style scoped lang="scss">
.history-page {
  min-height: 100vh;
}

.history-page__scroll {
  height: 100vh;
}

.history-page__shell {
  gap: 24rpx;
  padding-bottom: 56rpx;
}

.history-page__topbar,
.history-page__summary-card,
.history-page__item-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.history-page__back {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56rpx;
  height: 56rpx;
  border-radius: 50%;
  color: var(--text-primary);
  font-size: 40rpx;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: var(--shadow-card);
}

.history-page__hero {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.history-page__section-title,
.history-page__item-title {
  color: var(--text-primary);
  font-size: 30rpx;
  font-weight: 700;
}

.history-page__tabs {
  width: 100%;
  margin-top: 18rpx;
  white-space: nowrap;
}

.history-page__tabs-inner {
  display: inline-flex;
  gap: 14rpx;
}

.history-page__tab {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 64rpx;
  padding: 0 26rpx;
  border-radius: 999rpx;
  color: var(--text-secondary);
  font-size: var(--font-caption);
  background: #fff8fa;
}

.history-page__tab--active {
  color: var(--color-primary);
  background: rgba(255, 198, 211, 0.45);
}

.history-page__mini-btn {
  min-width: 0;
  min-height: 64rpx;
  padding: 0 24rpx;
  font-size: var(--font-caption);
}

.history-page__list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.history-page__item {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.history-page__item-date {
  display: block;
  margin-top: 8rpx;
  color: var(--text-secondary);
  font-size: var(--font-mini);
}

.history-page__status {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 48rpx;
  padding: 0 18rpx;
  border-radius: 999rpx;
  font-size: var(--font-mini);
}

.history-page__item-summary {
  color: var(--text-secondary);
  font-size: var(--font-caption);
  line-height: 1.6;
}
</style>
