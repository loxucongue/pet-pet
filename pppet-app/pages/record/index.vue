<script setup>
/** 记录主页面。 */
import { computed, ref } from "vue";
import { onLoad, onShow } from "@dcloudio/uni-app";

import EmptyState from "@/components/EmptyState.vue";
import LoadingOverlay from "@/components/LoadingOverlay.vue";
import PetSwitcher from "@/components/PetSwitcher.vue";
import RecordCalendar from "@/components/RecordCalendar.vue";
import { getPetList } from "@/api/pet.js";
import { getRecordList } from "@/api/record.js";
import { getCategoryConfig } from "@/data/record-categories.js";
import { formatDisplayDate, formatMonth, getMonthRange, getToday } from "@/utils/date.js";

const loading = ref(false);
const petList = ref([]);
const currentPetId = ref(null);
const initialPetId = ref(null);
const currentMonth = ref(formatMonth(new Date()));
const selectedDate = ref(getToday());
const monthRecords = ref([]);

const markedDates = computed(() => [...new Set(monthRecords.value.map((item) => item.record_date))]);
const monthCount = computed(() => monthRecords.value.length);
const currentPetName = computed(() => petList.value.find((item) => item.id === currentPetId.value)?.nickname || "未选择宠物");

const selectedRecords = computed(() =>
  monthRecords.value
    .filter((item) => item.record_date === selectedDate.value)
    .map((item) => ({
      ...item,
      categoryConfig: getCategoryConfig(item.category),
      summary: item.note || `${item.sub_type} 已记录`,
      timeText: String(item.created_at || "").slice(11, 16) || "全天",
    }))
    .sort((left, right) => String(right.created_at).localeCompare(String(left.created_at))),
);

async function fetchPets() {
  const response = await getPetList(undefined, { showLoading: false });
  petList.value = response?.items || [];

  if (!petList.value.length) {
    currentPetId.value = null;
    return;
  }

  const matchedInitialPet = petList.value.find((item) => item.id === initialPetId.value);
  const matchedCurrentPet = petList.value.find((item) => item.id === currentPetId.value);
  currentPetId.value = matchedInitialPet?.id || matchedCurrentPet?.id || petList.value[0].id;
}

async function fetchMonthRecords() {
  if (!currentPetId.value) {
    monthRecords.value = [];
    return;
  }

  const range = getMonthRange(currentMonth.value);
  const response = await getRecordList(
    {
      pet_id: currentPetId.value,
      date_from: range.start,
      date_to: range.end,
    },
    { showLoading: false },
  );
  monthRecords.value = response?.items || [];
}

async function initializePage() {
  loading.value = true;
  try {
    await fetchPets();
    await fetchMonthRecords();
  } finally {
    loading.value = false;
  }
}

function handlePetChange(petId) {
  if (!petId) {
    openAddPetPage();
    return;
  }

  currentPetId.value = petId;
  const today = getToday();
  selectedDate.value = today.slice(0, 7) === currentMonth.value ? today : getMonthRange(currentMonth.value).start;
  fetchMonthRecords();
}

function handleMonthChange(monthText) {
  currentMonth.value = monthText;
  if (selectedDate.value.slice(0, 7) !== monthText) {
    selectedDate.value = getMonthRange(monthText).start;
  }
  fetchMonthRecords();
}

function handleDateSelect(dateText) {
  selectedDate.value = dateText;
  const monthText = dateText.slice(0, 7);
  if (monthText !== currentMonth.value) {
    currentMonth.value = monthText;
    fetchMonthRecords();
  }
}

function openAddPage() {
  if (!currentPetId.value) {
    openAddPetPage();
    return;
  }

  uni.navigateTo({
    url: `/pages/record/add?petId=${currentPetId.value}`,
  });
}

function openAddPetPage() {
  uni.navigateTo({
    url: "/pages/pet/add",
  });
}

function openDetailPage(recordId) {
  uni.navigateTo({
    url: `/pages/record/detail?recordId=${recordId}`,
  });
}

function openWeightTrendPage() {
  if (!currentPetId.value) {
    return;
  }

  uni.navigateTo({
    url: `/pages/record/weight-trend?petId=${currentPetId.value}`,
  });
}

function openExpenseStatsPage() {
  if (!currentPetId.value) {
    return;
  }

  uni.navigateTo({
    url: `/pages/record/expense-stats?petId=${currentPetId.value}`,
  });
}

onLoad((options) => {
  const petId = Number(options?.petId || 0);
  if (petId) {
    initialPetId.value = petId;
  }
});

onShow(() => {
  initializePage();
});
</script>

