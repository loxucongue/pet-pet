<script setup>
/** 消费统计页面。 */
import { computed, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";

import EmptyState from "@/components/EmptyState.vue";
import LoadingOverlay from "@/components/LoadingOverlay.vue";
import PetSwitcher from "@/components/PetSwitcher.vue";
import SimpleDonutChart from "@/components/SimpleDonutChart.vue";
import { getPetList } from "@/api/pet.js";
import { getExpenseStats } from "@/api/record.js";
import { getCurrentYear } from "@/utils/date.js";

const loading = ref(false);
const petList = ref([]);
const currentPetId = ref(null);
const initialPetId = ref(null);
const mode = ref("month");
const selectedYear = ref(getCurrentYear());
const selectedMonth = ref(new Date().getMonth() + 1);
const stats = ref({
  total: 0,
  details: [],
});

const yearOptions = Array.from({ length: 6 }, (_, index) => getCurrentYear() - 4 + index);
const monthOptions = Array.from({ length: 12 }, (_, index) => index + 1);
const chartColors = ["#FF8BA7", "#A8D8EA", "#7EC699", "#F5C842", "#A88BFF", "#FFB36B"];

const detailList = computed(() =>
  (stats.value.details || []).map((item, index) => {
    const amount = Number(item.amount) || 0;
    const percent = stats.value.total ? (amount / stats.value.total) * 100 : 0;

    return {
      ...item,
      amount,
      percent,
      color: chartColors[index % chartColors.length],
    };
  }),
);

async function fetchPets() {
  const response = await getPetList(undefined, { showLoading: false });
  petList.value = response?.items || [];
  if (!petList.value.length) {
    currentPetId.value = null;
    return;
  }

  const matchedPet = petList.value.find((item) => item.id === initialPetId.value);
  currentPetId.value = matchedPet?.id || currentPetId.value || petList.value[0].id;
}

async function fetchStats() {
  if (!currentPetId.value) {
    stats.value = { total: 0, details: [] };
    return;
  }

  const response = await getExpenseStats(
    {
      pet_id: currentPetId.value,
      year: selectedYear.value,
      month: mode.value === "month" ? selectedMonth.value : undefined,
    },
    { showLoading: false },
  );

  stats.value = {
    total: Number(response?.total || 0),
    details: response?.details || [],
  };
}

async function initializePage() {
  loading.value = true;
  try {
    await fetchPets();
    await fetchStats();
  } finally {
    loading.value = false;
  }
}

function setMode(nextMode) {
  mode.value = nextMode;
  fetchStats();
}

function handlePetChange(petId) {
  currentPetId.value = petId;
  fetchStats();
}

function handleYearChange(event) {
  selectedYear.value = yearOptions[event.detail.value];
  fetchStats();
}

function handleMonthChange(event) {
  selectedMonth.value = monthOptions[event.detail.value];
  fetchStats();
}

onLoad((options) => {
  const petId = Number(options?.petId || 0);
  if (petId) {
    initialPetId.value = petId;
  }
  initializePage();
});
</script>

<template>
  <view class="expense-page">
    <LoadingOverlay :visible="loading" text="正在加载消费统计..." />

    <view class="page-shell expense-page__shell">
      <view class="expense-page__hero">
        <text class="section-title">消费统计</text>
        <text class="section-caption">按月或按年看清主粮、玩具、日用品等花费比例。</text>
      </view>

      <view v-if="petList.length" class="page-content">
        <view class="card">
          <PetSwitcher :pet-list="petList" :current-pet-id="currentPetId" @change="handlePetChange" />
        </view>

        <view class="card">
          <view class="expense-page__mode-tabs">
            <view
              class="expense-page__mode-tab"
              :class="{ 'expense-page__mode-tab--active': mode === 'month' }"
              @click="setMode('month')"
            >
              月度
            </view>
            <view
              class="expense-page__mode-tab"
              :class="{ 'expense-page__mode-tab--active': mode === 'year' }"
              @click="setMode('year')"
            >
              年度
            </view>
          </view>

          <view class="expense-page__picker-row">
            <picker :range="yearOptions" :value="yearOptions.indexOf(selectedYear)" @change="handleYearChange">
              <view class="input-field expense-page__picker">{{ selectedYear }} 年</view>
            </picker>
            <picker
              v-if="mode === 'month'"
              :range="monthOptions"
              :value="monthOptions.indexOf(selectedMonth)"
              @change="handleMonthChange"
            >
              <view class="input-field expense-page__picker">{{ selectedMonth }} 月</view>
            </picker>
          </view>

          <view class="expense-page__total">
            <text class="section-caption">总金额</text>
            <text class="expense-page__total-value">¥{{ stats.total.toFixed(2) }}</text>
          </view>

          <SimpleDonutChart :segments="detailList" :total="stats.total" />
        </view>

        <view v-if="detailList.length" class="card">
          <text class="expense-page__detail-title">分类明细</text>
          <view v-for="item in detailList" :key="item.sub_type" class="expense-page__detail-item">
            <view class="expense-page__detail-main">
              <view class="expense-page__detail-dot" :style="{ background: item.color }" />
              <text class="expense-page__detail-name">{{ item.sub_type }}</text>
            </view>
            <view class="expense-page__detail-side">
              <text class="expense-page__detail-amount">¥{{ item.amount.toFixed(2) }}</text>
              <text class="expense-page__detail-percent">{{ item.percent.toFixed(1) }}%</text>
            </view>
          </view>
        </view>

        <view v-else class="card">
          <EmptyState icon="💤" text="这个时间范围里还没有消费记录。" />
        </view>
      </view>

      <view v-else class="card">
        <EmptyState icon="💸" text="先添加宠物并记录消费，统计页才会出现数据。" />
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.expense-page__shell {
  gap: 24rpx;
}

.expense-page__hero {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.expense-page__mode-tabs {
  display: flex;
  gap: 10rpx;
  padding: 8rpx;
  border-radius: 999rpx;
  background: #f6f1f4;
}

.expense-page__mode-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 66rpx;
  border-radius: 999rpx;
  color: var(--text-secondary);
  font-size: var(--font-caption);
}

.expense-page__mode-tab--active {
  color: var(--text-primary);
  font-weight: 700;
  background: #ffffff;
  box-shadow: 0 8rpx 14rpx rgba(255, 139, 167, 0.14);
}

.expense-page__picker-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
  margin-top: 20rpx;
}

.expense-page__picker {
  display: flex;
  align-items: center;
}

.expense-page__total {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  margin: 28rpx 0 22rpx;
}

.expense-page__total-value {
  color: var(--text-primary);
  font-size: 52rpx;
  font-weight: 700;
}

.expense-page__detail-title {
  color: var(--text-primary);
  font-size: 30rpx;
  font-weight: 700;
}

.expense-page__detail-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  padding: 18rpx 0;
  border-bottom: 2rpx solid rgba(255, 139, 167, 0.08);
}

.expense-page__detail-item:last-child {
  padding-bottom: 0;
  border-bottom: 0;
}

.expense-page__detail-main,
.expense-page__detail-side {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.expense-page__detail-dot {
  width: 18rpx;
  height: 18rpx;
  border-radius: 50%;
}

.expense-page__detail-name,
.expense-page__detail-amount {
  color: var(--text-primary);
  font-size: var(--font-caption);
}

.expense-page__detail-percent {
  color: var(--text-secondary);
  font-size: var(--font-mini);
}
</style>
