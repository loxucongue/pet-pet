<script setup>
/** 体检报告分析详情页。 */
import { computed, ref } from "vue";
import { onLoad, onShow } from "@dcloudio/uni-app";

import EmptyState from "@/components/EmptyState.vue";
import LoadingOverlay from "@/components/LoadingOverlay.vue";
import {
  getHealthReportDetail,
  reanalyzeHealthReport,
  updateHealthReportIndicators,
} from "@/api/health.js";
import { formatDisplayDate } from "@/utils/date.js";
import { resolveFileUrl } from "@/utils/request.js";

const reportId = ref(null);
const loading = ref(false);
const saving = ref(false);
const reanalyzing = ref(false);
const reportDetail = ref(null);
const editMode = ref(false);
const editableIndicators = ref([]);

const indicatorStatusOptions = ["正常", "偏高", "偏低"];

const originalFileUrl = computed(() => resolveFileUrl(reportDetail.value?.original_file_path));
const isImageReport = computed(() => reportDetail.value?.file_type === "image");
const parsedIndicators = computed(() => normalizeIndicators(reportDetail.value?.parsed_indicators_json));
const reportStatusMeta = computed(() => getReportStatusMeta(reportDetail.value?.status));

function normalizeIndicators(value) {
  if (Array.isArray(value)) {
    return value.map((item) => ({
      name: item.name || "",
      value: item.value || "",
      unit: item.unit || "",
      reference_range: item.reference_range || "",
      status: item.status || "正常",
    }));
  }

  if (value && typeof value === "object" && Array.isArray(value.items)) {
    return normalizeIndicators(value.items);
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

function getIndicatorStatusMeta(status) {
  const normalized = String(status || "").trim().toLowerCase();
  if (normalized === "high" || normalized === "偏高") {
    return {
      text: "偏高",
      color: "#FF6B6B",
      background: "rgba(255, 107, 107, 0.14)",
    };
  }

  if (normalized === "low" || normalized === "偏低") {
    return {
      text: "偏低",
      color: "#F5C842",
      background: "rgba(245, 200, 66, 0.18)",
    };
  }

  return {
    text: "正常",
    color: "#7EC699",
    background: "rgba(126, 198, 153, 0.14)",
  };
}

function cloneIndicators(indicators) {
  return indicators.map((item) => ({
    name: item.name || "",
    value: item.value || "",
    unit: item.unit || "",
    reference_range: item.reference_range || "",
    status: item.status || "正常",
  }));
}

function goBack() {
  if (getCurrentPages().length > 1) {
    uni.navigateBack({ delta: 1 });
    return;
  }

  uni.redirectTo({
    url: "/pages/ai/report-history",
  });
}

async function fetchReportDetail() {
  if (!reportId.value) {
    return;
  }

  loading.value = true;
  try {
    const detail = await getHealthReportDetail(reportId.value, { showLoading: false });
    reportDetail.value = detail;

    if (!editMode.value) {
      editableIndicators.value = cloneIndicators(parsedIndicators.value);
    }
  } catch (error) {
    reportDetail.value = null;
    editableIndicators.value = [];
  } finally {
    loading.value = false;
  }
}

function previewOriginalImage() {
  if (!isImageReport.value || !originalFileUrl.value) {
    return;
  }

  uni.previewImage({
    urls: [originalFileUrl.value],
    current: originalFileUrl.value,
  });
}

function openPdfTip() {
  uni.showModal({
    title: "PDF 报告",
    content: "当前报告为 PDF 文件，H5 预览下建议在新标签页中打开静态链接查看。",
    confirmText: "知道了",
    showCancel: false,
    confirmColor: "#FF8BA7",
  });
}

function enterEditMode() {
  editMode.value = true;
  editableIndicators.value = cloneIndicators(parsedIndicators.value);
}

function cancelEditMode() {
  editMode.value = false;
  editableIndicators.value = cloneIndicators(parsedIndicators.value);
}

function handleIndicatorStatusChange(index, event) {
  editableIndicators.value[index].status = indicatorStatusOptions[event.detail.value];
}

async function saveIndicators() {
  saving.value = true;
  try {
    const indicators = editableIndicators.value
      .map((item) => ({
        name: String(item.name || "").trim(),
        value: String(item.value || "").trim(),
        unit: String(item.unit || "").trim() || null,
        reference_range: String(item.reference_range || "").trim() || null,
        status: String(item.status || "").trim() || "正常",
      }))
      .filter((item) => item.name || item.value);

    const updatedReport = await updateHealthReportIndicators(
      reportId.value,
      { indicators },
      { showLoading: false },
    );

    reportDetail.value = updatedReport;
    editMode.value = false;
    editableIndicators.value = cloneIndicators(normalizeIndicators(updatedReport.parsed_indicators_json));

    uni.showToast({
      title: "指标已保存",
      icon: "success",
    });
  } catch (error) {
    // Request layer already handles error toasts.
  } finally {
    saving.value = false;
  }
}

async function handleReanalyze() {
  reanalyzing.value = true;
  try {
    const updatedReport = await reanalyzeHealthReport(reportId.value, { showLoading: false });
    reportDetail.value = updatedReport;
    uni.showToast({
      title: "解读已更新",
      icon: "success",
    });
  } catch (error) {
    // Request layer already handles error toasts.
  } finally {
    reanalyzing.value = false;
  }
}

onLoad((options) => {
  const nextReportId = Number(options?.reportId || 0);
  if (nextReportId) {
    reportId.value = nextReportId;
  }
});

onShow(() => {
  fetchReportDetail();
});
</script>

<template>
  <view class="report-detail-page">
    <LoadingOverlay
      :visible="loading || saving || reanalyzing"
      :text="saving ? '正在保存指标...' : reanalyzing ? '正在重新生成解读...' : '正在加载报告详情...'"
    />

    <scroll-view v-if="reportDetail" scroll-y class="report-detail-page__scroll">
      <view class="page-shell report-detail-page__shell">
        <view class="report-detail-page__topbar">
          <view class="report-detail-page__back" @click="goBack">‹</view>
          <view class="report-detail-page__top-actions">
            <view
              class="report-detail-page__action-pill"
              :style="{ color: reportStatusMeta.color, background: reportStatusMeta.background }"
            >
              {{ reportStatusMeta.text }}
            </view>
            <view
              class="report-detail-page__action-pill report-detail-page__action-pill--plain"
              @click="editMode ? cancelEditMode() : enterEditMode()"
            >
              {{ editMode ? "取消" : "编辑" }}
            </view>
          </view>
        </view>

        <view class="card report-detail-page__hero">
          <text class="section-title">体检分析结果</text>
          <text class="section-caption">
            {{ formatDisplayDate(String(reportDetail.created_at).slice(0, 10)) }}
            ·
            {{ reportDetail.file_type === "pdf" ? "PDF 报告" : "图片报告" }}
          </text>
        </view>

        <view class="card">
          <view class="report-detail-page__section-head">
            <text class="report-detail-page__section-title">原始报告</text>
            <text class="section-caption">{{ isImageReport ? "点击可放大查看" : "已保留原始 PDF 文件" }}</text>
          </view>

          <image
            v-if="isImageReport && originalFileUrl"
            class="report-detail-page__cover"
            :src="originalFileUrl"
            mode="widthFix"
            @click="previewOriginalImage"
          />
          <view v-else class="report-detail-page__pdf-card" @click="openPdfTip">
            <text class="report-detail-page__pdf-icon">PDF</text>
            <view class="report-detail-page__pdf-copy">
              <text class="report-detail-page__pdf-title">原始报告文件</text>
              <text class="section-caption">当前为 PDF 报告，静态链接已保留到系统中。</text>
            </view>
          </view>
        </view>

        <view class="card">
          <view class="report-detail-page__section-head">
            <text class="report-detail-page__section-title">指标数据</text>
            <text class="section-caption">{{ editMode ? "编辑后保存会同步覆盖当前指标数据" : "颜色可快速判断指标状态" }}</text>
          </view>

          <view v-if="(editMode ? editableIndicators : parsedIndicators).length" class="report-detail-page__indicator-list">
            <view
              v-for="(indicator, index) in editMode ? editableIndicators : parsedIndicators"
              :key="`${indicator.name}-${index}`"
              class="report-detail-page__indicator-card"
            >
              <template v-if="editMode">
                <view class="report-detail-page__indicator-grid">
                  <view class="report-detail-page__field">
                    <text class="report-detail-page__label">名称</text>
                    <input v-model="editableIndicators[index].name" class="input-field" placeholder="如：白细胞" />
                  </view>
                  <view class="report-detail-page__field">
                    <text class="report-detail-page__label">数值</text>
                    <input v-model="editableIndicators[index].value" class="input-field" placeholder="如：12.5" />
                  </view>
                </view>

                <view class="report-detail-page__indicator-grid">
                  <view class="report-detail-page__field">
                    <text class="report-detail-page__label">单位</text>
                    <input v-model="editableIndicators[index].unit" class="input-field" placeholder="如：10^9/L" />
                  </view>
                  <view class="report-detail-page__field">
                    <text class="report-detail-page__label">参考范围</text>
                    <input
                      v-model="editableIndicators[index].reference_range"
                      class="input-field"
                      placeholder="如：6-17"
                    />
                  </view>
                </view>

                <view class="report-detail-page__field">
                  <text class="report-detail-page__label">状态</text>
                  <picker
                    :range="indicatorStatusOptions"
                    :value="Math.max(indicatorStatusOptions.indexOf(indicator.status || '正常'), 0)"
                    @change="(event) => handleIndicatorStatusChange(index, event)"
                  >
                    <view class="input-field report-detail-page__picker">
                      <text>{{ indicator.status || "正常" }}</text>
                      <text>›</text>
                    </view>
                  </picker>
                </view>
              </template>

              <template v-else>
                <view class="report-detail-page__indicator-top">
                  <view>
                    <text class="report-detail-page__indicator-name">{{ indicator.name }}</text>
                    <text class="report-detail-page__indicator-range">
                      参考范围：{{ indicator.reference_range || "未提供" }}
                    </text>
                  </view>
                  <view
                    class="report-detail-page__status-chip"
                    :style="{
                      color: getIndicatorStatusMeta(indicator.status).color,
                      background: getIndicatorStatusMeta(indicator.status).background,
                    }"
                  >
                    {{ getIndicatorStatusMeta(indicator.status).text }}
                  </view>
                </view>
                <text class="report-detail-page__indicator-value">
                  {{ indicator.value }}{{ indicator.unit ? ` ${indicator.unit}` : "" }}
                </text>
              </template>
            </view>
          </view>
          <EmptyState
            v-else
            icon="📋"
            text="还没有识别出明确的指标数据，可以稍后回来查看或手动编辑补充。"
          />
        </view>

        <view class="card">
          <view class="report-detail-page__section-head">
            <text class="report-detail-page__section-title">AI 通俗解读</text>
            <view class="btn-secondary report-detail-page__mini-btn" @click="handleReanalyze">
              重新解读
            </view>
          </view>
          <text class="report-detail-page__interpretation">
            {{ reportDetail.ai_interpretation || "AI 解读还未生成，可能仍在处理中或本次识别失败。" }}
          </text>
        </view>
      </view>
    </scroll-view>

    <view v-else-if="!loading" class="page-shell">
      <view class="card">
        <EmptyState
          icon="🧾"
          text="没有找到这份体检报告，可能已失效或你当前没有访问权限。"
          button-text="返回历史"
          @action="goBack"
        />
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.report-detail-page {
  min-height: 100vh;
  padding-bottom: 56rpx;
}

.report-detail-page__scroll {
  height: 100vh;
}

.report-detail-page__shell {
  gap: 24rpx;
}

.report-detail-page__topbar,
.report-detail-page__section-head,
.report-detail-page__indicator-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.report-detail-page__top-actions {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.report-detail-page__back {
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

.report-detail-page__action-pill,
.report-detail-page__status-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 48rpx;
  padding: 0 18rpx;
  border-radius: 999rpx;
  font-size: var(--font-mini);
}

.report-detail-page__action-pill--plain {
  color: var(--color-primary);
  background: rgba(255, 198, 211, 0.4);
}

.report-detail-page__section-title,
.report-detail-page__indicator-name,
.report-detail-page__pdf-title {
  color: var(--text-primary);
  font-size: 30rpx;
  font-weight: 700;
}

.report-detail-page__cover {
  width: 100%;
  margin-top: 18rpx;
  border-radius: 24rpx;
}

.report-detail-page__pdf-card {
  display: flex;
  align-items: center;
  gap: 18rpx;
  margin-top: 18rpx;
  padding: 24rpx;
  border-radius: 24rpx;
  background: #fff8fa;
}

.report-detail-page__pdf-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 88rpx;
  height: 88rpx;
  border-radius: 24rpx;
  color: #ffffff;
  font-size: 28rpx;
  font-weight: 700;
  background: linear-gradient(135deg, #ff8ba7 0%, #a8d8ea 100%);
}

.report-detail-page__pdf-copy {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 8rpx;
}

.report-detail-page__indicator-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  margin-top: 18rpx;
}

.report-detail-page__indicator-card {
  padding: 22rpx;
  border-radius: 24rpx;
  background: #fff9fb;
}

.report-detail-page__indicator-range {
  display: block;
  margin-top: 8rpx;
  color: var(--text-secondary);
  font-size: var(--font-mini);
}

.report-detail-page__indicator-value {
  display: block;
  margin-top: 16rpx;
  color: var(--text-primary);
  font-size: 38rpx;
  font-weight: 700;
}

.report-detail-page__indicator-grid {
  display: flex;
  gap: 16rpx;
  margin-top: 14rpx;
}

.report-detail-page__field {
  display: flex;
  flex: 1;
  min-width: 0;
  flex-direction: column;
  gap: 12rpx;
}

.report-detail-page__label {
  color: #d37898;
  font-size: var(--font-caption);
  font-weight: 600;
}

.report-detail-page__picker {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.report-detail-page__mini-btn {
  min-width: 0;
  min-height: 64rpx;
  padding: 0 24rpx;
  font-size: var(--font-caption);
}

.report-detail-page__interpretation {
  display: block;
  margin-top: 18rpx;
  color: var(--text-primary);
  font-size: var(--font-body);
  line-height: 1.8;
  white-space: pre-wrap;
}
</style>