<template>
  <view class="record-page">
    <LoadingOverlay :visible="loading" text="正在整理记录..." />

    <view class="page-shell record-page__shell">
      <view class="record-page__hero">
        <view>
          <text class="section-title">记录日常</text>
          <text class="section-caption">围绕 {{ currentPetName }} 的护理、体重、消费和医疗记录都在这里。</text>
        </view>
        <view class="tag-soft">本月 {{ monthCount }} 条</view>
      </view>

      <view v-if="petList.length" class="page-content">
        <view class="card">
          <view class="record-page__section-head">
            <text class="record-page__section-title">宠物切换</text>
            <text class="section-caption">切换后会同步刷新月历和当日记录</text>
          </view>
          <PetSwitcher :pet-list="petList" :current-pet-id="currentPetId" @change="handlePetChange" />
        </view>

        <view class="record-page__quick-grid">
          <view class="card record-page__quick-card" @click="openWeightTrendPage">
            <text class="record-page__quick-icon">📈</text>
            <text class="record-page__quick-title">体重趋势</text>
            <text class="section-caption">查看近 1 月到全部的变化</text>
          </view>
          <view class="card record-page__quick-card" @click="openExpenseStatsPage">
            <text class="record-page__quick-icon">💸</text>
            <text class="record-page__quick-title">消费统计</text>
            <text class="section-caption">按月或按年查看分类花费</text>
          </view>
        </view>

        <RecordCalendar
          :month="currentMonth"
          :selected-date="selectedDate"
          :marked-dates="markedDates"
          @change-month="handleMonthChange"
          @update:selectedDate="handleDateSelect"
        />

        <view class="card">
          <view class="record-page__section-head">
            <view>
              <text class="record-page__section-title">{{ formatDisplayDate(selectedDate) }}</text>
              <text class="section-caption">点击记录可进入详情页查看完整内容</text>
            </view>
            <text class="tag-soft">{{ selectedRecords.length }} 条</text>
          </view>

          <view v-if="selectedRecords.length" class="record-page__list">
            <view
              v-for="record in selectedRecords"
              :key="record.id"
              class="record-page__item"
              @click="openDetailPage(record.id)"
            >
              <view
                class="record-page__icon"
                :style="{ background: `${record.categoryConfig.color}22`, color: record.categoryConfig.color }"
              >
                {{ record.categoryConfig.icon }}
              </view>
              <view class="record-page__meta">
                <view class="record-page__row">
                  <text class="record-page__item-title">{{ record.sub_type }}</text>
                  <text class="record-page__item-time">{{ record.timeText }}</text>
                </view>
                <text class="record-page__item-note">{{ record.summary }}</text>
              </view>
            </view>
          </view>

          <EmptyState
            v-else
            icon="📝"
            text="这一天还没有记录，点右下角先记下一条吧。"
            button-text="去添加记录"
            @action="openAddPage"
          />
        </view>
      </view>

      <view v-else class="card">
        <EmptyState
          icon="🐾"
          text="先添加宠物档案，记录页才会开始变得热闹。"
          button-text="添加宠物"
          @action="openAddPetPage"
        />
      </view>
    </view>

    <view class="record-page__fab" @click="openAddPage">+</view>
  </view>
</template>

<style scoped lang="scss">
.record-page {
  min-height: 100vh;
  padding-bottom: 160rpx;
}

.record-page__shell {
  gap: 24rpx;
}

.record-page__hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24rpx;
}

.record-page__section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  margin-bottom: 20rpx;
}

.record-page__section-title {
  display: block;
  color: var(--text-primary);
  font-size: 30rpx;
  font-weight: 700;
}

.record-page__quick-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
}

.record-page__quick-card {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.record-page__quick-icon {
  font-size: 36rpx;
}

.record-page__quick-title {
  color: var(--text-primary);
  font-size: 28rpx;
  font-weight: 700;
}

.record-page__list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.record-page__item {
  display: flex;
  align-items: center;
  gap: 18rpx;
  padding: 22rpx;
  border-radius: 24rpx;
  background: #fff9fb;
}

.record-page__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 72rpx;
  height: 72rpx;
  border-radius: 22rpx;
  font-size: 34rpx;
}

.record-page__meta {
  flex: 1;
  min-width: 0;
}

.record-page__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}

.record-page__item-title {
  color: var(--text-primary);
  font-size: 28rpx;
  font-weight: 700;
}

.record-page__item-time {
  color: var(--text-secondary);
  font-size: var(--font-mini);
}

.record-page__item-note {
  display: block;
  margin-top: 10rpx;
  overflow: hidden;
  color: var(--text-secondary);
  font-size: var(--font-caption);
  white-space: nowrap;
  text-overflow: ellipsis;
}

.record-page__fab {
  position: fixed;
  right: 28rpx;
  bottom: 150rpx;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 112rpx;
  height: 112rpx;
  border-radius: 50%;
  color: #ffffff;
  font-size: 54rpx;
  font-weight: 500;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
  box-shadow: 0 20rpx 36rpx rgba(255, 139, 167, 0.26);
}
</style>
