<script setup>
/** AI 模块主页。 */
import { computed, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";

import EmptyState from "@/components/EmptyState.vue";
import LoadingOverlay from "@/components/LoadingOverlay.vue";
import { getChatPermissions } from "@/api/chat.js";
import { getHealthQuota, getHealthReportList } from "@/api/health.js";
import { getPetList } from "@/api/pet.js";
import { formatDisplayDate } from "@/utils/date.js";
import { resolveFileUrl } from "@/utils/request.js";

const loading = ref(false);
const petList = ref([]);
const recentReports = ref([]);
const quotaRemaining = ref(0);
const chatPermissionList = ref([]);
const maxChatPets = ref(1);
const usedChatPets = ref(0);

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
  chatPermissionList.value.map((item) => ({
    ...item,
    avatarUrl: resolveFileUrl(item.pet_avatar),
  })),
);

const advisorMetaText = computed(() => {
  if (maxChatPets.value > 1) {
    return `已解锁 ${usedChatPets.value}/${maxChatPets.value} 只宠物`;
  }
  return "普通用户最多 1 只";
});

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
    const [petResponse, quotaResponse, reportResponse, permissionResponse] = await Promise.all([
      getPetList(undefined, { showLoading: false }),
      getHealthQuota({ showLoading: false }),
      getHealthReportList(undefined, { showLoading: false }),
      getChatPermissions({ showLoading: false }),
    ]);

    petList.value = petResponse?.items || [];
    quotaRemaining.value = Number(quotaResponse?.remaining || 0);
    recentReports.value = reportResponse?.items || [];
    chatPermissionList.value = permissionResponse?.items || [];
    maxChatPets.value = Number(permissionResponse?.max_chat_pets || 1);
    usedChatPets.value = Number(permissionResponse?.used_chat_pets || 0);
  } catch (error) {
    petList.value = [];
    recentReports.value = [];
    quotaRemaining.value = 0;
    chatPermissionList.value = [];
    maxChatPets.value = 1;
    usedChatPets.value = 0;
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

function openAnalysisHistoryPage() {
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
  if (card.is_locked) {
    uni.showModal({
      title: "暂未解锁",
      content:
        card.lock_reason ||
        "当前账号可用的 AI 宠物顾问入口已满，开通会员或释放已有宠物入口后可继续使用。",
      confirmText: "我知道了",
      showCancel: false,
      confirmColor: "#FF8BA7",
    });
    return;
  }

  uni.navigateTo({
    url: `/pages/ai/chat?petId=${card.pet_id}`,
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
              先做体检报告解读，再进入宠物专属顾问继续追问，医疗信息和陪伴感都集中在这里。
            </text>
          </view>
          <view class="tag-soft">剩余 {{ quotaRemaining }} 次</view>
        </view>

        <view class="card ai-page__analysis-card">
          <view class="ai-page__analysis-top">
            <view class="ai-page__section-copy">
              <text class="ai-page__section-title">体检报告分析</text>
              <text class="section-caption">上传图片或 PDF，自动完成 OCR 识别和 AI 通俗解读。</text>
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
            <view class="btn-secondary ai-page__cta-btn" @click="openAnalysisHistoryPage">
              查看历史
            </view>
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
                <text class="ai-page__report-date">
                  {{ formatDisplayDate(String(report.created_at).slice(0, 10)) }}
                </text>
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
            <view class="ai-page__section-copy">
              <text class="ai-page__section-title">AI 宠物顾问</text>
              <text class="section-caption">
                每只宠物都有自己的历史对话，问答时会结合档案信息和近期健康记录。
              </text>
            </view>
            <view class="tag-soft">{{ advisorMetaText }}</view>
          </view>

          <view v-if="advisorCards.length" class="ai-page__advisor-list">
            <view
              v-for="card in advisorCards"
              :key="card.pet_id"
              class="ai-page__advisor-card"
              :class="{ 'ai-page__advisor-card--locked': card.is_locked }"
              @click="handleAdvisorClick(card)"
            >
              <view class="ai-page__advisor-avatar">
                <image v-if="card.avatarUrl" :src="card.avatarUrl" mode="aspectFill" />
                <text v-else>🐾</text>
              </view>
              <view class="ai-page__advisor-copy">
                <view class="ai-page__advisor-head">
                  <text class="ai-page__advisor-name">{{ card.pet_nickname }}</text>
                  <view v-if="card.is_locked" class="ai-page__advisor-lock">锁定</view>
                </view>
                <text class="section-caption">{{ card.species }} · {{ card.breed }}</text>
                <text class="ai-page__advisor-desc">
                  {{
                    card.is_locked
                      ? card.lock_reason || "当前宠物顾问入口暂未解锁"
                      : card.has_session
                        ? "进入这只宠物的专属顾问对话，继续最近的问题。"
                        : "进入专属 AI 顾问入口，开始新的健康咨询。"
                  }}
                </text>
              </view>
            </view>
          </view>
          <EmptyState
            v-else
            icon="🐱"
            text="先添加宠物档案，AI 才能按宠物建立历史记录和顾问入口。"
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

.ai-page__hero,
.ai-page__analysis-top,
.ai-page__section-head,
.ai-page__report-head,
.ai-page__advisor-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.ai-page__hero {
  align-items: flex-start;
}

.ai-page__hero-copy,
.ai-page__section-copy,
.ai-page__report-main,
.ai-page__advisor-copy {
  display: flex;
  flex: 1;
  min-width: 0;
  flex-direction: column;
  gap: 8rpx;
}

.ai-page__analysis-card {
  background: linear-gradient(180deg, rgba(255, 251, 252, 0.98) 0%, rgba(247, 251, 255, 0.98) 100%);
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
  background: rgba(255, 255, 255, 0.84);
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
