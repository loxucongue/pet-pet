<script setup>
/** 全局加载遮罩组件。 */
const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  text: {
    type: String,
    default: "加载中...",
  },
});
</script>

<template>
  <view v-if="props.visible" class="loading-overlay">
    <view class="loading-overlay__panel">
      <view class="loading-overlay__spinner" />
      <text class="loading-overlay__text">{{ props.text }}</text>
    </view>
  </view>
</template>

<style scoped lang="scss">
.loading-overlay {
  position: fixed;
  inset: 0;
  z-index: 999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 250, 252, 0.68);
  backdrop-filter: blur(6px);
}

.loading-overlay__panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 18rpx;
  min-width: 220rpx;
  padding: 32rpx 36rpx;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 28rpx;
  box-shadow: 0 18rpx 32rpx rgba(255, 139, 167, 0.16);
}

.loading-overlay__spinner {
  width: 64rpx;
  height: 64rpx;
  border: 6rpx solid rgba(255, 139, 167, 0.16);
  border-top-color: var(--color-primary);
  border-right-color: var(--color-secondary);
  border-radius: 50%;
  animation: loading-rotate 0.9s linear infinite;
}

.loading-overlay__text {
  color: var(--text-secondary);
  font-size: var(--font-caption);
}

@keyframes loading-rotate {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}
</style>
