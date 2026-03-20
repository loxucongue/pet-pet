<script setup>
/** 记录详情页。 */
import { computed, ref } from "vue";
import { onLoad, onShow } from "@dcloudio/uni-app";

import LoadingOverlay from "@/components/LoadingOverlay.vue";
import { deleteRecord as removeRecord, getRecordDetail } from "@/api/record.js";
import { getReminderList } from "@/api/reminder.js";
import { getCategoryConfig, isExpenseCategory, isWeightSubType } from "@/data/record-categories.js";
import { formatDisplayDate } from "@/utils/date.js";
import { resolveFileUrl } from "@/utils/request.js";

const loading = ref(false);
const recordId = ref(null);
const recordDetail = ref(null);
const recordReminder = ref(null);

const categoryConfig = computed(() => getCategoryConfig(recordDetail.value?.category));
const previewImages = computed(() => (recordDetail.value?.images || []).map((item) => resolveFileUrl(item.image_path)));

function goBack() {
  if (getCurrentPages().length > 1) {
    uni.navigateBack({ delta: 1 });
    return;
  }

  uni.switchTab({
    url: "/pages/record/index",
  });
}

async function fetchRecordDetailData() {
  if (!recordId.value) {
    return;
  }

  const detail = await getRecordDetail(recordId.value, { showLoading: false });
  recordDetail.value = detail;
  const reminderList = await getReminderList({ pet_id: detail.pet_id }, { showLoading: false });
  recordReminder.value = (reminderList || []).find((item) => item.record_id === recordId.value) || null;
}

async function initializePage() {
  loading.value = true;
  try {
    await fetchRecordDetailData();
  } finally {
    loading.value = false;
  }
}

function previewImage(index) {
  uni.previewImage({
    urls: previewImages.value,
    current: previewImages.value[index],
  });
}

function openEditPage() {
  uni.navigateTo({
    url: `/pages/record/add?recordId=${recordId.value}`,
  });
}

async function handleDelete() {
  const modalResult = await new Promise((resolve) => {
    uni.showModal({
      title: "删除记录",
      content: "删除后会一并移除图片和关联提醒，确定继续吗？",
      confirmColor: "#FF8BA7",
      success: resolve,
      fail: () => resolve({ confirm: false }),
    });
  });

  if (!modalResult.confirm) {
    return;
  }

  loading.value = true;
  try {
    await removeRecord(recordId.value, { showLoading: false });
    uni.showToast({ title: "记录已删除", icon: "success" });
    setTimeout(() => {
      if (getCurrentPages().length > 1) {
        uni.navigateBack({ delta: 1 });
        return;
      }
      uni.switchTab({ url: "/pages/record/index" });
    }, 350);
  } finally {
    loading.value = false;
  }
}

onLoad((options) => {
  const nextRecordId = Number(options?.recordId || 0);
  if (nextRecordId) {
    recordId.value = nextRecordId;
  }
});

onShow(() => {
  initializePage();
});
</script>

