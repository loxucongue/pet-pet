<script setup>
/** 轻量折线图组件。 */
import { computed } from "vue";

const props = defineProps({
  points: {
    type: Array,
    default: () => [],
  },
  height: {
    type: Number,
    default: 320,
  },
});

const chartPoints = computed(() => {
  if (!props.points.length) {
    return [];
  }

  const values = props.points.map((item) => Number(item.weight) || 0);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  return props.points.map((item, index) => {
    const x = props.points.length === 1 ? 50 : (index / (props.points.length - 1)) * 100;
    const y = 100 - (((Number(item.weight) || 0) - min) / range) * 76 - 12;

    return {
      ...item,
      x,
      y,
      label: String(item.date).slice(5),
    };
  });
});

const lineSegments = computed(() =>
  chartPoints.value.slice(0, -1).map((point, index) => {
    const nextPoint = chartPoints.value[index + 1];
    const dx = nextPoint.x - point.x;
    const dy = nextPoint.y - point.y;
    const length = Math.sqrt(dx * dx + dy * dy);
    const angle = (Math.atan2(dy, dx) * 180) / Math.PI;

    return {
      key: `${point.date}-${nextPoint.date}`,
      left: point.x,
      top: point.y,
      width: length,
      angle,
    };
  }),
);
</script>

<template>
  <view class="simple-line-chart">
    <view v-if="chartPoints.length" class="simple-line-chart__plot" :style="{ height: `${height}rpx` }">
      <view
        v-for="line in lineSegments"
        :key="line.key"
        class="simple-line-chart__line"
        :style="{
          left: `${line.left}%`,
          top: `${line.top}%`,
          width: `${line.width}%`,
          transform: `rotate(${line.angle}deg)`,
        }"
      />

      <view
        v-for="point in chartPoints"
        :key="point.date"
        class="simple-line-chart__point-wrap"
        :style="{ left: `${point.x}%`, top: `${point.y}%` }"
      >
        <view class="simple-line-chart__tooltip">{{ point.weight }}kg</view>
        <view class="simple-line-chart__point" />
      </view>
    </view>

    <view v-if="chartPoints.length" class="simple-line-chart__labels">
      <text
        v-for="point in chartPoints"
        :key="`${point.date}-label`"
        class="simple-line-chart__label"
        :style="{ left: `${point.x}%` }"
      >
        {{ point.label }}
      </text>
    </view>

    <view v-else class="simple-line-chart__empty">暂无体重数据</view>
  </view>
</template>

<style scoped lang="scss">
.simple-line-chart {
  width: 100%;
}

.simple-line-chart__plot {
  position: relative;
  margin: 16rpx 0 38rpx;
  border-bottom: 2rpx solid rgba(255, 139, 167, 0.18);
  border-left: 2rpx solid rgba(168, 216, 234, 0.24);
  background:
    linear-gradient(to top, rgba(255, 139, 167, 0.06) 0, rgba(255, 139, 167, 0.06) 2rpx, transparent 2rpx) 0 100% /
      100% 25% repeat-y;
}

.simple-line-chart__line {
  position: absolute;
  height: 6rpx;
  transform-origin: left center;
  border-radius: 999rpx;
  background: linear-gradient(90deg, var(--color-primary) 0%, var(--color-secondary) 100%);
}

.simple-line-chart__point-wrap {
  position: absolute;
  transform: translate(-50%, -50%);
}

.simple-line-chart__tooltip {
  position: absolute;
  left: 50%;
  bottom: 20rpx;
  transform: translateX(-50%);
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  color: var(--text-primary);
  font-size: var(--font-mini);
  white-space: nowrap;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: var(--shadow-card);
}

.simple-line-chart__point {
  width: 18rpx;
  height: 18rpx;
  border: 4rpx solid #ffffff;
  border-radius: 50%;
  background: var(--color-primary);
  box-shadow: 0 8rpx 18rpx rgba(255, 139, 167, 0.2);
}

.simple-line-chart__labels {
  position: relative;
  height: 34rpx;
}

.simple-line-chart__label {
  position: absolute;
  bottom: 0;
  transform: translateX(-50%);
  color: var(--text-secondary);
  font-size: var(--font-mini);
}

.simple-line-chart__empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 280rpx;
  border-radius: 28rpx;
  color: var(--text-secondary);
  font-size: var(--font-caption);
  background: #fffafc;
}
</style>
