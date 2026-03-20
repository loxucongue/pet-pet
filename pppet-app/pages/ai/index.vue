<script setup>
/** AI 主页面。 */
import { computed, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";

import EmptyState from "@/components/EmptyState.vue";
import LoadingOverlay from "@/components/LoadingOverlay.vue";
import { getHealthQuota, getHealthReportList } from "@/api/health.js";
import { getPetList } from "@/api/pet.js";
import { formatDisplayDate } from "@/utils/date.js";
import { getUserInfo } from "@/utils/storage.js";
import { resolveFileUrl } from "@/utils/request.js";

const loading = ref(false);
const petList = ref([]);
const recentReports = ref([]);
const quotaRemaining = ref(0);
const userInfo = ref(null);

const isVipUser = computed(() => {
  if (!userInfo.value || userInfo.value.user_type !== "vip") {
    return false;
  }

  if (!userInfo.value.vip_expire_time) {
    return true;
  }

  return new Date(userInfo.value.vip_expire_time).getTime() > Date.now();
});

const reportCards = computed(() =>
  recentReports.value.slice(0, 3).map((report) => {
    const indicatorList = normalizeIndicators(report.parsed_indicators_json);
    const pet = petList.value.find((item) => item.id === report.pet_id);

    return {
      ...report,
      petName: pet?.nickname || "未知宠物",
      summary:
        indicatorList.length > 0
          ? indicatorList
              .slice(0, 2)
              .map((item) => `${item.name} ${item.value}${item.unit || ""}`)
              .join(" · ")
          : report.ai_interpretation || "正在整理分析结果",
      statusMeta: getReportStatusMeta(report.status),
    };
  }),
);

const advisorCards = computed(() =>
  petList.value.map((pet, index) => ({
    ...pet,
    locked: !isVipUser.value && index > 0,
    avatarUrl: resolveFileUrl(pet.avatar),
  })),
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

function getReportStatusMeta(status) {
  const normalized = String(status || "").toLowerCase();
  if (normalized === "completed") {
    return {
      text: "已完成",
      color: "#7EC699",
      background: "rgba(126, 198, 153, 0.14)",
    };
  }

  if (normalized === "failed") {
    return {
      text: "失败",
      color: "#FF6B6B",
      background: "rgba(255, 107, 107, 0.14)",
    };
  }

  if (normalized === "processing") {
    return {
      text: "分析中",
      color: "#7DA7E7",
      background: "rgba(125, 167, 231, 0.14)",
    };
  }

  return {
    text: "待处理",
    color: "#F5C842",
    background: "rgba(245, 200, 66, 0.16)",
  };
}

async function fetchAiHomeData() {
  loading.value = true;
  try {
    userInfo.value = getUserInfo();

    const [petResponse, quotaResponse, reportResponse] = await Promise.all([
      getPetList(undefined, { showLoading: false }),
      getHealthQuota({ showLoading: false }),
      getHealthReportList(undefined, { showLoading: false }),
    ]);

    petList.value = petResponse?.items || [];
    quotaRemaining.value = Number(quotaResponse?.remaining || 0);
    recentReports.value = reportResponse?.items || [];
  } catch (error) {
    petList.value = [];
    recentReports.value = [];
    quotaRemaining.value = 0;
  } finally {
    loading.value = false;
  }
}

function openUploadPage(petId = "") {
  if (quotaRemaining.value <= 0) {
    uni.showToast({
      title: "AI 分析次数已用完",
      icon: "none",
    });
    return;
  }

  const suffix = petId ? `?petId=${petId}` : "";
  uni.navigateTo({
    url: `/pages/ai/upload-report${suffix}`,
  });
}

function openHistoryPage() {
  uni.navigateTo({
    url: "/pages/ai/report-history",
  });
}

function openReportDetail(reportId) {
  uni.navigateTo({
    url: `/pages/ai/report-detail?reportId=${reportId}`,
  });
}

function handleAdvisorClick(card) {
  if (card.locked) {
    uni.showModal({
      title: "开通会员",
      content: "普通用户可先体验 1 个 AI 宠物顾问入口，开通会员后可解锁更多宠物专属顾问。",
      confirmText: "我知道了",
      showCancel: false,
      confirmColor: "#FF8BA7",
    });
    return;
  }

  uni.showToast({
    title: `${card.nickname} 的 AI 顾问对话即将开放`,
    icon: "none",
  });
}

function openAddPetPage() {
  uni.navigateTo({
    url: "/pages/pet/add",
  });
}

onShow(() => {
  fetchAiHomeData();
});
</script>

<template>
  <view class="ai-page">
    <LoadingOverlay :visible="loading" text="正在整理 AI 分析入口..." />

    <scroll-view scroll-y class="ai-page__scroll">
      <view class="page-shell ai-page__shell">
        <view class="ai-page__hero">
          <view class="ai-page__hero-copy">
            <text class="section-title">AI 健康助手</text>
            <text class="section-caption">
              上传体检报告做通俗化解读，也可以逐步为每只宠物解锁专属 AI 顾问入口。
            </text>
          </view>
          <view class="tag-soft">剩余 {{ quotaRemaining }} 次</view>
        </view>

        <view class="card ai-page__analysis-card">
          <view class="ai-page__analysis-top">
            <view>
              <text class="ai-page__section-title">体检报告分析</text>
              <text class="section-caption">上传图片或 PDF，自动完成 OCR 识别和 AI 解读。</text>
            </view>
            <view
              class="ai-page__quota-pill"
              :class="{ 'ai-page__quota-pill--danger': quotaRemaining <= 0 }"
            >
              {{ quotaRemaining > 0 ? `还可分析 ${quotaRemaining} 次` : "次数已用完" }}
            </view>
          </view>

          <view class="ai-page__cta-row">
            <view
              class="ai-page__cta-btn"
              :class="quotaRemaining > 0 ? 'btn-primary' : 'btn-disabled'"
              @click="openUploadPage()"
            >
              上传新报告
            </view>
            <view class="btn-secondary ai-page__cta-btn" @click="openHistoryPage">查看历史</view>
          </view>

          <view v-if="reportCards.length" class="ai-page__report-list">
            <view
              v-for="report in reportCards"
              :key="report.id"
              class="ai-page__report-item"
              @click="openReportDetail(report.id)"
            >
              <view class="ai-page__report-cover">
                <image
                  v-if="report.file_type === 'image' && resolveFileUrl(report.original_file_path)"
                  :src="resolveFileUrl(report.original_file_path)"
                  mode="aspectFill"
                />
                <text v-else>{{ report.file_type === "pdf" ? "PDF" : "AI" }}</text>
              </view>
              <view class="ai-page__report-main">
                <view class="ai-page__report-head">
                  <text class="ai-page__report-title">{{ report.petName }}</text>
                  <view
                    class="ai-page__status-tag"
                    :style="{ color: report.statusMeta.color, background: report.statusMeta.background }"
                  >
                    {{ report.statusMeta.text }}
                  </view>
                </view>
                <text class="ai-page__report-date">{{ formatDisplayDate(String(report.created_at).slice(0, 10)) }}</text>
                <text class="ai-page__report-summary">{{ report.summary }}</text>
              </view>
            </view>
          </view>
          <EmptyState
            v-else
            icon="🩺"
            text="还没有体检分析记录，上传第一份报告后就能在这里回看结果。"
            button-text="去上传"
            @action="openUploadPage()"
          />
        </view>

        <view class="card">
          <view class="ai-page__section-head">
            <view>
              <text class="ai-page__section-title">AI 宠物顾问</text>
              <text class="section-caption">按宠物进入专属问答入口，后续会结合健康档案持续回答。</text>
            </view>
            <view class="tag-soft">{{ isVipUser ? "会员已解锁全部" : "普通用户体验 1 只" }}</view>
          </view>

          <view v-if="advisorCards.length" class="ai-page__advisor-list">
            <view
              v-for="card in advisorCards"
              :key="card.id"
              class="ai-page__advisor-card"
              :class="{ 'ai-page__advisor-card--locked': card.locked }"
              @click="handleAdvisorClick(card)"
            >
              <view class="ai-page__advisor-avatar">
                <image v-if="card.avatarUrl" :src="card.avatarUrl" mode="aspectFill" />
                <text v-else>🐾</text>
              </view>
              <view class="ai-page__advisor-copy">
                <view class="ai-page__advisor-head">
                  <text class="ai-page__advisor-name">{{ card.nickname }}</text>
                  <view v-if="card.locked" class="ai-page__advisor-lock">锁定</view>
                </view>
                <text class="section-caption">
                  {{ card.species }} · {{ card.breed }}
                </text>
                <text class="ai-page__advisor-desc">
                  {{ card.locked ? "开通会员后可解锁该宠物顾问对话" : "进入专属 AI 顾问入口，询问日常健康与护理问题" }}
                </text>
              </view>
            </view>
          </view>
          <EmptyState
            v-else
            icon="🐱"
            text="先添加宠物档案，AI 才能按宠物建立分析历史和顾问入口。"
            button-text="添加宠物"
            @action="openAddPetPage"
          />
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<style scoped lang="scss">
.ai-page {
  min-height: 100vh;
}

.ai-page__scroll {
  height: 100vh;
}

.ai-page__shell {
  gap: 24rpx;
  padding-bottom: 56rpx;
}

.ai-page__hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20rpx;
}

.ai-page__hero-copy {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 12rpx;
}

.ai-page__analysis-card {
  background: linear-gradient(180deg, rgba(255, 251, 252, 0.98) 0%, rgba(247, 251, 255, 0.98) 100%);
}

.ai-page__analysis-top,
.ai-page__section-head,
.ai-page__report-head,
.ai-page__advisor-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.ai-page__section-title,
.ai-page__report-title,
.ai-page__advisor-name {
  color: var(--text-primary);
  font-size: 30rpx;
  font-weight: 700;
}

.ai-page__quota-pill,
.ai-page__status-tag,
.ai-page__advisor-lock {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 48rpx;
  padding: 0 18rpx;
  border-radius: 999rpx;
  font-size: var(--font-mini);
}

.ai-page__quota-pill {
  color: var(--color-primary);
  background: rgba(255, 198, 211, 0.45);
}

.ai-page__quota-pill--danger {
  color: var(--color-danger);
  background: rgba(255, 107, 107, 0.14);
}

.ai-page__cta-row {
  display: flex;
  gap: 16rpx;
  margin-top: 24rpx;
}

.ai-page__cta-btn {
  flex: 1;
}

.ai-page__report-list,
.ai-page__advisor-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  margin-top: 24rpx;
}

