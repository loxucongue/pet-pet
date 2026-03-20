<script setup>
/** 体重趋势页面。 */
import { computed, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";

import EmptyState from "@/components/EmptyState.vue";
import LoadingOverlay from "@/components/LoadingOverlay.vue";
import PetSwitcher from "@/components/PetSwitcher.vue";
import SimpleLineChart from "@/components/SimpleLineChart.vue";
import { getPetList } from "@/api/pet.js";
import { getWeightTrend } from "@/api/record.js";

const loading = ref(false);
const petList = ref([]);
const currentPetId = ref(null);
const initialPetId = ref(null);
const period = ref("1m");
const points = ref([]);

const periodOptions = [
  { label: "近1月", value: "1m" },
  { label: "近3月", value: "3m" },
  { label: "近6月", value: "6m" },
  { label: "近1年", value: "1y" },
  { label: "全部", value: "all" },
];

const currentWeight = computed(() => (points.value.length ? Number(points.value[points.value.length - 1].weight) : null));
const deltaWeight = computed(() => {
  if (points.value.length < 2) {
    return null;
  }
  return Number(points.value[points.value.length - 1].weight) - Number(points.value[points.value.length - 2].weight);
});

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

async function fetchTrend() {
  if (!currentPetId.value) {
    points.value = [];
    return;
  }

  const response = await getWeightTrend(
    {
      pet_id: currentPetId.value,
      period: period.value,
    },
    { showLoading: false },
  );
  points.value = Array.isArray(response) ? response : [];
}

async function initializePage() {
  loading.value = true;
  try {
    await fetchPets();
    await fetchTrend();
  } finally {
    loading.value = false;
  }
}

function setPeriod(value) {
  period.value = value;
  fetchTrend();
}

function handlePetChange(petId) {
  currentPetId.value = petId;
  fetchTrend();
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
  <view class="trend-page">
    <LoadingOverlay :visible="loading" text="正在加载体重趋势..." />

    <view class="page-shell trend-page__shell">
      <view class="trend-page__hero">
        <text class="section-title">体重趋势</text>
        <text class="section-caption">按时间范围查看体重记录，快速判断增减变化。</text>
      </view>

      <view v-if="petList.length" class="page-content">
        <view class="card">
          <PetSwitcher :pet-list="petList" :current-pet-id="currentPetId" @change="handlePetChange" />
        </view>

        <view class="card">
          <view class="trend-page__tabs">
            <view
              v-for="item in periodOptions"
              :key="item.value"
              class="trend-page__tab"
              :class="{ 'trend-page__tab--active': period === item.value }"
              @click="setPeriod(item.value)"
            >
              {{ item.label }}
            </view>
          </view>

          <view v-if="points.length" class="trend-page__summary">
            <view class="trend-page__metric">
              <text class="section-caption">当前体重</text>
              <text class="trend-page__metric-value">{{ currentWeight }} kg</text>
            </view>
            <view class="trend-page__metric">
              <text class="section-caption">较上次变化</text>
              <text
                class="trend-page__metric-value"
                :class="{
                  'trend-page__metric-value--up': deltaWeight > 0,
                  'trend-page__metric-value--down': deltaWeight < 0,
                }"
              >
                {{ deltaWeight === null ? "--" : `${deltaWeight > 0 ? "+" : ""}${deltaWeight.toFixed(2)} kg` }}
              </text>
            </view>
          </view>

          <SimpleLineChart :points="points" />
        </view>
      </view>

      <view v-else class="card">
        <EmptyState icon="📉" text="先添加宠物并记录体重，这里才会生成趋势图。" />
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.trend-page__shell {
  gap: 24rpx;
}

.trend-page__hero {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.trend-page__tabs {
  display: flex;
  gap: 10rpx;
  padding: 8rpx;
  margin-bottom: 24rpx;
  border-radius: 999rpx;
  background: #f7f1f5;
}

.trend-page__tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 66rpx;
  border-radius: 999rpx;
  color: var(--text-secondary);
  font-size: var(--font-mini);
}

.trend-page__tab--active {
  color: var(--text-primary);
  font-weight: 700;
  background: #ffffff;
  box-shadow: 0 8rpx 14rpx rgba(255, 139, 167, 0.14);
}

.trend-page__summary {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
  margin-bottom: 24rpx;
}

.trend-page__metric {
  padding: 24rpx;
  border-radius: 24rpx;
  background: #fff8fa;
}

.trend-page__metric-value {
  display: block;
  margin-top: 10rpx;
  color: var(--text-primary);
  font-size: 34rpx;
  font-weight: 700;
}

.trend-page__metric-value--up {
  color: var(--color-danger);
}

.trend-page__metric-value--down {
  color: var(--color-success);
}
</style>
