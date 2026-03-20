<script setup>
/** 通用空状态展示组件。 */
const props = defineProps({
  icon: {
    type: String,
    default: "🐾",
  },
  text: {
    type: String,
    default: "暂时还没有内容",
  },
  buttonText: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["action"]);

function handleAction() {
  emit("action");
}
</script>

<template>
  <view class="empty-state">
    <view class="empty-state__icon">
      <text>{{ props.icon }}</text>
    </view>
    <text class="empty-state__text">{{ props.text }}</text>
    <view v-if="props.buttonText" class="empty-state__action btn-secondary" @click="handleAction">
      {{ props.buttonText }}
    </view>
  </view>
</template>

<style scoped lang="scss">
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20rpx;
  padding: 56rpx 32rpx;
  text-align: center;
}

.empty-state__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.76);
  color: #bcbcbc;
  font-size: 56rpx;
  box-shadow: var(--shadow-card);
}

.empty-state__text {
  color: var(--text-secondary);
  font-size: var(--font-caption);
  line-height: 1.6;
}

.empty-state__action {
  min-width: 240rpx;
}
</style>