.ai-page__report-item,
.ai-page__advisor-card {
  display: flex;
  gap: 18rpx;
  padding: 22rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.82);
}

.ai-page__report-cover,
.ai-page__advisor-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 96rpx;
  height: 96rpx;
  overflow: hidden;
  border-radius: 26rpx;
  color: var(--color-primary);
  font-size: 30rpx;
  background: linear-gradient(180deg, rgba(255, 198, 211, 0.75) 0%, rgba(212, 240, 247, 0.95) 100%);
}

.ai-page__report-cover image,
.ai-page__advisor-avatar image {
  width: 100%;
  height: 100%;
}

.ai-page__report-main,
.ai-page__advisor-copy {
  display: flex;
  flex: 1;
  min-width: 0;
  flex-direction: column;
  gap: 8rpx;
}

.ai-page__report-date {
  color: var(--text-secondary);
  font-size: var(--font-mini);
}

.ai-page__report-summary,
.ai-page__advisor-desc {
  color: var(--text-secondary);
  font-size: var(--font-caption);
  line-height: 1.5;
}

.ai-page__report-summary {
  display: -webkit-box;
  overflow: hidden;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.ai-page__advisor-card--locked {
  opacity: 0.82;
}

.ai-page__advisor-lock {
  color: #9b87bf;
  background: rgba(185, 166, 226, 0.18);
}
</style>
