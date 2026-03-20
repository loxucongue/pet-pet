<script setup>
/** 记录模块月历组件。 */
import { computed } from "vue";

const props = defineProps({
  month: {
    type: String,
    required: true,
  },
  selectedDate: {
    type: String,
    default: "",
  },
  markedDates: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(["update:selectedDate", "change-month"]);

const weekLabels = ["一", "二", "三", "四", "五", "六", "日"];

const monthTitle = computed(() => {
  const [year, month] = props.month.split("-").map(Number);
  return `${year}年${month}月`;
});

const markedSet = computed(() => new Set(props.markedDates));

const dayCells = computed(() => {
  const [year, month] = props.month.split("-").map(Number);
  const firstDay = new Date(year, month - 1, 1);
  const startWeekday = (firstDay.getDay() + 6) % 7;
  const daysInCurrentMonth = new Date(year, month, 0).getDate();
  const daysInPreviousMonth = new Date(year, month - 1, 0).getDate();
  const cells = [];

  for (let index = 0; index < 42; index += 1) {
    let cellYear = year;
    let cellMonth = month;
    let day = 0;
    let isCurrentMonth = true;

    if (index < startWeekday) {
      isCurrentMonth = false;
      day = daysInPreviousMonth - startWeekday + index + 1;
      if (month === 1) {
        cellYear -= 1;
        cellMonth = 12;
      } else {
        cellMonth -= 1;
      }
    } else if (index >= startWeekday + daysInCurrentMonth) {
      isCurrentMonth = false;
      day = index - startWeekday - daysInCurrentMonth + 1;
      if (month === 12) {
        cellYear += 1;
        cellMonth = 1;
      } else {
        cellMonth += 1;
      }
    } else {
      day = index - startWeekday + 1;
    }

    const date = `${cellYear}-${String(cellMonth).padStart(2, "0")}-${String(day).padStart(2, "0")}`;

    cells.push({
      date,
      day,
      isCurrentMonth,
      isSelected: date === props.selectedDate,
      isMarked: markedSet.value.has(date),
      isToday: date === formatDate(new Date()),
    });
  }

  return cells;
});

function formatDate(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

function changeMonth(offset) {
  const [year, month] = props.month.split("-").map(Number);
  const nextDate = new Date(year, month - 1 + offset, 1);
  emit(
    "change-month",
    `${nextDate.getFullYear()}-${String(nextDate.getMonth() + 1).padStart(2, "0")}`,
  );
}

function selectDate(cell) {
  emit("update:selectedDate", cell.date);
}
</script>

<template>
  <view class="record-calendar card">
    <view class="record-calendar__header">
      <view class="record-calendar__nav" @click="changeMonth(-1)">‹</view>
      <text class="record-calendar__title">{{ monthTitle }}</text>
      <view class="record-calendar__nav" @click="changeMonth(1)">›</view>
    </view>

    <view class="record-calendar__week">
      <text v-for="item in weekLabels" :key="item" class="record-calendar__week-label">{{ item }}</text>
    </view>

    <view class="record-calendar__grid">
      <view
        v-for="cell in dayCells"
        :key="cell.date"
        class="record-calendar__cell"
        :class="{
          'record-calendar__cell--muted': !cell.isCurrentMonth,
          'record-calendar__cell--selected': cell.isSelected,
        }"
        @click="selectDate(cell)"
      >
        <text
          class="record-calendar__day"
          :class="{ 'record-calendar__day--today': cell.isToday && !cell.isSelected }"
        >
          {{ cell.day }}
        </text>
        <view v-if="cell.isMarked" class="record-calendar__dot" />
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.record-calendar {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.record-calendar__header,
.record-calendar__week,
.record-calendar__grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
}

.record-calendar__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.record-calendar__nav {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56rpx;
  height: 56rpx;
  border-radius: 50%;
  color: var(--color-primary);
  font-size: 34rpx;
  background: #fff7fa;
}

.record-calendar__title {
  color: var(--text-primary);
  font-size: 30rpx;
  font-weight: 700;
}

.record-calendar__week-label {
  text-align: center;
  color: var(--text-secondary);
  font-size: var(--font-mini);
}

.record-calendar__grid {
  gap: 12rpx 0;
}

.record-calendar__cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
  padding: 12rpx 0;
  border-radius: 24rpx;
}

.record-calendar__cell--muted {
  opacity: 0.34;
}

.record-calendar__cell--selected {
  background: linear-gradient(180deg, rgba(255, 139, 167, 0.22) 0%, rgba(168, 216, 234, 0.2) 100%);
}

.record-calendar__day {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56rpx;
  height: 56rpx;
  border-radius: 50%;
  color: var(--text-primary);
  font-size: var(--font-caption);
}

.record-calendar__day--today {
  color: var(--color-primary);
  background: rgba(255, 198, 211, 0.26);
}

.record-calendar__cell--selected .record-calendar__day {
  color: #ffffff;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
}

.record-calendar__dot {
  width: 10rpx;
  height: 10rpx;
  border-radius: 50%;
  background: var(--color-primary);
}

.record-calendar__cell--selected .record-calendar__dot {
  background: #ffffff;
}
</style>
