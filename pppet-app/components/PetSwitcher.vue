<script setup>
/** 宠物横向切换栏组件。 */
import { resolveFileUrl } from "@/utils/request.js";

const props = defineProps({
  petList: {
    type: Array,
    default: () => [],
  },
  currentPetId: {
    type: [Number, String, null],
    default: null,
  },
});

const emit = defineEmits(["change"]);

function handleChange(petId) {
  emit("change", petId);
}

function getAvatarUrl(pet) {
  return resolveFileUrl(pet?.avatar);
}
</script>

<template>
  <view class="pet-switcher">
    <scroll-view v-if="props.petList.length" class="pet-switcher__scroll" scroll-x show-scrollbar="false">
      <view class="pet-switcher__list">
        <view
          v-for="pet in props.petList"
          :key="pet.id"
          class="pet-switcher__item"
          :class="{ 'pet-switcher__item--active': pet.id === props.currentPetId }"
          @click="handleChange(pet.id)"
        >
          <image v-if="getAvatarUrl(pet)" class="pet-switcher__avatar" :src="getAvatarUrl(pet)" mode="aspectFill" />
          <view v-else class="pet-switcher__avatar pet-switcher__avatar--fallback">
            <text>{{ pet.emoji || "🐾" }}</text>
          </view>
          <text class="pet-switcher__name">{{ pet.nickname }}</text>
        </view>
      </view>
    </scroll-view>
    <view v-else class="pet-switcher__empty" @click="handleChange(null)">
      <view class="pet-switcher__avatar pet-switcher__avatar--add">
        <text>+</text>
      </view>
      <text class="pet-switcher__name">添加宠物</text>
    </view>
  </view>
</template>

<style scoped lang="scss">
.pet-switcher {
  width: 100%;
}

.pet-switcher__scroll {
  width: 100%;
  white-space: nowrap;
}

.pet-switcher__list {
  display: inline-flex;
  gap: 20rpx;
  padding: 6rpx 0;
}

.pet-switcher__item,
.pet-switcher__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 132rpx;
  gap: 12rpx;
  padding: 18rpx 12rpx;
  background: rgba(255, 255, 255, 0.82);
  border: 2rpx solid transparent;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.pet-switcher__item--active {
  border-color: var(--color-primary);
  background: linear-gradient(180deg, rgba(255, 198, 211, 0.2) 0%, rgba(212, 240, 247, 0.22) 100%);
}

.pet-switcher__avatar {
  width: 84rpx;
  height: 84rpx;
  border-radius: 50%;
  overflow: hidden;
}

.pet-switcher__avatar--fallback,
.pet-switcher__avatar--add {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 38rpx;
  background: linear-gradient(180deg, rgba(255, 198, 211, 0.75) 0%, rgba(212, 240, 247, 0.95) 100%);
}

.pet-switcher__avatar--add {
  color: var(--color-primary);
  font-weight: 700;
}

.pet-switcher__name {
  max-width: 100%;
  color: var(--text-primary);
  font-size: var(--font-caption);
  line-height: 1.3;
  text-align: center;
  white-space: normal;
}
</style>
