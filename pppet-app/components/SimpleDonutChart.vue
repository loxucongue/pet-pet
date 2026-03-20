<script setup>
/** 轻量占比环图组件。 */
import { computed } from "vue";

const props = defineProps({
  segments: {
    type: Array,
    default: () => [],
  },
  total: {
    type: Number,
    default: 0,
  },
});

const gradientStyle = computed(() => {
  if (!props.segments.length || !props.total) {
    return "conic-gradient(#f3edf0 0deg 360deg)";
  }

  let start = 0;
  const parts = props.segments.map((item) => {
    const ratio = (Number(item.amount) || 0) / props.total;
    const end = start + ratio * 360;
    const segment = `${item.color} ${start}deg ${end}deg`;
    start = end;
    return segment;
  });

  return `conic-gradient(${parts.join(", ")})`;
});
</script>

<template>
  <view class="simple-donut-chart">
    <view class="simple-donut-chart__ring" :style="{ background: gradientStyle }">
      <view class="simple-donut-chart__center">
        <text class="simple-donut-chart__label">总消费</text>
        <text class="simple-donut-chart__value">¥{{ total.toFixed(2) }}</text>
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.simple-donut-chart {
  display: flex;
  align-items: center;
  justify-content: center;
}

.simple-donut-chart__ring {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 320rpx;
  height: 320rpx;
  border-radius: 50%;
  box-shadow: inset 0 0 0 20rpx rgba(255, 255, 255, 0.18), var(--shadow-card);
}

.simple-donut-chart__center {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 208rpx;
  height: 208rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.94);
}

.simple-donut-chart__label {
  color: var(--text-secondary);
  font-size: var(--font-mini);
}

.simple-donut-chart__value {
  margin-top: 8rpx;
  color: var(--text-primary);
  font-size: 30rpx;
  font-weight: 700;
}
</style>