<template>
  <view class="record-detail-page">
    <LoadingOverlay :visible="loading" text="正在整理记录详情..." />

    <scroll-view v-if="recordDetail" scroll-y class="record-detail-page__scroll">
      <view class="page-shell record-detail-page__shell">
        <view class="record-detail-page__topbar">
          <view class="record-detail-page__back" @click="goBack">‹</view>
          <view class="tag-soft">详情</view>
        </view>

        <view class="card record-detail-page__hero">
          <view
            class="record-detail-page__icon"
            :style="{ background: `${categoryConfig.color}22`, color: categoryConfig.color }"
          >
            {{ categoryConfig.icon }}
          </view>
          <view class="record-detail-page__hero-copy">
            <text class="record-detail-page__date">{{ formatDisplayDate(recordDetail.record_date) }}</text>
            <text class="record-detail-page__title">{{ recordDetail.sub_type }}</text>
            <text class="section-caption">{{ recordDetail.category }}</text>
          </view>
        </view>

        <view class="card">
          <text class="record-detail-page__section-title">备注</text>
          <text class="record-detail-page__note">{{ recordDetail.note || "这条记录没有补充备注。" }}</text>
        </view>

        <view v-if="previewImages.length" class="card">
          <text class="record-detail-page__section-title">图片</text>
          <view class="record-detail-page__image-grid">
            <image
              v-for="(image, index) in previewImages"
              :key="`${image}-${index}`"
              class="record-detail-page__image"
              :src="image"
              mode="aspectFill"
              @click="previewImage(index)"
            />
          </view>
        </view>

        <view v-if="isExpenseCategory(recordDetail.category) && recordDetail.amount !== null" class="card">
          <text class="record-detail-page__section-title">消费金额</text>
          <text class="record-detail-page__strong">¥{{ Number(recordDetail.amount).toFixed(2) }}</text>
        </view>

        <view v-if="isWeightSubType(recordDetail.sub_type) && recordDetail.weight_value !== null" class="card">
          <text class="record-detail-page__section-title">体重</text>
          <text class="record-detail-page__strong">{{ recordDetail.weight_value }} kg</text>
        </view>

        <view v-if="recordReminder" class="card record-detail-page__reminder-card">
          <text class="record-detail-page__section-title">关联提醒</text>
          <view class="record-detail-page__reminder-row">
            <text class="section-caption">提醒类型</text>
            <text class="record-detail-page__reminder-value">{{ recordReminder.reminder_type }}</text>
          </view>
          <view class="record-detail-page__reminder-row">
            <text class="section-caption">提醒周期</text>
            <text class="record-detail-page__reminder-value">每 {{ recordReminder.cycle_days }} 天</text>
          </view>
          <view class="record-detail-page__reminder-row">
            <text class="section-caption">下次提醒</text>
            <text class="record-detail-page__reminder-value">{{ formatDisplayDate(recordReminder.next_reminder_date) }}</text>
          </view>
        </view>
      </view>
    </scroll-view>

    <view class="record-detail-page__footer">
      <view class="btn-secondary record-detail-page__footer-btn" @click="handleDelete">删除</view>
      <view class="btn-primary record-detail-page__footer-btn" @click="openEditPage">编辑</view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.record-detail-page {
  min-height: 100vh;
  padding-bottom: 170rpx;
}

.record-detail-page__scroll {
  height: 100vh;
}

.record-detail-page__shell {
  gap: 24rpx;
}

.record-detail-page__topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.record-detail-page__back {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56rpx;
  height: 56rpx;
  border-radius: 50%;
  color: var(--text-primary);
  font-size: 36rpx;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: var(--shadow-card);
}

.record-detail-page__hero {
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.record-detail-page__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 96rpx;
  height: 96rpx;
  border-radius: 28rpx;
  font-size: 42rpx;
}

.record-detail-page__hero-copy {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.record-detail-page__date {
  color: var(--text-secondary);
  font-size: var(--font-caption);
}

.record-detail-page__title,
.record-detail-page__section-title {
  color: var(--text-primary);
  font-size: 30rpx;
  font-weight: 700;
}

.record-detail-page__note {
  display: block;
  margin-top: 18rpx;
  color: var(--text-primary);
  font-size: var(--font-body);
  line-height: 1.7;
}

.record-detail-page__image-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14rpx;
  margin-top: 18rpx;
}

.record-detail-page__image {
  width: 100%;
  height: 204rpx;
  border-radius: 24rpx;
}

.record-detail-page__strong {
  display: block;
  margin-top: 18rpx;
  color: var(--text-primary);
  font-size: 44rpx;
  font-weight: 700;
}

.record-detail-page__reminder-card {
  background: linear-gradient(180deg, rgba(255, 250, 252, 0.96) 0%, rgba(247, 251, 255, 0.96) 100%);
}

.record-detail-page__reminder-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  margin-top: 18rpx;
}

.record-detail-page__reminder-value {
  color: var(--text-primary);
  font-size: var(--font-caption);
  font-weight: 600;
}

.record-detail-page__footer {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  gap: 16rpx;
  padding: 18rpx 24rpx 34rpx;
  background: rgba(255, 253, 254, 0.96);
  box-shadow: 0 -12rpx 28rpx rgba(255, 195, 211, 0.14);
  backdrop-filter: blur(10px);
}

.record-detail-page__footer-btn {
  flex: 1;
}
</style>
