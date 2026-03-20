<script setup>
/** 宠物管理列表页面。 */
import { ref } from "vue";
import { onShow } from "@dcloudio/uni-app";

import EmptyState from "@/components/EmptyState.vue";
import LoadingOverlay from "@/components/LoadingOverlay.vue";
import http, { resolveFileUrl } from "@/utils/request.js";

const pets = ref([]);
const loading = ref(false);
const openPetId = ref(null);
const touchStartX = ref(0);

const speciesEmojiMap = {
  猫: "🐱",
  狗: "🐶",
  仓鼠: "🐹",
  兔子: "🐰",
  鸟: "🐦",
  "爬行类": "🦎",
  其他: "🐾",
};

function goBack() {
  if (getCurrentPages().length > 1) {
    uni.navigateBack({ delta: 1 });
    return;
  }

  uni.switchTab({
    url: "/pages/mine/index",
  });
}

function getAvatarUrl(pet) {
  return resolveFileUrl(pet.avatar);
}

function getPetEmoji(pet) {
  return speciesEmojiMap[pet.species] || "🐾";
}

async function fetchPets() {
  loading.value = true;
  try {
    const response = await http.get("/api/pets");
    pets.value = response?.items || [];
  } finally {
    loading.value = false;
  }
}

function openAddPage() {
  uni.navigateTo({
    url: "/pages/pet/add",
  });
}

function openEditPage(petId) {
  if (openPetId.value === petId) {
    openPetId.value = null;
    return;
  }

  uni.navigateTo({
    url: `/pages/pet/add?petId=${petId}`,
  });
}

function handleTouchStart(event) {
  touchStartX.value = event.changedTouches?.[0]?.clientX || 0;
}

function handleTouchEnd(petId, event) {
  const endX = event.changedTouches?.[0]?.clientX || 0;
  const deltaX = endX - touchStartX.value;

  if (deltaX < -60) {
    openPetId.value = petId;
    return;
  }

  if (deltaX > 40) {
    openPetId.value = null;
  }
}

function closeOpenedCard() {
  openPetId.value = null;
}

async function handleDelete(pet) {
  const modalResult = await new Promise((resolve) => {
    uni.showModal({
      title: "确认删除",
      content: `删除后 ${pet.nickname} 会从列表中隐藏，确定继续吗？`,
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
    await http.del(`/api/pets/${pet.id}`);
    uni.showToast({
      title: "已删除",
      icon: "success",
    });
    openPetId.value = null;
    await fetchPets();
  } finally {
    loading.value = false;
  }
}

onShow(() => {
  fetchPets();
});
</script>

<template>
  <view class="pet-list-page" @click="closeOpenedCard">
    <LoadingOverlay :visible="loading" text="正在整理宠物列表..." />

    <view class="pet-list-page__shell">
      <view class="pet-list-page__header">
        <view class="pet-list-page__back" @click.stop="goBack">‹</view>
        <view class="pet-list-page__header-copy">
          <text class="pet-list-page__title">我的毛孩子</text>
          <text class="section-caption">在这里统一管理宠物档案、编辑资料，左滑卡片可以快速删除。</text>
        </view>
      </view>

      <view class="card pet-list-page__summary">
        <view>
          <text class="section-caption">当前陪伴中的宠物</text>
          <text class="pet-list-page__count">{{ pets.length }} 只</text>
        </view>
        <view class="tag-soft">我的 Tab</view>
      </view>

      <view v-if="pets.length" class="pet-list-page__cards">
        <view
          v-for="pet in pets"
          :key="pet.id"
          class="pet-list-page__swipe"
          @click.stop
        >
          <view class="pet-list-page__delete" @click.stop="handleDelete(pet)">删除</view>
          <view
            class="pet-list-page__card"
            :class="{ 'pet-list-page__card--open': openPetId === pet.id }"
            @click.stop="openEditPage(pet.id)"
            @touchstart="handleTouchStart"
            @touchend="(event) => handleTouchEnd(pet.id, event)"
          >
            <view class="pet-list-page__avatar">
              <image v-if="getAvatarUrl(pet)" :src="getAvatarUrl(pet)" mode="aspectFill" />
              <text v-else>{{ getPetEmoji(pet) }}</text>
            </view>
            <view class="pet-list-page__meta">
              <text class="pet-list-page__name">{{ pet.nickname }}</text>
              <text class="pet-list-page__line">{{ pet.breed }} · {{ pet.species }}</text>
              <text class="pet-list-page__line">
                {{ pet.approximate_age || (pet.birthday ? `生日：${pet.birthday}` : "点击查看完整资料") }}
              </text>
            </view>
            <text class="pet-list-page__chevron">›</text>
          </view>
        </view>
      </view>

      <view v-else class="card">
        <EmptyState icon="🐾" text="你还没有添加宠物，先为第一只毛孩子建立档案吧。" button-text="添加宠物" @action="openAddPage" />
      </view>
    </view>

    <view class="pet-list-page__footer">
      <view class="btn-primary" @click.stop="openAddPage">+ 添加宠物</view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.pet-list-page {
  min-height: 100vh;
  padding-bottom: 160rpx;
  background: linear-gradient(180deg, #fff9fb 0%, #f7fbff 100%);
}

.pet-list-page__shell {
  padding: 32rpx 24rpx 32rpx;
}

.pet-list-page__header {
  display: flex;
  gap: 18rpx;
  align-items: flex-start;
  margin-bottom: 24rpx;
}

.pet-list-page__back {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56rpx;
  height: 56rpx;
  border-radius: 50%;
  color: var(--text-primary);
  font-size: 42rpx;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: var(--shadow-card);
}

.pet-list-page__header-copy {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 10rpx;
}

.pet-list-page__title {
  color: var(--text-primary);
  font-size: 44rpx;
  font-weight: 700;
  line-height: 1.25;
}

.pet-list-page__summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24rpx;
  background: linear-gradient(90deg, rgba(255, 228, 239, 0.96) 0%, rgba(232, 241, 255, 0.95) 100%);
}

.pet-list-page__count {
  display: block;
  margin-top: 8rpx;
  color: var(--text-primary);
  font-size: 48rpx;
  font-weight: 700;
}

.pet-list-page__cards {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.pet-list-page__swipe {
  position: relative;
  overflow: hidden;
  border-radius: 28rpx;
}

.pet-list-page__delete {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 132rpx;
  color: #ffffff;
  font-size: var(--font-body);
  background: linear-gradient(180deg, #ffa798 0%, #eb716d 100%);
}

.pet-list-page__card {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 18rpx;
  padding: 24rpx;
  background: #ffffff;
  border: 2rpx solid rgba(231, 230, 236, 0.9);
  border-radius: 28rpx;
  box-shadow: var(--shadow-card);
  transition: transform 0.2s ease;
}

.pet-list-page__card--open {
  transform: translateX(-132rpx);
}

.pet-list-page__avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 92rpx;
  height: 92rpx;
  overflow: hidden;
  border-radius: 50%;
  color: #c86f92;
  font-size: 42rpx;
  background: linear-gradient(180deg, rgba(255, 198, 211, 0.8) 0%, rgba(212, 240, 247, 0.9) 100%);
}

.pet-list-page__avatar image {
  width: 100%;
  height: 100%;
}

.pet-list-page__meta {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 8rpx;
  min-width: 0;
}

.pet-list-page__name {
  color: var(--text-primary);
  font-size: 30rpx;
  font-weight: 700;
}

.pet-list-page__line {
  color: var(--text-primary);
  font-size: var(--font-caption);
  line-height: 1.4;
}

.pet-list-page__chevron {
  color: #bfbec5;
  font-size: 36rpx;
}

.pet-list-page__footer {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 18rpx 24rpx 34rpx;
  background: rgba(255, 253, 254, 0.96);
  box-shadow: 0 -12rpx 28rpx rgba(255, 195, 211, 0.14);
  backdrop-filter: blur(10px);
}
</style>
